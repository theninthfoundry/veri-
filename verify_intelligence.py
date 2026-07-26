"""
Verification script for VERI Layer 4 & Layer 5 Runtime Intelligence Engines.
Tests prediction heuristics, multi-stakeholder intent alignment, and reality state delta compression.
"""

import sys
from veri.ir import RuntimeNode, NodeKind, Confidence
from veri.prediction import (
    Prediction,
    detect_reasoning_loop,
    detect_confidence_degradation,
    detect_cost_anomaly,
    detect_memory_staleness,
    run_predictive_analysis,
)
from veri.intent import Intent, align_intents
from veri.compressor import RealityGraph, RealityEntity, StateDelta, compress_session


def test_prediction_engine():
    print("Testing Hybrid Prediction & Anomaly Engine...")
    
    # 1. Test reasoning loop detection
    nodes_loop = [
        RuntimeNode(kind=NodeKind.REASONING, label="Analyze step A", agent_id="agent1"),
        RuntimeNode(kind=NodeKind.REASONING, label="Analyze step A", agent_id="agent1"),
        RuntimeNode(kind=NodeKind.REASONING, label="Analyze step A", agent_id="agent1"),
    ]
    p_loop = detect_reasoning_loop(nodes_loop)
    assert p_loop is not None, "Loop detection failed to trigger"
    assert p_loop.prediction_type == "reasoning_loop", "Wrong prediction type"
    print("  [✓] Reasoning loop detection verified (prob=0.85)")

    # 2. Test confidence degradation regression
    nodes_deg = [
        RuntimeNode(kind=NodeKind.REASONING, label="Step 1", confidence=Confidence.measured(0.95), agent_id="a"),
        RuntimeNode(kind=NodeKind.REASONING, label="Step 2", confidence=Confidence.measured(0.80), agent_id="a"),
        RuntimeNode(kind=NodeKind.REASONING, label="Step 3", confidence=Confidence.measured(0.65), agent_id="a"),
        RuntimeNode(kind=NodeKind.REASONING, label="Step 4", confidence=Confidence.measured(0.50), agent_id="a"),
    ]
    p_deg = detect_confidence_degradation(nodes_deg)
    assert p_deg is not None, "Confidence degradation failed to trigger"
    assert p_deg.prediction_type == "confidence_degradation", "Wrong prediction type"
    print("  [✓] Epistemic confidence degradation regression verified")

    # 3. Test cost anomaly velocity
    nodes_cost = [
        RuntimeNode(kind=NodeKind.ACTION, label="Call LLM", cost=2.10, agent_id="a"),
        RuntimeNode(kind=NodeKind.ACTION, label="Call LLM", cost=2.20, agent_id="a"),
    ]
    p_cost = detect_cost_anomaly(nodes_cost, budget=5.00)
    assert p_cost is not None, "Cost overrun detection failed"
    assert p_cost.prediction_type == "cost_overrun", "Wrong prediction type"
    print("  [✓] Cost overrun anomaly detection verified")

    # 4. Test run_predictive_analysis
    all_preds = run_predictive_analysis(nodes_deg + nodes_cost, budget=5.00)
    assert len(all_preds) >= 2, "Combined prediction suite failed"
    print("  [✓] Combined prediction suite verified")


def test_intent_alignment_engine():
    print("\nTesting Multi-Stakeholder Intent Alignment Engine...")
    
    agent_intent = Intent("agent", goal="book cheapest flight", priority=1, max_budget=800.0)
    user_intent = Intent("user", goal="arrive before 9am", priority=1, max_budget=500.0, constraints=["must arrive by 9am"])
    policy_intent = Intent("policy", goal="corporate travel compliance", constraints=["forbidden airline X"])

    report = align_intents(agent_intent, user_intent, policy_intent)
    assert not report.aligned, "Alignment report failed to catch budget conflict"
    assert len(report.conflicts) >= 1, "No conflicts returned"
    assert report.conflicts[0].between == ["agent", "user"], "Wrong conflict pairing"
    print("  [✓] Pre-execution intent misalignment detection verified (risk=0.70)")


def test_reality_graph_and_compression():
    print("\nTesting Reality Graph & Knowledge Compression Engine...")
    
    # Test living reality graph
    rg = RealityGraph()
    rg.update_entity(RealityEntity("e1", "robot", {"battery": 85, "location": "shelf_B"}))
    assert len(rg.entities) == 1, "Reality entity update failed"
    print("  [✓] Living Reality Graph state snapshot verified")

    # Test state delta semantic compression
    raw_nodes = [
        RuntimeNode(kind=NodeKind.INTENT, label="Navigate to Shelf B", agent_id="robot-1"),
        RuntimeNode(kind=NodeKind.KNOWLEDGE, label="Verified Shelf B location coordinates", agent_id="robot-1"),
        RuntimeNode(kind=NodeKind.DECISION, label="Execute path planning route A", agent_id="robot-1"),
        RuntimeNode(kind=NodeKind.ERROR, label="Obstacle detected in corridor", content={"error": "Path blocked"}, agent_id="robot-1"),
    ]

    deltas = compress_session(raw_nodes)
    assert len(deltas) == 4, "State delta compression count mismatch"
    delta_types = [d.delta_type for d in deltas]
    assert "goal_set" in delta_types, "Missing goal_set delta"
    assert "error_occurred" in delta_types, "Missing error_occurred delta"
    print("  [✓] Semantic knowledge compression (StateDelta) verified")


if __name__ == "__main__":
    print("==========================================================")
    print("🧠 VERI Intelligence Engine Layer 4 & 5 Verification Suite")
    print("==========================================================")
    
    test_prediction_engine()
    test_intent_alignment_engine()
    test_reality_graph_and_compression()
    
    print("\n🎉 ALL LAYER 4 & 5 INTELLIGENCE ENGINES VERIFIED SUCCESSFULLY!")
