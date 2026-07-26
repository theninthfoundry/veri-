"""
VERI Behavior Genome — BehaviorOS v4.0

Extracts measurable "behavioral DNA" from agent execution traces.
A 13-dimensional trait vector that uniquely characterizes an agent's
behavioral personality, enabling:
  - Cross-session behavioral comparison
  - Drift detection over deployment cycles
  - Behavioral phenotype classification
  - Genome-based search and clustering

This engine answers: "What kind of agent IS this?" — its personality, not its output.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind


# ── Trait Definitions ─────────────────────────────────────────────

TRAIT_NAMES = [
    "decisiveness",           # 0: How quickly does the agent decide?
    "exploration_rate",       # 1: Ratio of exploration to exploitation
    "tool_diversity",         # 2: How many different tools does it use?
    "reasoning_depth",        # 3: Average reasoning chain length
    "risk_tolerance",         # 4: Willingness to act under uncertainty
    "recovery_speed",         # 5: How fast does it recover from errors?
    "delegation_tendency",    # 6: How often does it delegate to sub-agents?
    "confidence_calibration", # 7: How well does confidence predict success?
    "cost_efficiency",        # 8: Output quality per dollar spent
    "focus_persistence",      # 9: How long does it stay on a single goal?
    "learning_rate",          # 10: How much does behavior improve over time?
    "error_handling_style",   # 11: Retry vs. abort vs. escalate preference
    "autonomy_level",        # 12: How much does it act without confirmation?
]

# Behavioral phenotype labels
PHENOTYPE_LABELS = {
    "cautious_analytical": "Cautious Analytical",
    "aggressive_exploratory": "Aggressive Exploratory",
    "efficient_executor": "Efficient Executor",
    "methodical_planner": "Methodical Planner",
    "adaptive_learner": "Adaptive Learner",
    "risk_taker": "Risk Taker",
    "conservative_delegator": "Conservative Delegator",
    "balanced": "Balanced",
}


# ── Data Structures ────────────────────────────────────────────────


class BehaviorGenome:
    """
    A 13-dimensional feature vector encoding an agent's behavioral identity.
    Each trait is normalized to [0, 1].
    """

    def __init__(self, traits: Dict[str, float], session_id: str = ""):
        self.traits = {k: max(0.0, min(1.0, v)) for k, v in traits.items()}
        self.session_id = session_id

        # Ensure all 13 traits are present
        for trait in TRAIT_NAMES:
            if trait not in self.traits:
                self.traits[trait] = 0.5  # Neutral default

    @property
    def vector(self) -> List[float]:
        """Returns the trait vector in canonical order."""
        return [self.traits[t] for t in TRAIT_NAMES]

    @property
    def dimension(self) -> int:
        return len(TRAIT_NAMES)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "traits": {k: round(v, 4) for k, v in self.traits.items()},
            "vector": [round(v, 4) for v in self.vector],
            "session_id": self.session_id,
            "phenotype": classify_phenotype(self),
        }


class DriftReport:
    """Report of behavioral personality drift over time."""

    def __init__(
        self,
        drifted_traits: Dict[str, Tuple[float, float]],
        total_drift: float,
        is_significant: bool,
        explanation: str,
    ):
        self.drifted_traits = drifted_traits  # trait → (old_value, new_value)
        self.total_drift = total_drift
        self.is_significant = is_significant
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drifted_traits": {
                k: {"old": round(v[0], 4), "new": round(v[1], 4)}
                for k, v in self.drifted_traits.items()
            },
            "total_drift": round(self.total_drift, 4),
            "is_significant": self.is_significant,
            "explanation": self.explanation,
        }


# ── Genome Extraction ─────────────────────────────────────────────


def extract_genome(
    nodes: List[RuntimeNode],
    edges: List[RuntimeEdge],
    session_id: str = "",
) -> BehaviorGenome:
    """
    Computes a 13-trait behavioral genome from an execution trace.
    Each trait is computed from structural properties of the IR graph.
    """
    if not nodes:
        return BehaviorGenome({}, session_id)

    node_map = {n.id: n for n in nodes}
    kind_counts = Counter(n.kind for n in nodes)
    total_nodes = len(nodes)

    # Build adjacency
    children: Dict[str, List[str]] = {}
    parents: Dict[str, List[str]] = {}
    for e in edges:
        children.setdefault(e.source, []).append(e.target)
        parents.setdefault(e.target, []).append(e.source)

    traits: Dict[str, float] = {}

    # ── Trait 0: Decisiveness ────────────────────────────────────
    # Ratio of decisions to total reasoning steps
    reasoning_count = kind_counts.get(NodeKind.REASONING, 0) + kind_counts.get(NodeKind.REFLECTION, 0)
    decision_count = kind_counts.get(NodeKind.DECISION, 0)
    traits["decisiveness"] = decision_count / max(1, reasoning_count + decision_count)

    # ── Trait 1: Exploration Rate ────────────────────────────────
    # Ratio of exploration nodes (knowledge, observation) to action nodes
    explore_count = kind_counts.get(NodeKind.KNOWLEDGE, 0) + kind_counts.get(NodeKind.OBSERVATION, 0)
    action_count = kind_counts.get(NodeKind.ACTION, 0) + kind_counts.get(NodeKind.TOOL_INVOCATION, 0)
    traits["exploration_rate"] = explore_count / max(1, explore_count + action_count)

    # ── Trait 2: Tool Diversity ──────────────────────────────────
    # Number of unique tool labels / total tool invocations
    tool_nodes = [n for n in nodes if n.kind == NodeKind.TOOL_INVOCATION]
    unique_tools = len(set(n.label for n in tool_nodes))
    traits["tool_diversity"] = unique_tools / max(1, len(tool_nodes)) if tool_nodes else 0.5

    # ── Trait 3: Reasoning Depth ─────────────────────────────────
    # Average chain length of consecutive reasoning nodes
    reasoning_nodes = [n for n in nodes if n.kind in (NodeKind.REASONING, NodeKind.BELIEF)]
    if reasoning_nodes:
        # Count consecutive reasoning runs
        runs = []
        current_run = 1
        for i in range(1, len(nodes)):
            if nodes[i].kind in (NodeKind.REASONING, NodeKind.BELIEF):
                current_run += 1
            else:
                if current_run > 1:
                    runs.append(current_run)
                current_run = 1
        if current_run > 1:
            runs.append(current_run)
        avg_depth = sum(runs) / max(1, len(runs)) if runs else 1.0
        traits["reasoning_depth"] = min(1.0, avg_depth / 10.0)  # Normalize: 10 steps = max depth
    else:
        traits["reasoning_depth"] = 0.0

    # ── Trait 4: Risk Tolerance ──────────────────────────────────
    # Average confidence of action nodes (lower = higher risk tolerance)
    action_confs = [
        n.confidence for n in nodes
        if n.kind in (NodeKind.ACTION, NodeKind.TOOL_INVOCATION, NodeKind.DECISION)
        and n.confidence is not None
    ]
    if action_confs:
        avg_action_conf = sum(action_confs) / len(action_confs)
        traits["risk_tolerance"] = 1.0 - avg_action_conf  # Low confidence actions = risk tolerant
    else:
        traits["risk_tolerance"] = 0.5

    # ── Trait 5: Recovery Speed ──────────────────────────────────
    # Average distance from error to next successful action
    error_indices = [i for i, n in enumerate(nodes) if n.kind == NodeKind.ERROR]
    recovery_distances = []
    for ei in error_indices:
        for j in range(ei + 1, min(ei + 20, len(nodes))):
            if nodes[j].kind in (NodeKind.ACTION, NodeKind.OUTCOME):
                recovery_distances.append(j - ei)
                break
    if recovery_distances:
        avg_recovery = sum(recovery_distances) / len(recovery_distances)
        traits["recovery_speed"] = max(0.0, 1.0 - avg_recovery / 10.0)
    else:
        traits["recovery_speed"] = 0.8  # No errors = fast recovery default

    # ── Trait 6: Delegation Tendency ─────────────────────────────
    delegation_count = kind_counts.get(NodeKind.DELEGATION, 0)
    traits["delegation_tendency"] = min(1.0, delegation_count / max(1, total_nodes) * 10.0)

    # ── Trait 7: Confidence Calibration ──────────────────────────
    # How well does stated confidence predict actual outcomes?
    confident_outcomes = []
    for n in nodes:
        if n.confidence is not None and n.kind == NodeKind.OUTCOME:
            # Simple heuristic: outcome nodes that follow high-confidence decisions
            confident_outcomes.append(n.confidence)
    if confident_outcomes:
        # Calibration = 1 - average deviation from 1.0 for successful outcomes
        avg_outcome_conf = sum(confident_outcomes) / len(confident_outcomes)
        traits["confidence_calibration"] = avg_outcome_conf
    else:
        traits["confidence_calibration"] = 0.5

    # ── Trait 8: Cost Efficiency ─────────────────────────────────
    total_cost = sum(n.cost for n in nodes if n.cost)
    outcome_count = kind_counts.get(NodeKind.OUTCOME, 0) + kind_counts.get(NodeKind.DECISION, 0)
    if total_cost > 0 and outcome_count > 0:
        # Cost per useful outcome (lower = more efficient)
        cost_per_outcome = total_cost / outcome_count
        traits["cost_efficiency"] = max(0.0, 1.0 - min(1.0, cost_per_outcome / 0.10))
    else:
        traits["cost_efficiency"] = 0.5

    # ── Trait 9: Focus Persistence ───────────────────────────────
    # How many goals are pursued simultaneously vs sequentially?
    goal_nodes = [n for n in nodes if n.kind in (NodeKind.INTENT, NodeKind.SUBGOAL)]
    unique_goals = len(set(n.label for n in goal_nodes))
    traits["focus_persistence"] = 1.0 / max(1, unique_goals)

    # ── Trait 10: Learning Rate ──────────────────────────────────
    learning_count = kind_counts.get(NodeKind.LEARNING, 0) + kind_counts.get(NodeKind.REFLECTION, 0)
    traits["learning_rate"] = min(1.0, learning_count / max(1, total_nodes) * 5.0)

    # ── Trait 11: Error Handling Style ───────────────────────────
    # 0 = abort (errors with no recovery), 0.5 = retry, 1.0 = escalate
    error_count = kind_counts.get(NodeKind.ERROR, 0)
    escalation_count = kind_counts.get(NodeKind.ESCALATION, 0)
    if error_count > 0:
        if escalation_count > 0:
            traits["error_handling_style"] = 0.9  # Escalates
        elif recovery_distances:
            traits["error_handling_style"] = 0.5  # Retries
        else:
            traits["error_handling_style"] = 0.1  # Aborts
    else:
        traits["error_handling_style"] = 0.5  # No errors, neutral

    # ── Trait 12: Autonomy Level ─────────────────────────────────
    # Ratio of actions to escalations/delegations
    autonomous_actions = action_count
    non_autonomous = escalation_count + delegation_count
    traits["autonomy_level"] = autonomous_actions / max(1, autonomous_actions + non_autonomous)

    return BehaviorGenome(traits, session_id)


# ── Genome Operations ─────────────────────────────────────────────


def compute_distance(genome_a: BehaviorGenome, genome_b: BehaviorGenome) -> float:
    """
    Euclidean distance between two behavioral genomes.
    Lower distance = more similar behavioral personality.
    """
    vec_a = genome_a.vector
    vec_b = genome_b.vector
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec_a, vec_b)))


def classify_phenotype(genome: BehaviorGenome) -> str:
    """
    Classifies a behavioral genome into a human-readable phenotype.
    Uses trait clustering heuristics.
    """
    t = genome.traits

    if t["decisiveness"] > 0.7 and t["risk_tolerance"] > 0.6:
        return "aggressive_exploratory"
    if t["cost_efficiency"] > 0.7 and t["focus_persistence"] > 0.7:
        return "efficient_executor"
    if t["reasoning_depth"] > 0.6 and t["exploration_rate"] > 0.5:
        return "methodical_planner"
    if t["learning_rate"] > 0.6 and t["recovery_speed"] > 0.6:
        return "adaptive_learner"
    if t["risk_tolerance"] > 0.7 and t["autonomy_level"] > 0.8:
        return "risk_taker"
    if t["delegation_tendency"] > 0.5 and t["risk_tolerance"] < 0.3:
        return "conservative_delegator"
    if t["decisiveness"] < 0.3 and t["reasoning_depth"] > 0.5:
        return "cautious_analytical"

    return "balanced"


def detect_drift(
    genome_history: List[BehaviorGenome],
    significance_threshold: float = 0.15,
) -> Optional[DriftReport]:
    """
    Detects behavioral personality drift across deployment cycles.
    Compares the most recent genome against the historical average.
    """
    if len(genome_history) < 3:
        return None

    latest = genome_history[-1]

    # Compute historical average genome
    avg_traits: Dict[str, float] = {}
    history = genome_history[:-1]  # All except latest
    for trait in TRAIT_NAMES:
        values = [g.traits[trait] for g in history]
        avg_traits[trait] = sum(values) / len(values)

    # Find drifted traits
    drifted: Dict[str, Tuple[float, float]] = {}
    total_drift = 0.0

    for trait in TRAIT_NAMES:
        old_val = avg_traits[trait]
        new_val = latest.traits[trait]
        delta = abs(new_val - old_val)
        total_drift += delta ** 2

        if delta > significance_threshold:
            drifted[trait] = (old_val, new_val)

    total_drift = math.sqrt(total_drift)
    is_significant = total_drift > significance_threshold * 3

    if not drifted:
        return None

    trait_descriptions = [
        f"{trait}: {old:.2f} → {new:.2f} ({'↑' if new > old else '↓'})"
        for trait, (old, new) in sorted(drifted.items(), key=lambda x: abs(x[1][1] - x[1][0]), reverse=True)
    ]

    return DriftReport(
        drifted_traits=drifted,
        total_drift=total_drift,
        is_significant=is_significant,
        explanation=(
            f"Behavioral drift detected across {len(drifted)} traits "
            f"(total drift magnitude: {total_drift:.3f}). "
            f"Changed traits: {'; '.join(trait_descriptions[:5])}."
        ),
    )


def get_trait_stability(
    genomes: List[BehaviorGenome],
) -> Dict[str, float]:
    """
    Computes per-trait consistency (inverse variance) across sessions.
    Lower variance = more stable/consistent trait.
    """
    if len(genomes) < 2:
        return {t: 1.0 for t in TRAIT_NAMES}

    stability: Dict[str, float] = {}
    for trait in TRAIT_NAMES:
        values = [g.traits[trait] for g in genomes]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        # Stability = 1 / (1 + variance * 10) -- scaled to [0, 1]
        stability[trait] = 1.0 / (1.0 + variance * 10.0)

    return stability
