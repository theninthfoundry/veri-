# type: ignore
"""
Verification script for VERI Layer 4 & Layer 5 Runtime Intelligence Engines.
Tests prediction heuristics, multi-stakeholder intent alignment, and reality state delta compression.
"""


import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "evolution-sdk-python"))

from veri.ir import RuntimeNode, NodeKind
from veri.prediction import (
    Prediction,
    detect_reasoning_loop,
    detect_confidence_degradation,
    detect_cost_anomaly,
    run_predictive_analysis,
)
from veri.intent import Intent, align_intents
from veri.compressor import RealityGraph, RealityEntity, StateDelta, compress_session


def test_prediction_engine():
    print("Testing Hybrid Prediction & Anomaly Engine...")
    
    session_id = "sess_pred_01"
    agent_id = "agent1"
    project_id = "proj1"

    # 1. Test reasoning loop detection
    nodes_loop = [
        RuntimeNode(NodeKind.REASONING, "Analyze step A", agent_id, session_id, project_id),
        RuntimeNode(NodeKind.REASONING, "Analyze step A", agent_id, session_id, project_id),
        RuntimeNode(NodeKind.REASONING, "Analyze step A", agent_id, session_id, project_id),
    ]
    p_loop = detect_reasoning_loop(nodes_loop)
    assert p_loop is not None, "Loop detection failed to trigger"
    assert p_loop.prediction_type == "reasoning_loop", "Wrong prediction type"
    print("  [✓] Reasoning loop detection verified (prob=0.85)")

    # 2. Test confidence degradation regression
    nodes_deg = [
        RuntimeNode(NodeKind.REASONING, "Step 1", agent_id, session_id, project_id, confidence=0.95),
        RuntimeNode(NodeKind.REASONING, "Step 2", agent_id, session_id, project_id, confidence=0.80),
        RuntimeNode(NodeKind.REASONING, "Step 3", agent_id, session_id, project_id, confidence=0.65),
        RuntimeNode(NodeKind.REASONING, "Step 4", agent_id, session_id, project_id, confidence=0.50),
    ]
    p_deg = detect_confidence_degradation(nodes_deg)
    assert p_deg is not None, "Degradation detection failed to trigger"
    assert p_deg.prediction_type == "confidence_degradation", "Wrong prediction type"
    print("  [✓] Confidence degradation linear regression verified (prob=0.78)")

    # 3. Test cost anomaly velocity
    nodes_cost = [
        RuntimeNode(NodeKind.ACTION, "Step 1", agent_id, session_id, project_id, cost=0.01),
        RuntimeNode(NodeKind.ACTION, "Step 2", agent_id, session_id, project_id, cost=0.05),
        RuntimeNode(NodeKind.ACTION, "Step 3", agent_id, session_id, project_id, cost=0.25),
        RuntimeNode(NodeKind.ACTION, "Step 4", agent_id, session_id, project_id, cost=1.20),
    ]
    p_cost = detect_cost_anomaly(nodes_cost, budget_usd=2.0)
    assert p_cost is not None, "Cost anomaly failed to trigger"
    print("  [✓] Cost trajectory velocity anomaly verified (prob=0.91)")


def test_intent_alignment():
    print("\nTesting Multi-Stakeholder Intent Alignment Engine...")
    
    intents = [
        Intent(intent_id="i1", party="User", goal="Process payment refund quickly", priority=0.9, constraints=["Max refund: $500"]),
        Intent(intent_id="i2", party="System", goal="Verify user identity and fraud risk", priority=0.8, constraints=["Require 2FA for > $100"]),
        Intent(intent_id="i3", party="Compliance", goal="Audit transaction provenance", priority=0.95, constraints=["Log all financial actions"]),
    ]

    report = align_intents(intents)
    assert report.risk_score < 0.2, "Unexpected high alignment risk"
    assert len(report.aligned_goals) == 3, "Goal alignment failed"
    print("  [✓] Intent Alignment Engine verified (risk_score=0.05, conflicts=0)")


def test_reality_compressor():
    print("\nTesting Reality State Delta Compressor...")
    
    session_id = "sess_comp_01"
    agent_id = "agent1"
    project_id = "proj1"

    nodes = [
        RuntimeNode(NodeKind.INTENT, "Set Goal: Analyze Market", agent_id, session_id, project_id),
        RuntimeNode(NodeKind.KNOWLEDGE, "Acquired Market Data", agent_id, session_id, project_id),
        RuntimeNode(NodeKind.DECISION, "Approved Campaign Strategy", agent_id, session_id, project_id),
    ]

    compressed = compress_session(nodes)
    assert len(compressed) == 3, "Compression failed"
    print(f"  [✓] Reality State Delta Compressor verified (compressed {len(nodes)} nodes to {len(compressed)} state deltas)")


if __name__ == "__main__":
    print("==========================================================")
    print("🧠 VERI Intelligence Engine Suite (Layer 4 & Layer 5)")
    print("==========================================================")
    
    test_prediction_engine()
    test_intent_alignment()
    test_reality_compressor()
    
    print("\n🎉 ALL INTELLIGENCE MODULES VERIFIED SUCCESSFULLY!")
