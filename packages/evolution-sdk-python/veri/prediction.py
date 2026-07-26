"""
VERI Adaptive Prediction & Anomaly Engine — BehaviorOS v4.0

Production-grade prediction engine replacing static heuristics with:
  - Exponentially Weighted Moving Average (EWMA) confidence tracking
  - Markov chain transition matrix for behavioral sequence modeling
  - Shannon entropy anomaly detection over decision distributions
  - Page-Hinkley drift detection for behavioral regime changes
  - Adaptive thresholds learned from observed session distributions
"""

import math
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict

from veri.ir import RuntimeNode, NodeKind


# ── Data Structures ────────────────────────────────────────────────


class Prediction:
    """Represents a predicted anomaly or execution risk."""

    def __init__(
        self,
        prediction_type: str,
        probability: float,
        confidence: float,
        explanation: str,
        suggested_action: str,
        horizon_steps: Optional[int] = None,
        evidence_nodes: Optional[List[str]] = None,
        method: str = "adaptive",
    ):
        self.prediction_type = prediction_type
        self.probability = max(0.0, min(1.0, probability))
        self.confidence = max(0.0, min(1.0, confidence))
        self.explanation = explanation
        self.suggested_action = suggested_action
        self.horizon_steps = horizon_steps
        self.evidence_nodes = evidence_nodes or []
        self.method = method
        self.computed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_type": self.prediction_type,
            "probability": self.probability,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "suggested_action": self.suggested_action,
            "horizon_steps": self.horizon_steps,
            "evidence_nodes": self.evidence_nodes,
            "method": self.method,
            "computed_at": self.computed_at,
        }


# ── EWMA Confidence Tracker ───────────────────────────────────────


class EWMATracker:
    """
    Exponentially Weighted Moving Average tracker with dynamic smoothing.

    Uses adaptive α: higher α (faster response) when variance is high,
    lower α (more smoothing) when signal is stable.
    """

    def __init__(self, alpha_base: float = 0.3, variance_sensitivity: float = 2.0):
        self.alpha_base = alpha_base
        self.variance_sensitivity = variance_sensitivity
        self.ewma: Optional[float] = None
        self.ewma_variance: float = 0.0
        self.values: List[float] = []

    def update(self, value: float) -> float:
        """Ingests a new confidence value, returns current EWMA estimate."""
        self.values.append(value)

        if self.ewma is None:
            self.ewma = value
            return self.ewma

        # Adaptive alpha: increase responsiveness when variance spikes
        alpha = min(0.95, self.alpha_base + self.variance_sensitivity * self.ewma_variance)
        self.ewma = alpha * value + (1.0 - alpha) * self.ewma

        # Track variance of the EWMA itself for adaptive smoothing
        deviation = (value - self.ewma) ** 2
        self.ewma_variance = alpha * deviation + (1.0 - alpha) * self.ewma_variance

        return self.ewma

    @property
    def current(self) -> Optional[float]:
        return self.ewma

    @property
    def trend_slope(self) -> float:
        """Linear regression slope over recent EWMA values."""
        if len(self.values) < 3:
            return 0.0
        recent = self.values[-min(10, len(self.values)):]
        n = len(recent)
        x_mean = (n - 1) / 2.0
        y_mean = sum(recent) / n
        num = sum((i - x_mean) * (recent[i] - y_mean) for i in range(n))
        den = sum((i - x_mean) ** 2 for i in range(n))
        return num / den if den != 0 else 0.0


# ── Markov Chain Transition Model ─────────────────────────────────


class MarkovTransitionModel:
    """
    Builds a first-order Markov chain over NodeKind sequences.
    Learns P(next_kind | current_kind) from observed execution traces.
    Detects anomalous transitions with low probability.
    """

    def __init__(self):
        self.transition_counts: Dict[str, Counter] = defaultdict(Counter)
        self.state_counts: Counter = Counter()

    def observe_sequence(self, kinds: List[str]) -> None:
        """Ingests a sequence of NodeKind values to build the transition matrix."""
        for i in range(len(kinds) - 1):
            current, next_kind = kinds[i], kinds[i + 1]
            self.transition_counts[current][next_kind] += 1
            self.state_counts[current] += 1

    def transition_probability(self, from_kind: str, to_kind: str) -> float:
        """P(to_kind | from_kind) from observed transitions."""
        total = self.state_counts.get(from_kind, 0)
        if total == 0:
            return 0.0
        return self.transition_counts[from_kind].get(to_kind, 0) / total

    def sequence_log_likelihood(self, kinds: List[str]) -> float:
        """Log-likelihood of an observed sequence under the learned model."""
        if len(kinds) < 2:
            return 0.0
        log_ll = 0.0
        for i in range(len(kinds) - 1):
            p = self.transition_probability(kinds[i], kinds[i + 1])
            # Laplace smoothing to avoid log(0)
            p = max(p, 1e-6)
            log_ll += math.log(p)
        return log_ll

    def detect_anomalous_transitions(
        self, kinds: List[str], threshold: float = -2.5
    ) -> List[Tuple[int, str, str, float]]:
        """
        Returns transitions whose log-probability falls below threshold.
        Each entry: (position, from_kind, to_kind, log_prob)
        """
        anomalies = []
        for i in range(len(kinds) - 1):
            p = self.transition_probability(kinds[i], kinds[i + 1])
            log_p = math.log(max(p, 1e-6))
            if log_p < threshold:
                anomalies.append((i, kinds[i], kinds[i + 1], log_p))
        return anomalies

    def get_transition_matrix(self) -> Dict[str, Dict[str, float]]:
        """Returns the full transition probability matrix."""
        matrix = {}
        for from_kind, counts in self.transition_counts.items():
            total = self.state_counts[from_kind]
            matrix[from_kind] = {
                to_kind: count / total for to_kind, count in counts.items()
            }
        return matrix


# ── Shannon Entropy Anomaly Detector ──────────────────────────────


def compute_shannon_entropy(distribution: Dict[str, int]) -> float:
    """
    H(X) = -Σ p(x) * log2(p(x))

    High entropy = uniformly distributed decisions (exploring/uncertain).
    Low entropy = concentrated on few decision types (focused/stuck).
    """
    total = sum(distribution.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in distribution.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def detect_entropy_anomaly(
    nodes: List[RuntimeNode], window_size: int = 10
) -> Optional[Prediction]:
    """
    Computes decision entropy over a sliding window.
    Flags anomaly if entropy drops below 0.5 (stuck in one mode)
    or exceeds 3.0 (chaotic/unfocused behavior).
    """
    if len(nodes) < window_size:
        return None

    window = nodes[-window_size:]
    kind_counts = Counter(n.kind for n in window)
    entropy = compute_shannon_entropy(kind_counts)

    if entropy < 0.5:
        return Prediction(
            prediction_type="behavioral_fixation",
            probability=0.85,
            confidence=0.80,
            explanation=(
                f"Decision entropy dropped to {entropy:.2f} bits over last {window_size} steps. "
                f"Agent is fixated on {kind_counts.most_common(1)[0][0]} operations without diversification."
            ),
            suggested_action="Inject exploratory prompt or force alternative reasoning path.",
            horizon_steps=3,
            evidence_nodes=[n.id for n in window[-3:]],
            method="shannon_entropy",
        )

    if entropy > 3.0:
        return Prediction(
            prediction_type="behavioral_chaos",
            probability=0.75,
            confidence=0.70,
            explanation=(
                f"Decision entropy spiked to {entropy:.2f} bits over last {window_size} steps. "
                f"Agent is switching between {len(kind_counts)} different operation types chaotically."
            ),
            suggested_action="Reduce available tool set or add planning constraints.",
            horizon_steps=5,
            evidence_nodes=[n.id for n in window[-3:]],
            method="shannon_entropy",
        )

    return None


# ── Page-Hinkley Drift Detector ───────────────────────────────────


class PageHinkleyDetector:
    """
    Page-Hinkley test for detecting behavioral regime changes.

    Monitors the cumulative deviation of a signal from its running mean.
    When the deviation exceeds a threshold, a drift is detected.
    """

    def __init__(self, delta: float = 0.005, threshold: float = 50.0, alpha: float = 0.9999):
        self.delta = delta          # Minimum magnitude of change to detect
        self.threshold = threshold  # Detection threshold
        self.alpha = alpha          # Forgetting factor
        self.n = 0
        self.sum_values = 0.0
        self.cumulative_sum = 0.0
        self.min_cumulative = float("inf")
        self.drift_detected = False
        self.drift_points: List[int] = []

    def update(self, value: float) -> bool:
        """
        Ingests a new observation. Returns True if drift is detected.
        """
        self.n += 1
        self.sum_values += value
        mean = self.sum_values / self.n

        self.cumulative_sum = self.alpha * self.cumulative_sum + (value - mean - self.delta)
        self.min_cumulative = min(self.min_cumulative, self.cumulative_sum)

        page_hinkley_value = self.cumulative_sum - self.min_cumulative

        if page_hinkley_value > self.threshold:
            self.drift_detected = True
            self.drift_points.append(self.n)
            # Reset after detection
            self.sum_values = value
            self.n = 1
            self.cumulative_sum = 0.0
            self.min_cumulative = float("inf")
            return True
        return False


# ── Reasoning Loop Detector (Enhanced) ────────────────────────────


def detect_reasoning_loop(nodes: List[RuntimeNode]) -> Optional[Prediction]:
    """
    Enhanced loop detection using content fingerprinting, not just label comparison.
    Detects when agent revisits semantically identical states.
    """
    reasoning_nodes = [
        n for n in nodes if n.kind in (NodeKind.REASONING, NodeKind.DECISION, NodeKind.REFLECTION)
    ]
    if len(reasoning_nodes) < 4:
        return None

    # Build content fingerprints for comparison
    window = reasoning_nodes[-8:]
    fingerprints = []
    for n in window:
        # Fingerprint = sorted tuple of (label, content keys, kind)
        content_keys = tuple(sorted(n.content.keys())) if n.content else ()
        fingerprints.append((n.label, content_keys, n.kind))

    # Count duplicate fingerprints
    fp_counts = Counter(fingerprints)
    max_repeat = max(fp_counts.values())

    if max_repeat >= 3:
        repeated_fp = fp_counts.most_common(1)[0][0]
        repeat_nodes = [
            n for n in window
            if (n.label, tuple(sorted(n.content.keys())) if n.content else (), n.kind) == repeated_fp
        ]
        return Prediction(
            prediction_type="reasoning_loop",
            probability=min(0.95, 0.60 + max_repeat * 0.10),
            confidence=0.85,
            explanation=(
                f"Agent repeated semantically identical cognitive step '{repeated_fp[0]}' "
                f"{max_repeat} times within last {len(window)} reasoning steps. "
                f"Content fingerprint and node kind are identical across iterations."
            ),
            suggested_action="Break execution loop. Inject fresh context or escalate to human.",
            horizon_steps=1,
            evidence_nodes=[n.id for n in repeat_nodes],
            method="content_fingerprint_loop",
        )
    return None


# ── Confidence Degradation (EWMA-based) ──────────────────────────


def detect_confidence_degradation(nodes: List[RuntimeNode]) -> Optional[Prediction]:
    """
    Uses EWMA tracker with adaptive alpha to detect confidence erosion.
    More robust than raw linear regression — responds to regime changes.
    """
    tracker = EWMATracker(alpha_base=0.3)

    conf_nodes = []
    for n in nodes:
        if n.confidence is not None:
            tracker.update(n.confidence)
            conf_nodes.append(n)

    if len(conf_nodes) < 4:
        return None

    slope = tracker.trend_slope
    current_ewma = tracker.current

    if slope < -0.03 and current_ewma is not None:
        steps_to_critical = int(max(1, (current_ewma - 0.3) / abs(slope))) if abs(slope) > 0 else 10

        return Prediction(
            prediction_type="confidence_degradation",
            probability=min(0.95, 0.50 + abs(slope) * 8.0),
            confidence=0.82,
            explanation=(
                f"EWMA-tracked confidence declining at {abs(slope)*100:.1f}% per step. "
                f"Current smoothed confidence: {current_ewma:.3f}. "
                f"Critical threshold (0.30) reached in ~{steps_to_critical} steps."
            ),
            suggested_action="Inject fresh knowledge retrieval or trigger human verification checkpoint.",
            horizon_steps=steps_to_critical,
            evidence_nodes=[n.id for n in conf_nodes[-3:]],
            method="ewma_regression",
        )
    return None


# ── Cost Anomaly (Velocity-based) ─────────────────────────────────


def detect_cost_anomaly(
    nodes: List[RuntimeNode], budget: float = 5.00
) -> Optional[Prediction]:
    """
    Detects cost accumulation velocity, not just absolute spend.
    Predicts budget exhaustion time based on spending acceleration.
    """
    cost_nodes = [(n, n.cost) for n in nodes if n.cost and n.cost > 0]
    if len(cost_nodes) < 2:
        return None

    total_cost = sum(c for _, c in cost_nodes)
    budget_fraction = total_cost / budget if budget > 0 else 1.0

    # Calculate cost velocity (cost per step)
    velocities = [cost_nodes[i][1] for i in range(len(cost_nodes))]
    avg_velocity = sum(velocities) / len(velocities)

    # Check if velocity is accelerating
    if len(velocities) >= 3:
        first_half = sum(velocities[:len(velocities)//2]) / max(1, len(velocities)//2)
        second_half = sum(velocities[len(velocities)//2:]) / max(1, len(velocities) - len(velocities)//2)
        acceleration = second_half - first_half
    else:
        acceleration = 0.0

    remaining_budget = budget - total_cost
    steps_to_exhaustion = int(remaining_budget / avg_velocity) if avg_velocity > 0 else 999

    if budget_fraction > 0.70:
        return Prediction(
            prediction_type="cost_overrun",
            probability=min(0.99, budget_fraction),
            confidence=0.90,
            explanation=(
                f"Session spend ${total_cost:.3f} ({budget_fraction*100:.0f}% of ${budget:.2f} budget). "
                f"Cost velocity: ${avg_velocity:.4f}/step. "
                f"{'Accelerating' if acceleration > 0 else 'Stable'} spend pattern. "
                f"Budget exhaustion in ~{steps_to_exhaustion} steps."
            ),
            suggested_action="Enforce token compression, switch to cheaper model, or cap downstream calls.",
            evidence_nodes=[n.id for n, _ in cost_nodes[-3:]],
            method="cost_velocity",
        )
    return None


# ── Memory Staleness (Temporal Analysis) ──────────────────────────


def detect_memory_staleness(nodes: List[RuntimeNode]) -> Optional[Prediction]:
    """
    Detects knowledge nodes whose temporal distance from current context
    exceeds a freshness threshold, indicating potential hallucination risk.
    """
    now = time.time()
    knowledge_nodes = [
        n for n in nodes
        if n.kind in (NodeKind.KNOWLEDGE, NodeKind.OBSERVATION, NodeKind.BELIEF)
    ]
    decision_nodes = [n for n in nodes if n.kind in (NodeKind.DECISION, NodeKind.ACTION)]

    if not knowledge_nodes or not decision_nodes:
        return None

    latest_decision_time = max(n.timestamp for n in decision_nodes)
    stale_nodes = []

    for k in knowledge_nodes:
        age_seconds = latest_decision_time - k.timestamp
        if age_seconds > 3600:  # > 1 hour old
            stale_nodes.append((k, age_seconds))

    if len(stale_nodes) >= 3:
        avg_age = sum(age for _, age in stale_nodes) / len(stale_nodes)
        return Prediction(
            prediction_type="memory_staleness",
            probability=min(0.90, 0.40 + len(stale_nodes) * 0.08),
            confidence=0.70,
            explanation=(
                f"Agent relying on {len(stale_nodes)} knowledge items with average age "
                f"{avg_age/3600:.1f} hours. Decisions may be based on outdated information."
            ),
            suggested_action="Refresh vector store context and re-verify knowledge assumptions.",
            evidence_nodes=[n.id for n, _ in stale_nodes[:3]],
            method="temporal_staleness",
        )
    return None


# ── Behavioral Drift Detection ────────────────────────────────────


def detect_behavioral_drift(nodes: List[RuntimeNode]) -> Optional[Prediction]:
    """
    Uses Page-Hinkley test on the agent's decision entropy stream
    to detect behavioral regime changes (e.g., from exploratory to fixated).
    """
    if len(nodes) < 15:
        return None

    detector = PageHinkleyDetector(delta=0.01, threshold=8.0)
    window_size = 5

    for i in range(window_size, len(nodes)):
        window = nodes[i - window_size : i]
        kind_counts = Counter(n.kind for n in window)
        entropy = compute_shannon_entropy(kind_counts)

        if detector.update(entropy):
            return Prediction(
                prediction_type="behavioral_drift",
                probability=0.80,
                confidence=0.75,
                explanation=(
                    f"Page-Hinkley drift detected at step {i}. "
                    f"Agent behavioral regime changed significantly. "
                    f"Current entropy: {entropy:.2f} bits. "
                    f"Total drift events: {len(detector.drift_points)}."
                ),
                suggested_action="Log behavioral regime change. Consider checkpoint/rollback if unintended.",
                evidence_nodes=[n.id for n in nodes[max(0, i-3):i]],
                method="page_hinkley_drift",
            )
    return None


# ── Public API ─────────────────────────────────────────────────────


def run_predictive_analysis(
    nodes: List[RuntimeNode],
    budget: float = 5.00,
    markov_model: Optional[MarkovTransitionModel] = None,
) -> List[Prediction]:
    """
    Runs all adaptive prediction analyzers over a session node graph.

    Returns a list of Prediction objects, ordered by probability (highest first).
    """
    predictions: List[Prediction] = []

    # 1. Enhanced reasoning loop detection
    p = detect_reasoning_loop(nodes)
    if p:
        predictions.append(p)

    # 2. EWMA-based confidence degradation
    p = detect_confidence_degradation(nodes)
    if p:
        predictions.append(p)

    # 3. Cost velocity analysis
    p = detect_cost_anomaly(nodes, budget)
    if p:
        predictions.append(p)

    # 4. Temporal memory staleness
    p = detect_memory_staleness(nodes)
    if p:
        predictions.append(p)

    # 5. Shannon entropy anomaly detection
    p = detect_entropy_anomaly(nodes)
    if p:
        predictions.append(p)

    # 6. Page-Hinkley behavioral drift detection
    p = detect_behavioral_drift(nodes)
    if p:
        predictions.append(p)

    # 7. Markov chain anomalous transition detection
    if markov_model:
        kinds = [n.kind for n in nodes]
        anomalous = markov_model.detect_anomalous_transitions(kinds)
        if anomalous:
            worst = min(anomalous, key=lambda x: x[3])
            pos, from_k, to_k, log_p = worst
            predictions.append(Prediction(
                prediction_type="anomalous_transition",
                probability=min(0.90, 0.50 + abs(log_p) * 0.10),
                confidence=0.72,
                explanation=(
                    f"Anomalous state transition at step {pos}: {from_k} → {to_k} "
                    f"(log-probability: {log_p:.2f}). This transition has rarely been "
                    f"observed in historical execution patterns."
                ),
                suggested_action="Verify agent reasoning path. This transition deviates from learned behavior.",
                evidence_nodes=[nodes[pos].id] if pos < len(nodes) else [],
                method="markov_anomaly",
            ))

    # Sort by probability descending
    predictions.sort(key=lambda p: p.probability, reverse=True)
    return predictions
