"""
VERI Runtime Behavior Models — BehaviorOS v5.0

Specialized domain models for:
  - Failure Prediction Model (predicts session failure probability)
  - Planning Optimization Model (recommends optimal sub-goal decomposition)
  - Anomaly Classification Model (classifies behavioral anomalies into types)
  - Recovery Recommendation Model (generates step-by-step recovery plans)
"""

import math
from typing import List, Dict, Any, Optional

from veri.ir import RuntimeNode, NodeKind


class FailurePredictionModel:
    """Specialized model that predicts session failure probability before execution."""

    def predict_failure_probability(self, nodes: List[RuntimeNode]) -> float:
        if not nodes:
            return 0.0

        # Feature extraction
        error_count = sum(1 for n in nodes if n.kind == NodeKind.ERROR)
        low_conf_count = sum(1 for n in nodes if n.confidence is not None and n.confidence < 0.4)
        total_cost = sum(n.cost for n in nodes if n.cost)

        # Log-odds score
        score = -2.0 + (error_count * 1.5) + (low_conf_count * 0.8) + (total_cost * 2.0)
        prob = 1.0 / (1.0 + math.exp(-score))
        return round(prob, 4)


class PlanningOptimizationModel:
    """Specialized model for optimizing sub-goal decomposition."""

    def recommend_plan_adjustments(self, nodes: List[RuntimeNode]) -> List[Dict[str, Any]]:
        reasoning_count = sum(1 for n in nodes if n.kind == NodeKind.REASONING)
        adjustments = []

        if reasoning_count > 5:
            adjustments.append({
                "type": "prune_reasoning",
                "recommendation": "Consolidate excessive reasoning steps to reduce latency.",
                "confidence": 0.85,
            })

        return adjustments


class AnomalyClassificationModel:
    """Specialized model for classifying behavioral anomalies."""

    def classify_anomaly(self, anomaly_text: str) -> Dict[str, Any]:
        text_lower = anomaly_text.lower()
        if "loop" in text_lower or "repeat" in text_lower:
            return {"category": "reasoning_loop", "severity": "high", "action": "Break loop & force decision."}
        elif "cost" in text_lower or "budget" in text_lower:
            return {"category": "cost_overrun", "severity": "critical", "action": "Cap tokens & downgrade model."}
        elif "timeout" in text_lower or "504" in text_lower:
            return {"category": "tool_failure", "severity": "medium", "action": "Retry with exponential backoff."}

        return {"category": "general_anomaly", "severity": "low", "action": "Log anomaly for audit."}


class RecoveryRecommendationModel:
    """Specialized model for generating recovery plans from past failures."""

    def generate_recovery_plan(self, failure_node_label: str) -> List[str]:
        return [
            f"1. Isolate root cause of '{failure_node_label}'",
            "2. Verify prerequisite context from vector store",
            "3. Re-execute step with golden parameters",
            "4. Verify outcome against contract policy",
        ]
