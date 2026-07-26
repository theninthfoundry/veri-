"""
VERI Multi-Pass Behavior Compiler — BehaviorOS v4.0

Production-grade optimization compiler replacing string comparison with:
  - Semantic deduplication via Jaccard similarity on tokenized content
  - Critical path analysis (longest weighted path identification)
  - Dependency-aware parallelization with DAG topological ordering
  - Cost-benefit Pareto frontier optimization
  - Dead code elimination via backward reachability from outcome nodes
"""

import math
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind


# ── Data Structures ────────────────────────────────────────────────


class Optimization:
    """Represents a calculated graph optimization opportunity."""

    def __init__(
        self,
        optimization_type: str,
        description: str,
        cost_reduction: float,
        latency_reduction: float,
        confidence: float,
        suggestion: str,
        affected_nodes: List[str],
        priority: float = 0.5,
    ):
        self.optimization_type = optimization_type
        self.description = description
        self.cost_reduction = cost_reduction
        self.latency_reduction = latency_reduction
        self.confidence = confidence
        self.suggestion = suggestion
        self.affected_nodes = affected_nodes
        self.priority = priority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "optimization_type": self.optimization_type,
            "description": self.description,
            "impact": {
                "cost_reduction": round(self.cost_reduction, 4),
                "latency_reduction": round(self.latency_reduction, 2),
            },
            "confidence": round(self.confidence, 2),
            "suggestion": self.suggestion,
            "affected_nodes": self.affected_nodes,
            "priority": round(self.priority, 2),
        }


class ParetoPoint:
    """A point on the cost-quality Pareto frontier."""

    def __init__(
        self, cost: float, quality: float, label: str, node_ids: List[str]
    ):
        self.cost = cost
        self.quality = quality
        self.label = label
        self.node_ids = node_ids

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cost": round(self.cost, 4),
            "quality": round(self.quality, 4),
            "label": self.label,
            "node_ids": self.node_ids,
        }


# ── Utility Functions ─────────────────────────────────────────────


def _tokenize(text: str) -> Set[str]:
    """Tokenizes text into a set of lowercase words for Jaccard comparison."""
    return set(text.lower().split()) if text else set()


def _jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """J(A,B) = |A ∩ B| / |A ∪ B|"""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _build_adjacency(
    node_ids: Set[str], edges: List[RuntimeEdge]
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Returns (children_map, parent_map) for the DAG."""
    children: Dict[str, List[str]] = defaultdict(list)
    parents: Dict[str, List[str]] = defaultdict(list)
    for e in edges:
        if e.source in node_ids and e.target in node_ids:
            children[e.source].append(e.target)
            parents[e.target].append(e.source)
    return children, parents


def _topological_sort(
    node_ids: Set[str], edges: List[RuntimeEdge]
) -> List[str]:
    """Kahn's algorithm for topological ordering."""
    in_degree: Dict[str, int] = {nid: 0 for nid in node_ids}
    children: Dict[str, List[str]] = defaultdict(list)

    for e in edges:
        if e.source in node_ids and e.target in node_ids:
            in_degree[e.target] = in_degree.get(e.target, 0) + 1
            children[e.source].append(e.target)

    queue = [nid for nid in node_ids if in_degree.get(nid, 0) == 0]
    order = []

    while queue:
        current = queue.pop(0)
        order.append(current)
        for child in children.get(current, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    return order


# ── Compiler Passes ────────────────────────────────────────────────


class SemanticDeduplicationPass:
    """
    Detects semantically redundant reasoning steps using Jaccard similarity
    on tokenized content, not just label string equality.

    Threshold: J(A,B) > 0.7 → likely redundant.
    """

    def __init__(self, similarity_threshold: float = 0.7):
        self.threshold = similarity_threshold

    def analyze(
        self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]
    ) -> List[Optimization]:
        opts = []
        reasoning_nodes = [
            n for n in nodes
            if n.kind in (NodeKind.REASONING, NodeKind.REFLECTION, NodeKind.DECISION)
        ]

        for i in range(len(reasoning_nodes)):
            for j in range(i + 1, len(reasoning_nodes)):
                n1 = reasoning_nodes[i]
                n2 = reasoning_nodes[j]

                # Tokenize labels and content
                tokens_1 = _tokenize(n1.label)
                tokens_2 = _tokenize(n2.label)

                # Also include content keys for richer comparison
                if n1.content:
                    tokens_1 |= _tokenize(" ".join(str(v) for v in n1.content.values()))
                if n2.content:
                    tokens_2 |= _tokenize(" ".join(str(v) for v in n2.content.values()))

                similarity = _jaccard_similarity(tokens_1, tokens_2)

                if similarity > self.threshold:
                    cost_saved = (n2.cost or 0.002) + (n1.cost or 0.002) * 0.5
                    latency_saved = n2.latency or 350.0

                    opts.append(Optimization(
                        optimization_type="semantic_deduplication",
                        description=(
                            f"Reasoning steps '{n1.label}' and '{n2.label}' are "
                            f"{similarity*100:.0f}% semantically similar (Jaccard). "
                            f"Shared tokens: {len(tokens_1 & tokens_2)}/{len(tokens_1 | tokens_2)}."
                        ),
                        cost_reduction=cost_saved,
                        latency_reduction=latency_saved,
                        confidence=min(0.95, similarity),
                        suggestion=(
                            f"Cache result of '{n1.label}' and reuse for '{n2.label}'. "
                            f"Eliminates redundant LLM call."
                        ),
                        affected_nodes=[n1.id, n2.id],
                        priority=similarity,
                    ))
        return opts


class CriticalPathPass:
    """
    Identifies the critical path (longest weighted path) through the execution DAG.
    Nodes on the critical path cannot be parallelized without extending total latency.
    Nodes NOT on the critical path have slack and can be deferred or parallelized.
    """

    def analyze(
        self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]
    ) -> List[Optimization]:
        opts = []
        node_map = {n.id: n for n in nodes}
        node_ids = set(node_map.keys())
        children, parents = _build_adjacency(node_ids, edges)
        topo_order = _topological_sort(node_ids, edges)

        # Forward pass: compute earliest start time for each node
        earliest: Dict[str, float] = {}
        for nid in topo_order:
            node = node_map.get(nid)
            parent_list = parents.get(nid, [])
            if not parent_list:
                earliest[nid] = 0.0
            else:
                earliest[nid] = max(
                    earliest.get(p, 0.0) + (node_map[p].latency if p in node_map else 0.0)
                    for p in parent_list
                )

        # Backward pass: compute latest start time for each node
        latest: Dict[str, float] = {}
        total_latency = max(
            earliest.get(nid, 0.0) + (node_map[nid].latency if nid in node_map else 0.0)
            for nid in node_ids
        ) if node_ids else 0.0

        for nid in reversed(topo_order):
            node = node_map.get(nid)
            child_list = children.get(nid, [])
            node_latency = node.latency if node else 0.0
            if not child_list:
                latest[nid] = total_latency - node_latency
            else:
                latest[nid] = min(
                    latest.get(c, total_latency) for c in child_list
                ) - node_latency

        # Compute slack for each node
        slack: Dict[str, float] = {}
        critical_path_nodes: Set[str] = set()

        for nid in topo_order:
            s = latest.get(nid, 0.0) - earliest.get(nid, 0.0)
            slack[nid] = max(0.0, s)
            if abs(s) < 0.01:  # Zero slack = critical path
                critical_path_nodes.add(nid)

        # Report non-critical nodes with high slack as parallelization candidates
        high_slack_nodes = [
            (nid, slack[nid])
            for nid in topo_order
            if nid not in critical_path_nodes and slack.get(nid, 0.0) > 100.0
        ]

        if high_slack_nodes:
            slack_labels = [
                f"'{node_map[nid].label}' (slack: {s:.0f}ms)"
                for nid, s in high_slack_nodes[:5]
            ]
            total_slack_time = sum(s for _, s in high_slack_nodes)

            opts.append(Optimization(
                optimization_type="critical_path_slack",
                description=(
                    f"Critical path analysis found {len(high_slack_nodes)} nodes with scheduling slack. "
                    f"Total recoverable parallelism: {total_slack_time:.0f}ms."
                ),
                cost_reduction=0.0,
                latency_reduction=min(total_slack_time, total_latency * 0.3),
                confidence=0.85,
                suggestion=(
                    f"Nodes with slack can be rescheduled or parallelized: "
                    f"{'; '.join(slack_labels[:3])}."
                ),
                affected_nodes=[nid for nid, _ in high_slack_nodes[:5]],
                priority=0.8,
            ))

        return opts


class DependencyAwareParallelizationPass:
    """
    Identifies adjacent independent operations that can be parallelized
    by analyzing actual data dependencies in the DAG, not just sequential order.
    """

    def analyze(
        self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]
    ) -> List[Optimization]:
        opts = []
        node_map = {n.id: n for n in nodes}
        node_ids = set(node_map.keys())

        # Build dependency sets for each node (transitive closure)
        _, parents = _build_adjacency(node_ids, edges)

        def get_ancestors(nid: str, memo: Dict[str, Set[str]] = {}) -> Set[str]:
            if nid in memo:
                return memo[nid]
            ancestors: Set[str] = set()
            for p in parents.get(nid, []):
                ancestors.add(p)
                ancestors |= get_ancestors(p, memo)
            memo[nid] = ancestors
            return ancestors

        # Find tool/action nodes
        action_nodes = [
            n for n in nodes
            if n.kind in (NodeKind.TOOL_INVOCATION, NodeKind.ACTION, NodeKind.LLM_CALL)
        ]

        # Find independent pairs
        independent_groups: List[List[RuntimeNode]] = []

        for i in range(len(action_nodes)):
            group = [action_nodes[i]]
            ancestors_i = get_ancestors(action_nodes[i].id)

            for j in range(i + 1, min(i + 5, len(action_nodes))):
                ancestors_j = get_ancestors(action_nodes[j].id)

                # Independent if neither is ancestor of the other
                if (action_nodes[j].id not in ancestors_i and
                        action_nodes[i].id not in ancestors_j):
                    group.append(action_nodes[j])

            if len(group) >= 2:
                independent_groups.append(group)

        # Deduplicate and report
        reported_pairs: Set[Tuple[str, str]] = set()
        for group in independent_groups:
            for k in range(len(group)):
                for l in range(k + 1, len(group)):
                    pair_key = tuple(sorted([group[k].id, group[l].id]))
                    if pair_key in reported_pairs:
                        continue
                    reported_pairs.add(pair_key)

                    t1, t2 = group[k], group[l]
                    savings_ms = min(t1.latency or 200.0, t2.latency or 200.0)

                    opts.append(Optimization(
                        optimization_type="parallelizable_operations",
                        description=(
                            f"'{t1.label}' and '{t2.label}' have no data dependency "
                            f"(verified via transitive closure analysis)."
                        ),
                        cost_reduction=0.0,
                        latency_reduction=savings_ms,
                        confidence=0.88,
                        suggestion=(
                            f"Execute '{t1.label}' and '{t2.label}' concurrently "
                            f"via asyncio.gather(). Saves ~{savings_ms:.0f}ms."
                        ),
                        affected_nodes=[t1.id, t2.id],
                        priority=0.7,
                    ))
        return opts


class DeadCodeEliminationPass:
    """
    Prunes unreachable branches via backward reachability from outcome nodes.
    Any node not on a path to an outcome or decision node is dead code.
    """

    def analyze(
        self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]
    ) -> List[Optimization]:
        opts = []
        node_map = {n.id: n for n in nodes}
        node_ids = set(node_map.keys())
        children, parents = _build_adjacency(node_ids, edges)

        # Identify outcome nodes (terminal nodes, decisions, or error nodes)
        terminal_kinds = {NodeKind.OUTCOME, NodeKind.DECISION, NodeKind.ERROR, NodeKind.ACTION}
        outgoing_nodes = {e.source for e in edges if e.source in node_ids and e.target in node_ids}
        outcome_nodes = {
            nid for nid in node_ids
            if nid not in outgoing_nodes or (nid in node_map and node_map[nid].kind in terminal_kinds)
        }

        # Backward BFS from outcome nodes
        reachable: Set[str] = set()
        queue = list(outcome_nodes)
        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue
            reachable.add(current)
            for p in parents.get(current, []):
                if p not in reachable:
                    queue.append(p)

        # Dead nodes = not reachable from any outcome
        dead_nodes = node_ids - reachable
        if dead_nodes:
            dead_cost = sum(
                node_map[nid].cost for nid in dead_nodes
                if nid in node_map and node_map[nid].cost
            )
            dead_latency = sum(
                node_map[nid].latency for nid in dead_nodes
                if nid in node_map and node_map[nid].latency
            )

            labels = [
                node_map[nid].label for nid in list(dead_nodes)[:5]
                if nid in node_map
            ]

            opts.append(Optimization(
                optimization_type="dead_code_elimination",
                description=(
                    f"{len(dead_nodes)} nodes are unreachable from any outcome/decision node. "
                    f"These represent abandoned reasoning paths or wasted computation."
                ),
                cost_reduction=dead_cost,
                latency_reduction=dead_latency,
                confidence=0.92,
                suggestion=(
                    f"Eliminate dead execution branches: {', '.join(labels)}. "
                    f"Add pre-execution contract to prevent speculative branching."
                ),
                affected_nodes=list(dead_nodes)[:10],
                priority=0.9,
            ))

        return opts


class CostQualityParetoPass:
    """
    Computes the Pareto frontier of cost vs. quality tradeoffs.
    Identifies nodes where reducing cost has minimal quality impact
    and vice versa.
    """

    def analyze(
        self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]
    ) -> List[Optimization]:
        opts = []

        # Build (cost, quality) points for each node
        points = []
        for n in nodes:
            cost = n.cost or 0.0
            # Quality proxy: confidence * (1 + evidence count * 0.1)
            conf = n.confidence if n.confidence is not None else 0.5
            quality = conf
            if cost > 0.001:  # Only consider cost-bearing nodes
                points.append(ParetoPoint(
                    cost=cost, quality=quality, label=n.label, node_ids=[n.id]
                ))

        if len(points) < 3:
            return opts

        # Sort by cost
        points.sort(key=lambda p: p.cost)

        # Find Pareto frontier (non-dominated points)
        frontier: List[ParetoPoint] = []
        max_quality = -1.0
        for p in sorted(points, key=lambda p: p.cost):
            if p.quality > max_quality:
                frontier.append(p)
                max_quality = p.quality

        # Find dominated points with high cost and low quality
        dominated_high_cost = [
            p for p in points
            if p not in frontier and p.cost > 0.005 and p.quality < 0.6
        ]

        if dominated_high_cost:
            total_wasted = sum(p.cost for p in dominated_high_cost)
            labels = [p.label for p in dominated_high_cost[:3]]

            opts.append(Optimization(
                optimization_type="pareto_dominated",
                description=(
                    f"{len(dominated_high_cost)} nodes are Pareto-dominated: "
                    f"high cost with low quality output. "
                    f"Total wasted spend: ${total_wasted:.4f}."
                ),
                cost_reduction=total_wasted * 0.6,
                latency_reduction=0.0,
                confidence=0.78,
                suggestion=(
                    f"Replace high-cost/low-quality nodes with cheaper alternatives: "
                    f"{', '.join(labels)}. Consider model downgrade or prompt optimization."
                ),
                affected_nodes=[
                    nid for p in dominated_high_cost for nid in p.node_ids
                ][:8],
                priority=0.75,
            ))

        return opts


class UnnecessaryRetrievalPass:
    """Identifies knowledge retrieval nodes whose data was never consumed downstream."""

    def analyze(
        self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]
    ) -> List[Optimization]:
        opts = []
        node_ids = {n.id for n in nodes}
        knowledge_nodes = [
            n for n in nodes
            if n.kind in (NodeKind.KNOWLEDGE, NodeKind.OBSERVATION)
        ]

        # Check if knowledge node has any outgoing edges
        outgoing = {e.source for e in edges if e.source in node_ids}

        for k in knowledge_nodes:
            if k.id not in outgoing:
                opts.append(Optimization(
                    optimization_type="unnecessary_retrieval",
                    description=(
                        f"Knowledge retrieval '{k.label}' was fetched but has no "
                        f"downstream consumers in the execution graph."
                    ),
                    cost_reduction=k.cost or 0.001,
                    latency_reduction=k.latency or 150.0,
                    confidence=0.85,
                    suggestion=(
                        f"Defer retrieval '{k.label}' until explicitly requested "
                        f"by an active sub-goal. Use lazy-loading pattern."
                    ),
                    affected_nodes=[k.id],
                    priority=0.6,
                ))
        return opts


# ── Public API ─────────────────────────────────────────────────────


def run_optimization_passes(
    nodes: List[RuntimeNode], edges: List[RuntimeEdge]
) -> List[Optimization]:
    """
    Runs all 6 compiler passes over an execution graph.
    Returns optimizations sorted by priority (highest first).
    """
    all_opts: List[Optimization] = []

    passes = [
        SemanticDeduplicationPass(),
        CriticalPathPass(),
        DependencyAwareParallelizationPass(),
        DeadCodeEliminationPass(),
        CostQualityParetoPass(),
        UnnecessaryRetrievalPass(),
    ]

    for p in passes:
        all_opts.extend(p.analyze(nodes, edges))

    # Sort by priority descending, then by cost reduction
    all_opts.sort(
        key=lambda o: (o.priority, o.cost_reduction + o.latency_reduction / 1000.0),
        reverse=True,
    )
    return all_opts
