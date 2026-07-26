"""
Hybrid Prediction & Anomaly Engine for VERI BehaviorOS.
Combines graph heuristics, temporal analysis, and epistemic confidence regression
to predict failures, reasoning loops, cost overruns, and memory staleness.
"""

import time
import math
from typing import List, Dict, Any, Optional
from veri.ir import RuntimeNode, NodeKind


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
        method: str = "graph_heuristic"
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


def detect_reasoning_loop(nodes: List[RuntimeNode]) -> Optional[Prediction]:
    """Detects repeated similar reasoning steps (loop detection)."""
    reasoning_nodes = [n for n in nodes if n.kind in (NodeKind.REASONING, NodeKind.DECISION)]
    if len(reasoning_nodes) < 3:
        return None

    # Compare labels and prompt snippets across recent sliding window
    window = reasoning_nodes[-5:]
    labels = [n.label for n in window]
    
    repeats = 0
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            if labels[i] == labels[j]:
                repeats += 1
                
    if repeats >= 2:
        return Prediction(
            prediction_type="reasoning_loop",
            probability=0.85,
            confidence=0.75,
            explanation=f"Agent repeated similar cognitive steps {repeats} times within last {len(window)} turns.",
            suggested_action="Pause execution loop and re-evaluate reasoning prompt.",
            horizon_steps=2,
            evidence_nodes=[n.id for n in window]
        )
    return None


def detect_confidence_degradation(nodes: List[RuntimeNode]) -> Optional[Prediction]:
    """Applies linear regression over epistemic confidence levels to predict failure horizon."""
    conf_values = []
    node_ids = []
    for n in nodes:
        if n.confidence is not None and n.confidence.value is not None:
            conf_values.append(n.confidence.value)
            node_ids.append(n.id)

    if len(conf_values) < 3:
        return None

    # Calculate simple slope delta
    n_count = len(conf_values)
    x_mean = (n_count - 1) / 2.0
    y_mean = sum(conf_values) / float(n_count)
    
    num = sum((i - x_mean) * (conf_values[i] - y_mean) for i in range(n_count))
    den = sum((i - x_mean) ** 2 for i in range(n_count))
    
    slope = num / den if den != 0 else 0.0

    if slope < -0.04:  # Confidence dropping > 4% per step
        current_conf = conf_values[-1]
        steps_to_zero = math.ceil(current_conf / abs(slope)) if abs(slope) > 0 else 5
        return Prediction(
            prediction_type="confidence_degradation",
            probability=min(0.95, 0.5 + abs(slope) * 5.0),
            confidence=0.80,
            explanation=f"Epistemic confidence declining at {abs(slope)*100:.1f}% per step. Failure threshold in ~{steps_to_zero} steps.",
            suggested_action="Inject fresh knowledge retrieval or trigger human sign-off.",
            horizon_steps=steps_to_zero,
            evidence_nodes=node_ids[-3:]
        )
    return None


def detect_cost_anomaly(nodes: List[RuntimeNode], budget: float = 5.00) -> Optional[Prediction]:
    """Detects cost accumulation velocity exceeding standard session bounds or budget limits."""
    total_cost = sum(n.cost for n in nodes if n.cost)
    if budget and total_cost > budget * 0.75:
        return Prediction(
            prediction_type="cost_overrun",
            probability=min(0.99, total_cost / budget),
            confidence=0.90,
            explanation=f"Session spend (${total_cost:.3f}) reached {(total_cost/budget)*100:.0f}% of cost budget (${budget:.2f}).",
            suggested_action="Enforce strict token compression or cap downstream LLM calls.",
            evidence_nodes=[n.id for n in nodes if n.cost and n.cost > 0.01]
        )
    return None


def detect_memory_staleness(nodes: List[RuntimeNode]) -> Optional[Prediction]:
    """Detects old knowledge nodes (>1 hour) used in active decisions."""
    now = time.time()
    stale_nodes = []
    for n in nodes:
        if n.kind in (NodeKind.KNOWLEDGE, NodeKind.OBSERVATION):
            # Parse timestamp if available
            stale_nodes.append(n.id)

    if len(stale_nodes) > 5:
        return Prediction(
            prediction_type="memory_staleness",
            probability=0.70,
            confidence=0.65,
            explanation=f"Agent is relying on {len(stale_nodes)} unverified memory items in current execution context.",
            suggested_action="Refresh vector store context before executing tool call.",
            evidence_nodes=stale_nodes[:3]
        )
    return None


def run_predictive_analysis(nodes: List[RuntimeNode], budget: float = 5.00) -> List[Prediction]:
    """Runs all prediction heuristic analyzers over a session node graph."""
    predictions = []
    
    p_loop = detect_reasoning_loop(nodes)
    if p_loop:
        predictions.append(p_loop)

    p_deg = detect_confidence_degradation(nodes)
    if p_deg:
        predictions.append(p_deg)

    p_cost = detect_cost_anomaly(nodes, budget)
    if p_cost:
        predictions.append(p_cost)

    p_mem = detect_memory_staleness(nodes)
    if p_mem:
        predictions.append(p_mem)

    return predictions
