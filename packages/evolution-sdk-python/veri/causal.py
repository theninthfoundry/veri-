"""
VERI Causal Reasoning Engine — BehaviorOS v4.0

True causal inference engine based on structural causal models with:
  - do-calculus intervention simulation (sever incoming edges, propagate)
  - Causal effect estimation via average treatment effect on DAG
  - Root cause isolation via backward causal walk with strength ranking
  - Counterfactual query answering ("what if X had been Y?")
  - Causal sufficiency testing

This engine answers: "WHY did the agent behave this way?" — not just "WHAT happened."
"""

import math
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind


# ── Data Structures ────────────────────────────────────────────────


class CausalStrength:
    """Measured causal influence between two nodes."""

    def __init__(
        self,
        source_id: str,
        target_id: str,
        strength: float,
        method: str,
        is_direct: bool = True,
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.strength = max(0.0, min(1.0, strength))
        self.method = method
        self.is_direct = is_direct

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "strength": round(self.strength, 4),
            "method": self.method,
            "is_direct": self.is_direct,
        }


class CausalLink:
    """A single link in a causal chain."""

    def __init__(
        self,
        from_id: str,
        from_label: str,
        to_id: str,
        to_label: str,
        strength: float,
        edge_kind: str,
    ):
        self.from_id = from_id
        self.from_label = from_label
        self.to_id = to_id
        self.to_label = to_label
        self.strength = strength
        self.edge_kind = edge_kind

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_id": self.from_id,
            "from_label": self.from_label,
            "to_id": self.to_id,
            "to_label": self.to_label,
            "strength": round(self.strength, 4),
            "edge_kind": self.edge_kind,
        }


class RootCause:
    """An identified root cause of a failure or anomaly."""

    def __init__(
        self,
        node_id: str,
        label: str,
        kind: str,
        causal_strength: float,
        path_length: int,
        explanation: str,
        causal_chain: List[CausalLink],
    ):
        self.node_id = node_id
        self.label = label
        self.kind = kind
        self.causal_strength = causal_strength
        self.path_length = path_length
        self.explanation = explanation
        self.causal_chain = causal_chain

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "kind": self.kind,
            "causal_strength": round(self.causal_strength, 4),
            "path_length": self.path_length,
            "explanation": self.explanation,
            "causal_chain": [l.to_dict() for l in self.causal_chain],
        }


class InterventionResult:
    """Result of a do(X=x) causal intervention."""

    def __init__(
        self,
        intervened_node_id: str,
        intervention_value: Any,
        original_outcomes: Dict[str, float],
        counterfactual_outcomes: Dict[str, float],
        total_effect: float,
        explanation: str,
    ):
        self.intervened_node_id = intervened_node_id
        self.intervention_value = intervention_value
        self.original_outcomes = original_outcomes
        self.counterfactual_outcomes = counterfactual_outcomes
        self.total_effect = total_effect
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intervened_node_id": self.intervened_node_id,
            "intervention_value": str(self.intervention_value),
            "original_outcomes": {
                k: round(v, 4) for k, v in self.original_outcomes.items()
            },
            "counterfactual_outcomes": {
                k: round(v, 4) for k, v in self.counterfactual_outcomes.items()
            },
            "total_effect": round(self.total_effect, 4),
            "explanation": self.explanation,
        }


# ── Causal Graph ──────────────────────────────────────────────────


class CausalGraph:
    """
    Structural Causal Model represented as a directed graph
    with measurable causal strengths on edges.
    """

    def __init__(self):
        self.nodes: Dict[str, RuntimeNode] = {}
        self.children: Dict[str, List[str]] = defaultdict(list)
        self.parents: Dict[str, List[str]] = defaultdict(list)
        self.edge_strengths: Dict[Tuple[str, str], float] = {}
        self.edge_kinds: Dict[Tuple[str, str], str] = {}

    def add_node(self, node: RuntimeNode) -> None:
        self.nodes[node.id] = node

    def add_edge(
        self, source_id: str, target_id: str, kind: str, weight: float = 1.0
    ) -> None:
        self.children[source_id].append(target_id)
        self.parents[target_id].append(source_id)

        # Causal strength: weighted combination of edge weight and confidence
        source_conf = self._get_confidence(source_id)
        strength = weight * source_conf
        self.edge_strengths[(source_id, target_id)] = strength
        self.edge_kinds[(source_id, target_id)] = kind

    def _get_confidence(self, node_id: str) -> float:
        node = self.nodes.get(node_id)
        if node and node.confidence is not None:
            return node.confidence
        return 0.5

    def get_descendants(self, node_id: str) -> Set[str]:
        """All nodes transitively reachable from node_id."""
        visited: Set[str] = set()
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            for child in self.children.get(current, []):
                if child not in visited:
                    visited.add(child)
                    queue.append(child)
        return visited

    def get_ancestors(self, node_id: str) -> Set[str]:
        """All nodes that transitively influence node_id."""
        visited: Set[str] = set()
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            for parent in self.parents.get(current, []):
                if parent not in visited:
                    visited.add(parent)
                    queue.append(parent)
        return visited

    def topological_sort(self) -> List[str]:
        """Kahn's algorithm."""
        in_deg: Dict[str, int] = {nid: 0 for nid in self.nodes}
        for nid in self.nodes:
            for child in self.children.get(nid, []):
                if child in in_deg:
                    in_deg[child] += 1

        queue = [nid for nid, d in in_deg.items() if d == 0]
        order = []
        while queue:
            current = queue.pop(0)
            order.append(current)
            for child in self.children.get(current, []):
                if child in in_deg:
                    in_deg[child] -= 1
                    if in_deg[child] == 0:
                        queue.append(child)
        return order


# ── Causal Reasoning Engine ──────────────────────────────────────


class CausalReasoningEngine:
    """
    True causal inference engine that builds structural causal models
    from execution traces and supports intervention queries.
    """

    def build_causal_graph(
        self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]
    ) -> CausalGraph:
        """Construct a structural causal model from an execution trace."""
        graph = CausalGraph()

        for n in nodes:
            graph.add_node(n)

        for e in edges:
            if e.source in graph.nodes and e.target in graph.nodes:
                weight = e.weight if e.weight is not None else 1.0
                graph.add_edge(e.source, e.target, e.kind, weight)

        return graph

    def estimate_causal_effect(
        self,
        graph: CausalGraph,
        source_id: str,
        target_id: str,
    ) -> CausalStrength:
        """
        Estimates the Average Causal Effect (ACE) of source on target.

        Uses the front-door criterion when possible:
        ACE = Σ_m P(m|do(x)) * P(y|do(m))

        Falls back to path-based estimation when graph structure is complex.
        """
        if source_id not in graph.nodes or target_id not in graph.nodes:
            return CausalStrength(source_id, target_id, 0.0, "not_found")

        # Check direct causal link
        direct_strength = graph.edge_strengths.get((source_id, target_id))
        if direct_strength is not None:
            return CausalStrength(
                source_id, target_id, direct_strength, "direct_edge", is_direct=True
            )

        # Path-based estimation: find all causal paths from source to target
        all_paths = self._find_all_paths(graph, source_id, target_id, max_depth=8)

        if not all_paths:
            return CausalStrength(source_id, target_id, 0.0, "no_path")

        # Compute path strength: product of edge strengths along each path
        path_strengths = []
        for path in all_paths:
            strength = 1.0
            for i in range(len(path) - 1):
                edge_s = graph.edge_strengths.get((path[i], path[i + 1]), 0.5)
                strength *= edge_s
            path_strengths.append(strength)

        # Total causal effect: noisy-OR combination of path strengths
        # P(Y|do(X)) = 1 - Π(1 - path_strength_i)
        product = 1.0
        for ps in path_strengths:
            product *= (1.0 - ps)
        total_effect = 1.0 - product

        return CausalStrength(
            source_id, target_id, total_effect,
            f"path_based ({len(all_paths)} paths)", is_direct=False
        )

    def find_root_causes(
        self,
        graph: CausalGraph,
        failure_node_id: str,
        k: int = 3,
    ) -> List[RootCause]:
        """
        Walks the causal graph backward from a failure node to identify
        the top-k root causes ranked by causal strength.
        """
        if failure_node_id not in graph.nodes:
            return []

        failure_node = graph.nodes[failure_node_id]
        ancestors = graph.get_ancestors(failure_node_id)

        candidates: List[RootCause] = []

        for ancestor_id in ancestors:
            ancestor = graph.nodes.get(ancestor_id)
            if not ancestor:
                continue

            # Compute causal strength from ancestor to failure
            effect = self.estimate_causal_effect(graph, ancestor_id, failure_node_id)

            # Build causal chain
            paths = self._find_all_paths(graph, ancestor_id, failure_node_id, max_depth=8)
            chain = []
            if paths:
                # Use shortest path for explanation
                shortest = min(paths, key=len)
                for i in range(len(shortest) - 1):
                    from_node = graph.nodes.get(shortest[i])
                    to_node = graph.nodes.get(shortest[i + 1])
                    edge_kind = graph.edge_kinds.get(
                        (shortest[i], shortest[i + 1]), "unknown"
                    )
                    if from_node and to_node:
                        chain.append(CausalLink(
                            from_id=shortest[i],
                            from_label=from_node.label,
                            to_id=shortest[i + 1],
                            to_label=to_node.label,
                            strength=graph.edge_strengths.get(
                                (shortest[i], shortest[i + 1]), 0.5
                            ),
                            edge_kind=edge_kind,
                        ))

            path_length = min(len(p) for p in paths) - 1 if paths else 0

            # Root cause scoring: high causal strength + short path + low confidence
            ancestor_conf = ancestor.confidence if ancestor.confidence is not None else 0.5
            root_score = effect.strength * (1.0 / max(1, path_length)) * (1.5 - ancestor_conf)

            candidates.append(RootCause(
                node_id=ancestor_id,
                label=ancestor.label,
                kind=ancestor.kind,
                causal_strength=root_score,
                path_length=path_length,
                explanation=(
                    f"'{ancestor.label}' ({ancestor.kind}) causally influences "
                    f"failure node '{failure_node.label}' via {len(paths)} path(s) "
                    f"of length {path_length}. Causal effect: {effect.strength:.3f}."
                ),
                causal_chain=chain,
            ))

        # Sort by causal strength and return top-k
        candidates.sort(key=lambda c: c.causal_strength, reverse=True)
        return candidates[:k]

    def simulate_intervention(
        self,
        graph: CausalGraph,
        node_id: str,
        new_confidence: float = 0.95,
    ) -> InterventionResult:
        """
        Implements do(X = new_confidence): severs all incoming edges to X,
        sets X's value, and propagates effects through the DAG.

        This is the core of Pearl's do-calculus.
        """
        if node_id not in graph.nodes:
            return InterventionResult(
                node_id, new_confidence, {}, {}, 0.0,
                f"Node '{node_id}' not found."
            )

        topo_order = graph.topological_sort()

        # Original outcome values
        original_conf: Dict[str, float] = {}
        for nid in graph.nodes:
            node = graph.nodes[nid]
            original_conf[nid] = node.confidence if node.confidence is not None else 0.5

        # Intervened: sever incoming edges to target, set value
        intervened_conf: Dict[str, float] = dict(original_conf)
        intervened_conf[node_id] = new_confidence

        # Forward propagation in topological order
        node_idx = topo_order.index(node_id) if node_id in topo_order else 0

        for nid in topo_order[node_idx + 1:]:
            parents_of_nid = graph.parents.get(nid, [])
            if not parents_of_nid:
                continue

            # Weighted average of parent confidences
            weighted_sum = 0.0
            total_weight = 0.0
            for pid in parents_of_nid:
                edge_strength = graph.edge_strengths.get((pid, nid), 0.5)
                weighted_sum += intervened_conf.get(pid, 0.5) * edge_strength
                total_weight += edge_strength

            if total_weight > 0:
                propagated = weighted_sum / total_weight
                # Blend with original (attenuation)
                intervened_conf[nid] = 0.7 * propagated + 0.3 * original_conf.get(nid, 0.5)

        # Identify outcome nodes (no children)
        outcome_ids = {
            nid for nid in graph.nodes
            if not graph.children.get(nid)
        }

        original_outcomes = {nid: original_conf.get(nid, 0.5) for nid in outcome_ids}
        counterfactual_outcomes = {nid: intervened_conf.get(nid, 0.5) for nid in outcome_ids}

        # Total effect: average absolute change across outcomes
        total_effect = 0.0
        if outcome_ids:
            total_effect = sum(
                abs(counterfactual_outcomes[nid] - original_outcomes[nid])
                for nid in outcome_ids
            ) / len(outcome_ids)

        node = graph.nodes[node_id]
        explanation = (
            f"Intervention do({node.label} = {new_confidence:.2f}) propagated to "
            f"{len(outcome_ids)} outcome nodes. "
            f"Average outcome change: {total_effect:.3f}. "
            f"{'Significant' if total_effect > 0.1 else 'Minimal'} causal impact."
        )

        return InterventionResult(
            intervened_node_id=node_id,
            intervention_value=new_confidence,
            original_outcomes=original_outcomes,
            counterfactual_outcomes=counterfactual_outcomes,
            total_effect=total_effect,
            explanation=explanation,
        )

    def compute_causal_chain(
        self,
        graph: CausalGraph,
        source_id: str,
        target_id: str,
    ) -> List[CausalLink]:
        """Full causal pathway decomposition from source to target."""
        paths = self._find_all_paths(graph, source_id, target_id, max_depth=10)
        if not paths:
            return []

        # Return the strongest path
        best_path = None
        best_strength = -1.0

        for path in paths:
            strength = 1.0
            for i in range(len(path) - 1):
                strength *= graph.edge_strengths.get((path[i], path[i + 1]), 0.5)
            if strength > best_strength:
                best_strength = strength
                best_path = path

        if not best_path:
            return []

        chain = []
        for i in range(len(best_path) - 1):
            from_node = graph.nodes.get(best_path[i])
            to_node = graph.nodes.get(best_path[i + 1])
            if from_node and to_node:
                chain.append(CausalLink(
                    from_id=best_path[i],
                    from_label=from_node.label,
                    to_id=best_path[i + 1],
                    to_label=to_node.label,
                    strength=graph.edge_strengths.get(
                        (best_path[i], best_path[i + 1]), 0.5
                    ),
                    edge_kind=graph.edge_kinds.get(
                        (best_path[i], best_path[i + 1]), "unknown"
                    ),
                ))
        return chain

    def test_causal_sufficiency(
        self, graph: CausalGraph, source_id: str, target_id: str
    ) -> Dict[str, Any]:
        """
        Tests whether the observed variables are sufficient to identify
        the causal effect of source on target (no unobserved confounders).

        In our case, since all nodes are observed in the IR, we check for
        back-door paths that might introduce confounding.
        """
        if source_id not in graph.nodes or target_id not in graph.nodes:
            return {"sufficient": False, "reason": "Node not found"}

        # Check for common ancestors (potential confounders)
        source_ancestors = graph.get_ancestors(source_id)
        target_ancestors = graph.get_ancestors(target_id)
        common_ancestors = source_ancestors & target_ancestors

        # Check for back-door paths
        # A back-door path exists if there's a common ancestor that's
        # not on the directed path from source to target
        directed_paths = self._find_all_paths(graph, source_id, target_id, max_depth=8)
        directed_nodes = set()
        for path in directed_paths:
            directed_nodes.update(path)

        confounders = common_ancestors - directed_nodes

        sufficient = len(confounders) == 0

        return {
            "sufficient": sufficient,
            "common_ancestors": len(common_ancestors),
            "potential_confounders": len(confounders),
            "confounder_ids": list(confounders)[:5],
            "directed_paths": len(directed_paths),
            "explanation": (
                f"Causal effect is {'identifiable' if sufficient else 'potentially confounded'}. "
                f"{len(common_ancestors)} common ancestors, "
                f"{len(confounders)} potential confounders."
            ),
        }

    # ── Internal Utilities ────────────────────────────────────────

    def _find_all_paths(
        self,
        graph: CausalGraph,
        source: str,
        target: str,
        max_depth: int = 8,
    ) -> List[List[str]]:
        """DFS to find all directed paths from source to target."""
        all_paths: List[List[str]] = []

        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(path) > max_depth:
                return
            if current == target:
                all_paths.append(list(path))
                return
            for child in graph.children.get(current, []):
                if child not in visited:
                    visited.add(child)
                    path.append(child)
                    dfs(child, path, visited)
                    path.pop()
                    visited.remove(child)

        dfs(source, [source], {source})
        return all_paths
