"""
VERI Behavioral State Engine — BehaviorOS v4.0

Models agent cognition as a formal state machine with continuous state variables.
Tracks cognitive phases (EXPLORING → REASONING → DECIDING → ACTING → REFLECTING)
and detects anomalous states (STUCK, OSCILLATING, DEGRADING).

This engine answers: "What is the agent *thinking*, not just *doing*?"
"""

import time
import math
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, deque

from veri.ir import RuntimeNode, NodeKind


# ── Cognitive Phase Model ─────────────────────────────────────────


class CognitivePhase(Enum):
    """The seven fundamental cognitive phases of an autonomous agent."""
    EXPLORING = "exploring"        # Gathering information, scanning environment
    REASONING = "reasoning"        # Processing information, building mental models
    DECIDING = "deciding"          # Selecting between alternatives
    ACTING = "acting"              # Executing tool calls, taking actions
    REFLECTING = "reflecting"      # Evaluating outcomes, learning
    RECOVERING = "recovering"      # Handling errors, replanning
    STUCK = "stuck"                # No progress, repeated states


# Phase classification rules: NodeKind → CognitivePhase
_PHASE_MAP: Dict[str, CognitivePhase] = {
    NodeKind.OBSERVATION: CognitivePhase.EXPLORING,
    NodeKind.KNOWLEDGE: CognitivePhase.EXPLORING,
    NodeKind.WORLD_STATE: CognitivePhase.EXPLORING,
    NodeKind.RESOURCE: CognitivePhase.EXPLORING,
    NodeKind.REASONING: CognitivePhase.REASONING,
    NodeKind.BELIEF: CognitivePhase.REASONING,
    NodeKind.ASSUMPTION: CognitivePhase.REASONING,
    NodeKind.UNKNOWN: CognitivePhase.REASONING,
    NodeKind.DECISION: CognitivePhase.DECIDING,
    NodeKind.PLAN: CognitivePhase.DECIDING,
    NodeKind.INTENT: CognitivePhase.DECIDING,
    NodeKind.SUBGOAL: CognitivePhase.DECIDING,
    NodeKind.ACTION: CognitivePhase.ACTING,
    NodeKind.TOOL_INVOCATION: CognitivePhase.ACTING,
    NodeKind.LLM_CALL: CognitivePhase.ACTING,
    NodeKind.DELEGATION: CognitivePhase.ACTING,
    NodeKind.REFLECTION: CognitivePhase.REFLECTING,
    NodeKind.LEARNING: CognitivePhase.REFLECTING,
    NodeKind.OUTCOME: CognitivePhase.REFLECTING,
    NodeKind.ERROR: CognitivePhase.RECOVERING,
    NodeKind.RISK: CognitivePhase.RECOVERING,
    NodeKind.ANOMALY: CognitivePhase.RECOVERING,
    NodeKind.ESCALATION: CognitivePhase.RECOVERING,
    NodeKind.CONFLICT: CognitivePhase.RECOVERING,
    NodeKind.CONSTRAINT: CognitivePhase.RECOVERING,
}


# ── State Transition ──────────────────────────────────────────────


class StateTransition:
    """Records a single cognitive phase transition."""

    def __init__(
        self,
        from_phase: CognitivePhase,
        to_phase: CognitivePhase,
        trigger_node_id: str,
        trigger_label: str,
        timestamp: float,
        dwell_time: float,  # Time spent in previous phase (seconds)
    ):
        self.from_phase = from_phase
        self.to_phase = to_phase
        self.trigger_node_id = trigger_node_id
        self.trigger_label = trigger_label
        self.timestamp = timestamp
        self.dwell_time = dwell_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_phase": self.from_phase.value,
            "to_phase": self.to_phase.value,
            "trigger_node_id": self.trigger_node_id,
            "trigger_label": self.trigger_label,
            "timestamp": self.timestamp,
            "dwell_time": round(self.dwell_time, 3),
        }


# ── Cognitive State Vector ────────────────────────────────────────


class CognitiveStateVector:
    """
    5-dimensional continuous representation of agent cognitive state.

    Dimensions:
        [0] confidence: Smoothed epistemic confidence (EWMA)
        [1] coherence:  How well current actions align with stated goals
        [2] focus:      Inverse of cognitive phase switching frequency
        [3] uncertainty: Accumulated unresolved uncertainty
        [4] momentum:   Rate of forward progress toward goals
    """

    def __init__(
        self,
        confidence: float = 0.5,
        coherence: float = 0.5,
        focus: float = 0.5,
        uncertainty: float = 0.5,
        momentum: float = 0.5,
    ):
        self.confidence = max(0.0, min(1.0, confidence))
        self.coherence = max(0.0, min(1.0, coherence))
        self.focus = max(0.0, min(1.0, focus))
        self.uncertainty = max(0.0, min(1.0, uncertainty))
        self.momentum = max(0.0, min(1.0, momentum))

    @property
    def values(self) -> List[float]:
        return [self.confidence, self.coherence, self.focus, self.uncertainty, self.momentum]

    @property
    def magnitude(self) -> float:
        """L2 norm of the state vector."""
        return math.sqrt(sum(v * v for v in self.values))

    def distance_to(self, other: "CognitiveStateVector") -> float:
        """Euclidean distance between two state vectors."""
        return math.sqrt(
            sum((a - b) ** 2 for a, b in zip(self.values, other.values))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": round(self.confidence, 4),
            "coherence": round(self.coherence, 4),
            "focus": round(self.focus, 4),
            "uncertainty": round(self.uncertainty, 4),
            "momentum": round(self.momentum, 4),
            "magnitude": round(self.magnitude, 4),
        }


# ── Anomaly Detection Results ─────────────────────────────────────


class CognitiveAnomaly:
    """Detected cognitive state anomaly."""

    def __init__(
        self,
        anomaly_type: str,
        severity: str,
        description: str,
        evidence_nodes: List[str],
        suggested_action: str,
    ):
        self.anomaly_type = anomaly_type
        self.severity = severity  # "low", "medium", "high", "critical"
        self.description = description
        self.evidence_nodes = evidence_nodes
        self.suggested_action = suggested_action

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description,
            "evidence_nodes": self.evidence_nodes,
            "suggested_action": self.suggested_action,
        }


# ── Behavioral State Engine ──────────────────────────────────────


class BehavioralStateEngine:
    """
    Core cognitive state machine that processes IR node streams
    and maintains a continuous model of agent cognition.
    """

    def __init__(self, stuck_threshold: int = 8, oscillation_window: int = 6):
        self.stuck_threshold = stuck_threshold
        self.oscillation_window = oscillation_window

        # State tracking
        self.current_phase: CognitivePhase = CognitivePhase.EXPLORING
        self.phase_entry_time: float = time.time()
        self.transitions: List[StateTransition] = []
        self.phase_history: deque = deque(maxlen=50)
        self.node_count: int = 0

        # State vector components
        self._confidence_ewma: float = 0.5
        self._confidence_alpha: float = 0.3
        self._phase_switches_recent: int = 0
        self._steps_since_outcome: int = 0
        self._error_count_recent: int = 0
        self._goal_nodes: List[str] = []
        self._action_node_labels: List[str] = []

    def ingest_node(self, node: RuntimeNode) -> Optional[StateTransition]:
        """
        Process a new IR node, update cognitive state, and detect phase transitions.

        Returns a StateTransition if the cognitive phase changed, None otherwise.
        """
        self.node_count += 1
        new_phase = self._classify_phase(node)

        # Update EWMA confidence
        if node.confidence is not None:
            self._confidence_ewma = (
                self._confidence_alpha * node.confidence
                + (1.0 - self._confidence_alpha) * self._confidence_ewma
            )

        # Track goals for coherence calculation
        if node.kind in (NodeKind.INTENT, NodeKind.SUBGOAL, NodeKind.PLAN):
            self._goal_nodes.append(node.label)

        # Track actions for momentum
        if node.kind in (NodeKind.ACTION, NodeKind.TOOL_INVOCATION):
            self._action_node_labels.append(node.label)

        # Track outcomes for momentum
        if node.kind == NodeKind.OUTCOME:
            self._steps_since_outcome = 0
        else:
            self._steps_since_outcome += 1

        # Track errors
        if node.kind in (NodeKind.ERROR, NodeKind.ANOMALY):
            self._error_count_recent += 1

        # Detect phase transition
        transition = None
        if new_phase != self.current_phase:
            now = node.timestamp if node.timestamp else time.time()
            dwell_time = now - self.phase_entry_time

            transition = StateTransition(
                from_phase=self.current_phase,
                to_phase=new_phase,
                trigger_node_id=node.id,
                trigger_label=node.label,
                timestamp=now,
                dwell_time=dwell_time,
            )
            self.transitions.append(transition)
            self.current_phase = new_phase
            self.phase_entry_time = now
            self._phase_switches_recent += 1

        self.phase_history.append(new_phase)
        return transition

    def ingest_nodes(self, nodes: List[RuntimeNode]) -> List[StateTransition]:
        """Batch ingest multiple nodes, returning all detected transitions."""
        transitions = []
        for node in nodes:
            t = self.ingest_node(node)
            if t:
                transitions.append(t)
        return transitions

    def get_cognitive_phase(self) -> CognitivePhase:
        """Returns the current cognitive phase classification."""
        # Check for STUCK override
        if self._is_stuck():
            return CognitivePhase.STUCK
        return self.current_phase

    def get_state_vector(self) -> CognitiveStateVector:
        """
        Computes the current 5-dimensional cognitive state vector.
        """
        # [0] Confidence: EWMA-tracked confidence
        confidence = self._confidence_ewma

        # [1] Coherence: Are actions aligned with goals?
        coherence = self._compute_coherence()

        # [2] Focus: Inverse of phase switching frequency
        focus = self._compute_focus()

        # [3] Uncertainty: Accumulated unresolved uncertainty
        uncertainty = self._compute_uncertainty()

        # [4] Momentum: Rate of forward progress
        momentum = self._compute_momentum()

        return CognitiveStateVector(
            confidence=confidence,
            coherence=coherence,
            focus=focus,
            uncertainty=uncertainty,
            momentum=momentum,
        )

    def detect_anomalous_states(self) -> List[CognitiveAnomaly]:
        """Detect all currently active cognitive anomalies."""
        anomalies = []

        # 1. STUCK detection
        if self._is_stuck():
            recent = list(self.phase_history)[-self.stuck_threshold:]
            anomalies.append(CognitiveAnomaly(
                anomaly_type="stuck",
                severity="high",
                description=(
                    f"Agent stuck in '{self.current_phase.value}' phase for "
                    f"{self.stuck_threshold}+ consecutive steps without transition."
                ),
                evidence_nodes=[
                    t.trigger_node_id for t in self.transitions[-3:]
                ] if self.transitions else [],
                suggested_action=(
                    "Inject alternative reasoning prompt or force goal re-evaluation. "
                    "Consider escalating to human oversight."
                ),
            ))

        # 2. OSCILLATING detection
        if self._is_oscillating():
            recent_phases = list(self.phase_history)[-self.oscillation_window:]
            phase_names = [p.value for p in recent_phases]
            anomalies.append(CognitiveAnomaly(
                anomaly_type="oscillating",
                severity="medium",
                description=(
                    f"Agent oscillating between phases rapidly: "
                    f"{' → '.join(phase_names)}. "
                    f"Indicates indecision or conflicting objectives."
                ),
                evidence_nodes=[
                    t.trigger_node_id for t in self.transitions[-3:]
                ] if self.transitions else [],
                suggested_action=(
                    "Reduce available options or add decision constraints. "
                    "Agent may need clearer objective function."
                ),
            ))

        # 3. DEGRADING confidence
        if self._confidence_ewma < 0.25:
            anomalies.append(CognitiveAnomaly(
                anomaly_type="degrading",
                severity="high",
                description=(
                    f"EWMA confidence degraded to {self._confidence_ewma:.3f}. "
                    f"Agent is increasingly uncertain about its own outputs."
                ),
                evidence_nodes=[
                    t.trigger_node_id for t in self.transitions[-2:]
                ] if self.transitions else [],
                suggested_action=(
                    "Inject fresh knowledge/context. Consider model upgrade or "
                    "human verification checkpoint."
                ),
            ))

        # 4. ERROR SPIRAL: too many errors without recovery
        if self._error_count_recent >= 3 and self.current_phase == CognitivePhase.RECOVERING:
            anomalies.append(CognitiveAnomaly(
                anomaly_type="error_spiral",
                severity="critical",
                description=(
                    f"Agent has encountered {self._error_count_recent} errors "
                    f"and is stuck in RECOVERING phase. Error spiral detected."
                ),
                evidence_nodes=[
                    t.trigger_node_id for t in self.transitions[-3:]
                ] if self.transitions else [],
                suggested_action="Halt execution immediately. Escalate to human operator.",
            ))

        return anomalies

    def get_trajectory(self) -> List[StateTransition]:
        """Returns the full cognitive phase transition history."""
        return list(self.transitions)

    def get_phase_distribution(self) -> Dict[str, float]:
        """Returns the fraction of time spent in each cognitive phase."""
        if not self.phase_history:
            return {}
        counts = Counter(p.value for p in self.phase_history)
        total = sum(counts.values())
        return {phase: count / total for phase, count in counts.items()}

    def get_transition_matrix(self) -> Dict[str, Dict[str, int]]:
        """Returns the observed phase transition count matrix."""
        matrix: Dict[str, Dict[str, int]] = {}
        for t in self.transitions:
            from_p = t.from_phase.value
            to_p = t.to_phase.value
            if from_p not in matrix:
                matrix[from_p] = {}
            matrix[from_p][to_p] = matrix[from_p].get(to_p, 0) + 1
        return matrix

    def to_dict(self) -> Dict[str, Any]:
        """Full state engine snapshot."""
        state_vec = self.get_state_vector()
        return {
            "current_phase": self.get_cognitive_phase().value,
            "state_vector": state_vec.to_dict(),
            "node_count": self.node_count,
            "transition_count": len(self.transitions),
            "phase_distribution": self.get_phase_distribution(),
            "anomalies": [a.to_dict() for a in self.detect_anomalous_states()],
            "recent_transitions": [
                t.to_dict() for t in self.transitions[-5:]
            ],
        }

    # ── Internal Computation ──────────────────────────────────────

    def _classify_phase(self, node: RuntimeNode) -> CognitivePhase:
        """Classify a node's cognitive phase from its kind."""
        return _PHASE_MAP.get(node.kind, CognitivePhase.EXPLORING)

    def _is_stuck(self) -> bool:
        """Detect if agent is stuck (same phase for too long)."""
        if len(self.phase_history) < self.stuck_threshold:
            return False
        recent = list(self.phase_history)[-self.stuck_threshold:]
        return len(set(recent)) == 1

    def _is_oscillating(self) -> bool:
        """Detect rapid phase oscillation (high switching frequency)."""
        if len(self.phase_history) < self.oscillation_window:
            return False
        recent = list(self.phase_history)[-self.oscillation_window:]
        transitions = sum(
            1 for i in range(1, len(recent)) if recent[i] != recent[i - 1]
        )
        # Oscillating if >80% of steps involve a phase change
        return transitions >= self.oscillation_window * 0.8

    def _compute_coherence(self) -> float:
        """
        Measures action-goal alignment.
        Higher when recent actions relate to stated goals.
        """
        if not self._goal_nodes or not self._action_node_labels:
            return 0.5  # No data, neutral

        # Jaccard-like: how many action labels share words with goal labels?
        goal_words = set()
        for g in self._goal_nodes[-5:]:
            goal_words |= set(g.lower().split())

        if not goal_words:
            return 0.5

        aligned = 0
        recent_actions = self._action_node_labels[-10:]
        for action in recent_actions:
            action_words = set(action.lower().split())
            if action_words & goal_words:
                aligned += 1

        return aligned / len(recent_actions) if recent_actions else 0.5

    def _compute_focus(self) -> float:
        """
        Inverse of phase switching frequency.
        High focus = staying in productive phases, low switching.
        """
        if len(self.phase_history) < 5:
            return 0.5

        recent = list(self.phase_history)[-10:]
        switches = sum(1 for i in range(1, len(recent)) if recent[i] != recent[i - 1])
        max_switches = len(recent) - 1

        return 1.0 - (switches / max_switches) if max_switches > 0 else 1.0

    def _compute_uncertainty(self) -> float:
        """
        Accumulated unresolved uncertainty.
        Increases with assumptions, unknowns, and low-confidence nodes.
        """
        base = 1.0 - self._confidence_ewma

        # Additional uncertainty from error count
        error_factor = min(0.3, self._error_count_recent * 0.05)

        return min(1.0, base + error_factor)

    def _compute_momentum(self) -> float:
        """
        Rate of forward progress toward goals.
        Decreases when many steps pass without an outcome.
        """
        if self._steps_since_outcome == 0:
            return 0.95

        # Momentum decays with steps since last outcome
        decay = math.exp(-0.1 * self._steps_since_outcome)
        return max(0.05, decay)
