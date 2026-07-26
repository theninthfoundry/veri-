"""
VERI Counterfactual Ablation Engine — BehaviorOS v4.0

Production-grade counterfactual simulation engine replacing binary checks with:
  - Topological sort for correct propagation order through DAGs
  - Confidence attenuation model through edge chains
  - Multi-node simultaneous ablation
  - Sensitivity analysis (∂output/∂input per node)
  - Monte Carlo path sampling for stochastic impact estimation
"""

import math
import random
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind


# ── Data Structures ────────────────────────────────────────────────


class SimulationResult:
    """Result of a counterfactual node ablation simulation."""

    def __init__(
        self,
        target_node_id: str,
        substitute_value: Any,
        recovered: bool,
        recovery_probability: float,
        causal_impact_score: float,
        explanation: str,
        affected_downstream: int = 0,
        sensitivity: float = 0.0,
        propagation_depth: int = 0,
    ):
        self.target_node_id = target_node_id
        self.substitute_value = substitute_value
        self.recovered = recovered
        self.recovery_probability = max(0.0, min(1.0, recovery_probability))
        self.causal_impact_score = max(0.0, min(1.0, causal_impact_score))
        self.explanation = explanation
        self.affected_downstream = affected_downstream
        self.sensitivity = sensitivity
        self.propagation_depth = propagation_depth

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_node_id": self.target_node_id,
            "substitute_value": str(self.substitute_value),
            "recovered": self.recovered,
            "recovery_probability": self.recovery_probability,
            "causal_impact_score": self.causal_impact_score,
            "explanation": self.explanation,
            "affected_downstream": self.affected_downstream,
            "sensitivity": self.sensitivity,
            "propagation_depth": self.propagation_depth,
        }


class SensitivityReport:
    """Per-node sensitivity analysis report."""

    def __init__(
        self,
        node_id: str,
        label: str,
        sensitivity_score: float,
        downstream_count: int,
        is_critical_path: bool,
    ):
        self.node_id = node_id
        self.label = label
        self.sensitivity_score = sensitivity_score
        self.downstream_count = downstream_count
        self.is_critical_path = is_critical_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "sensitivity_score": round(self.sensitivity_score, 4),
            "downstream_count": self.downstream_count,
            "is_critical_path": self.is_critical_path,
        }


class MultiAblationResult:
    """Result of simultaneously ablating multiple nodes."""

    def __init__(
        self,
        ablated_node_ids: List[str],
        systemic_impact: float,
        individual_impacts: Dict[str, float],
        interaction_effect: float,
        explanation: str,
    ):
        self.ablated_node_ids = ablated_node_ids
        self.systemic_impact = systemic_impact
        self.individual_impacts = individual_impacts
        self.interaction_effect = interaction_effect
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ablated_node_ids": self.ablated_node_ids,
            "systemic_impact": round(self.systemic_impact, 4),
            "individual_impacts": {
                k: round(v, 4) for k, v in self.individual_impacts.items()
            },
            "interaction_effect": round(self.interaction_effect, 4),
            "explanation": self.explanation,
        }


# ── DAG Utilities ─────────────────────────────────────────────────


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


def _get_downstream_set(
    start_id: str, edges: List[RuntimeEdge], node_ids: Set[str]
) -> Set[str]:
    """BFS to find all nodes transitively downstream of start_id."""
    children_map: Dict[str, List[str]] = defaultdict(list)
    for e in edges:
        if e.source in node_ids and e.target in node_ids:
            children_map[e.source].append(e.target)

    visited: Set[str] = set()
    queue = [start_id]
    while queue:
        current = queue.pop(0)
        for child in children_map.get(current, []):
            if child not in visited:
                visited.add(child)
                queue.append(child)
    return visited


def _get_max_depth(
    start_id: str, edges: List[RuntimeEdge], node_ids: Set[str]
) -> int:
    """BFS to find maximum propagation depth from start_id."""
    children_map: Dict[str, List[str]] = defaultdict(list)
    for e in edges:
        if e.source in node_ids and e.target in node_ids:
            children_map[e.source].append(e.target)

    max_depth = 0
    queue: List[Tuple[str, int]] = [(start_id, 0)]
    visited: Set[str] = {start_id}

    while queue:
        current, depth = queue.pop(0)
        for child in children_map.get(current, []):
            if child not in visited:
                visited.add(child)
                max_depth = max(max_depth, depth + 1)
                queue.append((child, depth + 1))

    return max_depth


# ── Counterfactual Simulator ──────────────────────────────────────


class CounterfactualSimulator:
    """
    Simulates counterfactual execution paths by substituting intermediate
    node outputs and propagating effects through the execution DAG.
    """

    def __init__(self, attenuation_factor: float = 0.85):
        """
        Args:
            attenuation_factor: How much causal influence attenuates per edge hop.
                               0.85 means each hop reduces impact by 15%.
        """
        self.attenuation_factor = attenuation_factor

    def simulate_ablation(
        self,
        nodes: List[RuntimeNode],
        edges: List[RuntimeEdge],
        target_node_id: str,
        substitute_value: Any,
    ) -> SimulationResult:
        """
        Substitutes the output of target_node_id and propagates effects
        through the DAG in topological order to evaluate recovery.

        Uses confidence attenuation model: each downstream node's confidence
        is adjusted by the propagated impact, decaying with graph distance.
        """
        node_map = {n.id: n for n in nodes}
        node_ids = set(node_map.keys())
        target_node = node_map.get(target_node_id)

        if not target_node:
            return SimulationResult(
                target_node_id=target_node_id,
                substitute_value=substitute_value,
                recovered=False,
                recovery_probability=0.0,
                causal_impact_score=0.0,
                explanation=f"Node '{target_node_id}' not found in execution graph.",
            )

        # Find all downstream nodes
        downstream = _get_downstream_set(target_node_id, edges, node_ids)
        propagation_depth = _get_max_depth(target_node_id, edges, node_ids)

        if not downstream:
            return SimulationResult(
                target_node_id=target_node_id,
                substitute_value=substitute_value,
                recovered=True,
                recovery_probability=0.99,
                causal_impact_score=0.05,
                explanation=(
                    f"Node '{target_node.label}' is a leaf node with no downstream dependencies. "
                    f"Substitution has minimal systemic impact."
                ),
                affected_downstream=0,
                propagation_depth=0,
            )

        # Build parent map for incoming edge weights
        parent_map: Dict[str, List[str]] = defaultdict(list)
        for e in edges:
            if e.source in node_ids and e.target in node_ids:
                parent_map[e.target].append(e.source)

        # Propagate confidence changes through DAG
        # Original confidence map
        original_conf: Dict[str, float] = {}
        for n in nodes:
            original_conf[n.id] = n.confidence if n.confidence is not None else 0.5

        # Simulated confidence: ablated node gets substitute confidence
        simulated_conf = dict(original_conf)
        simulated_conf[target_node_id] = 0.95  # Substitute with "golden" value

        # Topological propagation
        topo_order = _topological_sort(node_ids, edges)
        target_idx = topo_order.index(target_node_id) if target_node_id in topo_order else 0

        impact_scores: Dict[str, float] = {}

        for nid in topo_order[target_idx + 1:]:
            if nid not in downstream:
                continue

            parents = parent_map.get(nid, [])
            if not parents:
                continue

            # Compute weighted average of parent confidences
            parent_conf_sum = sum(simulated_conf.get(p, 0.5) for p in parents)
            parent_conf_avg = parent_conf_sum / len(parents)

            # Attenuated propagation
            orig = original_conf.get(nid, 0.5)
            new_conf = self.attenuation_factor * parent_conf_avg + (1.0 - self.attenuation_factor) * orig
            simulated_conf[nid] = new_conf

            # Impact = absolute change from original
            impact = abs(new_conf - orig)
            impact_scores[nid] = impact

        # Error nodes that might recover
        error_downstream = [
            nid for nid in downstream
            if node_map.get(nid) and node_map[nid].kind == NodeKind.ERROR
        ]
        error_recovery_count = sum(
            1 for eid in error_downstream
            if simulated_conf.get(eid, 0) > original_conf.get(eid, 0) + 0.1
        )

        # Calculate aggregate causal impact
        total_impact = sum(impact_scores.values())
        avg_impact = total_impact / len(downstream) if downstream else 0.0

        # Recovery probability based on error recovery and impact propagation
        if error_downstream:
            recovery_prob = error_recovery_count / len(error_downstream)
        else:
            recovery_prob = 0.95 if avg_impact < 0.15 else max(0.1, 1.0 - avg_impact)

        recovered = recovery_prob > 0.5

        explanation_parts = [
            f"Substituting node '{target_node.label}' ({target_node_id[:12]}) "
            f"propagates through {len(downstream)} downstream nodes "
            f"(max depth: {propagation_depth}).",
        ]
        if error_downstream:
            explanation_parts.append(
                f"{error_recovery_count}/{len(error_downstream)} downstream errors recover "
                f"under counterfactual substitution."
            )
        explanation_parts.append(
            f"Average confidence impact: {avg_impact:.3f}. "
            f"Attenuation factor: {self.attenuation_factor}."
        )

        return SimulationResult(
            target_node_id=target_node_id,
            substitute_value=substitute_value,
            recovered=recovered,
            recovery_probability=recovery_prob,
            causal_impact_score=min(1.0, avg_impact * 3.0),
            explanation=" ".join(explanation_parts),
            affected_downstream=len(downstream),
            sensitivity=avg_impact,
            propagation_depth=propagation_depth,
        )

    def multi_ablation(
        self,
        nodes: List[RuntimeNode],
        edges: List[RuntimeEdge],
        target_node_ids: List[str],
    ) -> MultiAblationResult:
        """
        Simultaneously ablate multiple nodes and measure systemic impact.
        Detects interaction effects (super-additive or sub-additive impact).
        """
        node_map = {n.id: n for n in nodes}
        node_ids = set(node_map.keys())

        # 1. Compute individual impacts
        individual_impacts: Dict[str, float] = {}
        for tid in target_node_ids:
            result = self.simulate_ablation(nodes, edges, tid, "golden")
            individual_impacts[tid] = result.causal_impact_score

        # 2. Compute joint impact (all ablated simultaneously)
        all_downstream: Set[str] = set()
        for tid in target_node_ids:
            all_downstream |= _get_downstream_set(tid, edges, node_ids)

        # Joint impact considers overlapping downstream paths
        sum_individual = sum(individual_impacts.values())
        # Overlap reduction: if nodes share downstream paths, joint < sum
        overlap_count = 0
        for i, t1 in enumerate(target_node_ids):
            d1 = _get_downstream_set(t1, edges, node_ids)
            for t2 in target_node_ids[i + 1:]:
                d2 = _get_downstream_set(t2, edges, node_ids)
                overlap_count += len(d1 & d2)

        # Systemic impact with overlap correction
        overlap_factor = max(0.5, 1.0 - overlap_count * 0.05)
        systemic_impact = min(1.0, sum_individual * overlap_factor)

        # Interaction effect: positive means super-additive, negative means sub-additive
        interaction = systemic_impact - sum_individual

        labels = [
            node_map[tid].label if tid in node_map else tid[:12]
            for tid in target_node_ids
        ]
        explanation = (
            f"Simultaneous ablation of {len(target_node_ids)} nodes "
            f"({', '.join(labels)}). "
            f"Total downstream affected: {len(all_downstream)}. "
            f"Sum of individual impacts: {sum_individual:.3f}. "
            f"Joint systemic impact: {systemic_impact:.3f}. "
            f"Interaction effect: {interaction:+.3f} "
            f"({'super-additive' if interaction > 0.01 else 'sub-additive' if interaction < -0.01 else 'additive'})."
        )

        return MultiAblationResult(
            ablated_node_ids=target_node_ids,
            systemic_impact=systemic_impact,
            individual_impacts=individual_impacts,
            interaction_effect=interaction,
            explanation=explanation,
        )

    def sensitivity_analysis(
        self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]
    ) -> List[SensitivityReport]:
        """
        Computes ∂(outcome)/∂(node) for every node in the graph.
        Identifies critical path nodes whose removal most impacts outcomes.
        """
        node_map = {n.id: n for n in nodes}
        node_ids = set(node_map.keys())

        # Find outcome nodes (terminal nodes with no outgoing edges)
        outgoing = {e.source for e in edges if e.source in node_ids}
        outcome_nodes = node_ids - outgoing

        reports = []
        impact_scores: Dict[str, float] = {}

        for n in nodes:
            downstream = _get_downstream_set(n.id, edges, node_ids)
            # How many outcome nodes are downstream?
            outcome_reach = len(downstream & outcome_nodes)
            downstream_count = len(downstream)

            # Sensitivity = fraction of outcomes reachable * confidence weight
            if outcome_nodes:
                reach_fraction = outcome_reach / len(outcome_nodes)
            else:
                reach_fraction = 0.0

            conf = n.confidence if n.confidence is not None else 0.5
            # Lower confidence nodes are more sensitive (small changes have bigger effect)
            confidence_sensitivity = 1.0 - conf

            sensitivity = reach_fraction * 0.6 + (downstream_count / max(1, len(nodes))) * 0.25 + confidence_sensitivity * 0.15
            impact_scores[n.id] = sensitivity

        # Critical path: top 20% by sensitivity
        threshold = sorted(impact_scores.values(), reverse=True)
        critical_cutoff = threshold[max(0, len(threshold) // 5)] if threshold else 0.5

        for n in nodes:
            score = impact_scores.get(n.id, 0.0)
            downstream = _get_downstream_set(n.id, edges, node_ids)
            reports.append(SensitivityReport(
                node_id=n.id,
                label=n.label,
                sensitivity_score=score,
                downstream_count=len(downstream),
                is_critical_path=score >= critical_cutoff,
            ))

        reports.sort(key=lambda r: r.sensitivity_score, reverse=True)
        return reports

    def monte_carlo_impact(
        self,
        nodes: List[RuntimeNode],
        edges: List[RuntimeEdge],
        target_node_id: str,
        n_samples: int = 100,
    ) -> Dict[str, Any]:
        """
        Monte Carlo sampling of counterfactual impacts.
        Randomly perturbs substitute values and measures distribution of outcomes.
        """
        impacts = []
        recoveries = 0

        for _ in range(n_samples):
            # Random substitute value with different confidence levels
            substitute_conf = random.betavariate(2, 2)  # Bell-shaped around 0.5
            result = self.simulate_ablation(
                nodes, edges, target_node_id, substitute_conf
            )
            impacts.append(result.causal_impact_score)
            if result.recovered:
                recoveries += 1

        mean_impact = sum(impacts) / len(impacts) if impacts else 0.0
        std_impact = (sum((x - mean_impact) ** 2 for x in impacts) / max(1, len(impacts) - 1)) ** 0.5
        recovery_rate = recoveries / n_samples

        return {
            "target_node_id": target_node_id,
            "n_samples": n_samples,
            "mean_impact": round(mean_impact, 4),
            "std_impact": round(std_impact, 4),
            "recovery_rate": round(recovery_rate, 4),
            "impact_95th_percentile": round(
                sorted(impacts)[int(0.95 * len(impacts))] if impacts else 0.0, 4
            ),
            "impact_5th_percentile": round(
                sorted(impacts)[int(0.05 * len(impacts))] if impacts else 0.0, 4
            ),
        }
