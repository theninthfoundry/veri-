"""
VERI Behavioral Physics Engine — BehaviorOS v4.0

Models agent behavior using dynamical systems theory:
  - Behavioral state as position in continuous phase space
  - Forces (pressures) acting on the agent
  - Momentum tracking (rate of change of behavioral state)
  - Energy conservation (kinetic + potential behavioral energy)
  - Phase transition detection (critical regime changes)
  - Attractor identification (behavioral fixed points)

This engine answers: "What FORCES are shaping the agent's behavior?"
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from collections import deque

from veri.ir import RuntimeNode, NodeKind


# ── Data Structures ────────────────────────────────────────────────


class BehavioralState:
    """
    Position in continuous behavioral phase space.

    Dimensions:
        confidence:        Epistemic confidence level [0, 1]
        cost_velocity:     Rate of cost accumulation ($/step)
        reasoning_momentum: Reasoning chain velocity (reasoning nodes/step)
        decision_entropy:  Shannon entropy of recent decision distribution
    """

    def __init__(
        self,
        confidence: float = 0.5,
        cost_velocity: float = 0.0,
        reasoning_momentum: float = 0.0,
        decision_entropy: float = 1.0,
    ):
        self.confidence = confidence
        self.cost_velocity = cost_velocity
        self.reasoning_momentum = reasoning_momentum
        self.decision_entropy = decision_entropy

    @property
    def position(self) -> List[float]:
        return [self.confidence, self.cost_velocity, self.reasoning_momentum, self.decision_entropy]

    @property
    def magnitude(self) -> float:
        return math.sqrt(sum(v * v for v in self.position))

    def distance_to(self, other: "BehavioralState") -> float:
        return math.sqrt(
            sum((a - b) ** 2 for a, b in zip(self.position, other.position))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": round(self.confidence, 4),
            "cost_velocity": round(self.cost_velocity, 6),
            "reasoning_momentum": round(self.reasoning_momentum, 4),
            "decision_entropy": round(self.decision_entropy, 4),
            "magnitude": round(self.magnitude, 4),
        }


class BehavioralForce:
    """A pressure or force acting on the agent's behavioral state."""

    def __init__(
        self,
        force_type: str,
        magnitude: float,
        direction: str,
        source: str,
    ):
        self.force_type = force_type  # "time_pressure", "cost_pressure", "complexity_pressure", "uncertainty_pressure"
        self.magnitude = magnitude    # Strength of force [0, 1]
        self.direction = direction    # "accelerating" or "decelerating"
        self.source = source          # What causes this force

    def to_dict(self) -> Dict[str, Any]:
        return {
            "force_type": self.force_type,
            "magnitude": round(self.magnitude, 4),
            "direction": self.direction,
            "source": self.source,
        }


class MomentumVector:
    """Rate of change of the behavioral state."""

    def __init__(
        self,
        d_confidence: float = 0.0,
        d_cost_velocity: float = 0.0,
        d_reasoning_momentum: float = 0.0,
        d_decision_entropy: float = 0.0,
    ):
        self.d_confidence = d_confidence
        self.d_cost_velocity = d_cost_velocity
        self.d_reasoning_momentum = d_reasoning_momentum
        self.d_decision_entropy = d_decision_entropy

    @property
    def magnitude(self) -> float:
        return math.sqrt(
            self.d_confidence ** 2
            + self.d_cost_velocity ** 2
            + self.d_reasoning_momentum ** 2
            + self.d_decision_entropy ** 2
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "d_confidence": round(self.d_confidence, 4),
            "d_cost_velocity": round(self.d_cost_velocity, 6),
            "d_reasoning_momentum": round(self.d_reasoning_momentum, 4),
            "d_decision_entropy": round(self.d_decision_entropy, 4),
            "magnitude": round(self.magnitude, 4),
        }


class BehavioralEnergy:
    """
    Total behavioral energy = kinetic + potential.

    Kinetic: Energy of motion (rate of state change)
    Potential: Stored uncertainty/risk energy (accumulated unresolved tension)
    """

    def __init__(self, kinetic: float, potential: float):
        self.kinetic = kinetic
        self.potential = potential

    @property
    def total(self) -> float:
        return self.kinetic + self.potential

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kinetic": round(self.kinetic, 4),
            "potential": round(self.potential, 4),
            "total": round(self.total, 4),
        }


class PhaseTransition:
    """A detected critical behavioral regime change."""

    def __init__(
        self,
        transition_type: str,
        step_index: int,
        before_state: BehavioralState,
        after_state: BehavioralState,
        magnitude: float,
        explanation: str,
    ):
        self.transition_type = transition_type
        self.step_index = step_index
        self.before_state = before_state
        self.after_state = after_state
        self.magnitude = magnitude
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_type": self.transition_type,
            "step_index": self.step_index,
            "before_state": self.before_state.to_dict(),
            "after_state": self.after_state.to_dict(),
            "magnitude": round(self.magnitude, 4),
            "explanation": self.explanation,
        }


class Attractor:
    """A behavioral fixed point the agent converges toward."""

    def __init__(
        self,
        attractor_type: str,
        center: BehavioralState,
        basin_radius: float,
        stability: float,
        explanation: str,
    ):
        self.attractor_type = attractor_type  # "fixed_point", "limit_cycle", "strange_attractor"
        self.center = center
        self.basin_radius = basin_radius  # How far away states still converge to this point
        self.stability = stability  # 0-1: how strongly states are pulled toward attractor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attractor_type": self.attractor_type,
            "center": self.center.to_dict(),
            "basin_radius": round(self.basin_radius, 4),
            "stability": round(self.stability, 4),
        }


# ── Behavioral Physics Engine ────────────────────────────────────


class BehavioralPhysicsEngine:
    """
    Models agent behavior as a dynamical system with state variables,
    forces, momentum, and energy conservation.
    """

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.state_history: List[BehavioralState] = []

    def compute_state(self, nodes: List[RuntimeNode]) -> BehavioralState:
        """Compute current behavioral state from IR node stream."""
        if not nodes:
            return BehavioralState()

        # Confidence: EWMA of recent node confidences
        confs = [n.confidence for n in nodes if n.confidence is not None]
        confidence = sum(confs[-self.window_size:]) / max(1, len(confs[-self.window_size:])) if confs else 0.5

        # Cost velocity: cost per step in recent window
        recent = nodes[-self.window_size:]
        costs = [n.cost for n in recent if n.cost]
        cost_velocity = sum(costs) / max(1, len(recent))

        # Reasoning momentum: reasoning nodes per step
        reasoning_count = sum(
            1 for n in recent
            if n.kind in (NodeKind.REASONING, NodeKind.BELIEF, NodeKind.REFLECTION)
        )
        reasoning_momentum = reasoning_count / max(1, len(recent))

        # Decision entropy: Shannon entropy of node kinds in window
        from collections import Counter
        kind_counts = Counter(n.kind for n in recent)
        total = sum(kind_counts.values())
        entropy = 0.0
        for count in kind_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        decision_entropy = entropy

        state = BehavioralState(
            confidence=confidence,
            cost_velocity=cost_velocity,
            reasoning_momentum=reasoning_momentum,
            decision_entropy=decision_entropy,
        )
        self.state_history.append(state)
        return state

    def compute_forces(
        self,
        nodes: List[RuntimeNode],
        budget: float = 5.0,
        time_limit: float = 300.0,
    ) -> List[BehavioralForce]:
        """Compute active forces/pressures acting on the agent."""
        forces = []

        if not nodes:
            return forces

        # 1. Cost Pressure: increases as spending approaches budget
        total_cost = sum(n.cost for n in nodes if n.cost)
        cost_fraction = total_cost / budget if budget > 0 else 0.0
        if cost_fraction > 0.5:
            forces.append(BehavioralForce(
                force_type="cost_pressure",
                magnitude=min(1.0, cost_fraction),
                direction="decelerating",
                source=f"Session cost ${total_cost:.3f} ({cost_fraction*100:.0f}% of budget)",
            ))

        # 2. Time Pressure: increases with session duration
        if len(nodes) >= 2:
            duration = nodes[-1].timestamp - nodes[0].timestamp
            time_fraction = duration / time_limit if time_limit > 0 else 0.0
            if time_fraction > 0.5:
                forces.append(BehavioralForce(
                    force_type="time_pressure",
                    magnitude=min(1.0, time_fraction),
                    direction="accelerating",
                    source=f"Session duration {duration:.0f}s ({time_fraction*100:.0f}% of limit)",
                ))

        # 3. Complexity Pressure: increases with graph size and branching
        from collections import Counter
        kind_diversity = len(set(n.kind for n in nodes[-20:]))
        if kind_diversity > 6:
            forces.append(BehavioralForce(
                force_type="complexity_pressure",
                magnitude=min(1.0, kind_diversity / 10.0),
                direction="decelerating",
                source=f"{kind_diversity} distinct operation types in recent window",
            ))

        # 4. Uncertainty Pressure: increases with low/declining confidence
        confs = [n.confidence for n in nodes if n.confidence is not None]
        if confs:
            recent_confs = confs[-10:]
            avg_conf = sum(recent_confs) / len(recent_confs)
            if avg_conf < 0.4:
                forces.append(BehavioralForce(
                    force_type="uncertainty_pressure",
                    magnitude=1.0 - avg_conf,
                    direction="decelerating",
                    source=f"Average confidence {avg_conf:.2f} in recent window",
                ))

        # 5. Error Pressure: accumulates with unresolved errors
        error_count = sum(1 for n in nodes[-20:] if n.kind == NodeKind.ERROR)
        if error_count >= 2:
            forces.append(BehavioralForce(
                force_type="error_pressure",
                magnitude=min(1.0, error_count * 0.25),
                direction="decelerating",
                source=f"{error_count} errors in recent window",
            ))

        return forces

    def compute_momentum(
        self, state_history: Optional[List[BehavioralState]] = None
    ) -> MomentumVector:
        """
        Compute behavioral momentum as finite differences of state history.
        Momentum = ΔState / ΔStep
        """
        history = state_history or self.state_history
        if len(history) < 2:
            return MomentumVector()

        s1 = history[-2]
        s2 = history[-1]

        return MomentumVector(
            d_confidence=s2.confidence - s1.confidence,
            d_cost_velocity=s2.cost_velocity - s1.cost_velocity,
            d_reasoning_momentum=s2.reasoning_momentum - s1.reasoning_momentum,
            d_decision_entropy=s2.decision_entropy - s1.decision_entropy,
        )

    def compute_energy(
        self, state: Optional[BehavioralState] = None
    ) -> BehavioralEnergy:
        """
        Compute behavioral energy.

        Kinetic energy: proportional to momentum magnitude (rate of state change)
        Potential energy: accumulated uncertainty/risk (stored tension)
        """
        if not self.state_history:
            return BehavioralEnergy(0.0, 0.0)

        momentum = self.compute_momentum()

        # Kinetic energy = 0.5 * |momentum|^2
        kinetic = 0.5 * momentum.magnitude ** 2

        # Potential energy = accumulated uncertainty (distance from ideal state)
        current = state or self.state_history[-1]
        ideal = BehavioralState(
            confidence=0.95, cost_velocity=0.0,
            reasoning_momentum=0.3, decision_entropy=1.5,
        )
        potential = current.distance_to(ideal) * 0.5

        return BehavioralEnergy(kinetic=kinetic, potential=potential)

    def detect_phase_transitions(
        self, state_history: Optional[List[BehavioralState]] = None
    ) -> List[PhaseTransition]:
        """
        Detects critical points where behavioral regime changes occur.
        A phase transition = state change magnitude exceeds threshold.
        """
        history = state_history or self.state_history
        transitions: List[PhaseTransition] = []

        if len(history) < 3:
            return transitions

        # Compute moving average of state change magnitudes
        changes: List[float] = []
        for i in range(1, len(history)):
            changes.append(history[i].distance_to(history[i - 1]))

        if not changes:
            return transitions

        mean_change = sum(changes) / len(changes)
        std_change = math.sqrt(
            sum((c - mean_change) ** 2 for c in changes) / max(1, len(changes) - 1)
        )

        # Phase transition: change > mean + 2*std
        threshold = mean_change + 2.0 * std_change

        for i, change in enumerate(changes):
            if change > threshold and change > 0.1:
                before = history[i]
                after = history[i + 1]

                # Classify transition type
                if after.confidence - before.confidence > 0.2:
                    t_type = "confidence_jump"
                elif before.confidence - after.confidence > 0.2:
                    t_type = "confidence_collapse"
                elif after.decision_entropy - before.decision_entropy > 0.5:
                    t_type = "exploration_burst"
                elif before.decision_entropy - after.decision_entropy > 0.5:
                    t_type = "exploitation_lock"
                elif after.cost_velocity > before.cost_velocity * 2:
                    t_type = "cost_acceleration"
                else:
                    t_type = "regime_change"

                transitions.append(PhaseTransition(
                    transition_type=t_type,
                    step_index=i + 1,
                    before_state=before,
                    after_state=after,
                    magnitude=change,
                    explanation=(
                        f"Behavioral phase transition at step {i+1}: {t_type}. "
                        f"State change magnitude {change:.3f} (threshold: {threshold:.3f})."
                    ),
                ))

        return transitions

    def find_attractors(
        self, state_history: Optional[List[BehavioralState]] = None
    ) -> List[Attractor]:
        """
        Identifies behavioral fixed points by clustering state history.
        Regions where the agent spends disproportionate time indicate attractors.
        """
        history = state_history or self.state_history
        if len(history) < 5:
            return []

        # Simple density-based clustering
        # Grid the state space and find high-density regions
        grid_size = 0.15
        grid_counts: Dict[Tuple[int, ...], List[BehavioralState]] = {}

        for state in history:
            grid_key = tuple(
                int(v / grid_size) for v in state.position
            )
            grid_counts.setdefault(grid_key, []).append(state)

        # Find high-density cells (> 20% of states)
        threshold = max(2, len(history) * 0.15)
        attractors: List[Attractor] = []

        for grid_key, states in grid_counts.items():
            if len(states) >= threshold:
                # Compute centroid
                center_vals = [0.0] * 4
                for s in states:
                    for i, v in enumerate(s.position):
                        center_vals[i] += v
                center_vals = [v / len(states) for v in center_vals]

                center = BehavioralState(
                    confidence=center_vals[0],
                    cost_velocity=center_vals[1],
                    reasoning_momentum=center_vals[2],
                    decision_entropy=center_vals[3],
                )

                # Basin radius: max distance from center
                max_dist = max(s.distance_to(center) for s in states)

                # Stability: fraction of history in this basin
                stability = len(states) / len(history)

                # Classify attractor type
                if stability > 0.5:
                    a_type = "fixed_point"
                elif len(set(tuple(int(v / (grid_size/2)) for v in s.position) for s in states)) > 3:
                    a_type = "limit_cycle"
                else:
                    a_type = "fixed_point"

                attractors.append(Attractor(
                    attractor_type=a_type,
                    center=center,
                    basin_radius=max_dist,
                    stability=stability,
                    explanation=f"Behavioral attractor at ({', '.join(f'{v:.2f}' for v in center_vals)})",
                ))

        attractors.sort(key=lambda a: a.stability, reverse=True)
        return attractors

    def to_dict(self, nodes: List[RuntimeNode]) -> Dict[str, Any]:
        """Full physics engine analysis."""
        state = self.compute_state(nodes)
        momentum = self.compute_momentum()
        energy = self.compute_energy(state)
        forces = self.compute_forces(nodes)
        transitions = self.detect_phase_transitions()
        attractors = self.find_attractors()

        return {
            "state": state.to_dict(),
            "momentum": momentum.to_dict(),
            "energy": energy.to_dict(),
            "forces": [f.to_dict() for f in forces],
            "phase_transitions": [t.to_dict() for t in transitions],
            "attractors": [a.to_dict() for a in attractors],
        }
