"""
Verification script for VERI Deep Intelligence Layer (Simulation, Learning, and Bayesian Engines).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "evolution-sdk-python"))

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind, EdgeKind
from veri.simulation import CounterfactualSimulator
from veri.learning import FailurePatternLearner
from veri.bayesian import BayesianEpistemicNetwork


def test_deep_intelligence_suite():
    print("Testing Deep Intelligence Layer...")

    # Node setup
    session_id = "sess_deep_01"
    agent_id = "agent-1"
    project_id = "proj-1"

    n1 = RuntimeNode(NodeKind.INTENT, "Book travel package", agent_id, session_id, project_id, id="n1")
    n2 = RuntimeNode(NodeKind.ACTION, "Search flight", agent_id, session_id, project_id, id="n2", content={"price": 1200.0})
    n3 = RuntimeNode(NodeKind.ERROR, "Budget limit exceeded error", agent_id, session_id, project_id, id="n3", content={"error": "Max price exceeded"})

    nodes = [n1, n2, n3]
    edges = [
        RuntimeEdge("n1", "n2", EdgeKind.CAUSES, session_id),
        RuntimeEdge("n2", "n3", EdgeKind.CAUSES, session_id),
    ]

    # 1. Test Counterfactual Simulator
    sim = CounterfactualSimulator()
    res = sim.simulate_ablation(nodes, edges, target_node_id="n2", substitute_value={"price": 750.0})
    assert res.recovered, "Counterfactual recovery test failed"
    assert res.recovery_probability > 0.5, "Low recovery probability"
    print(f"  [✓] Counterfactual Ablation Simulator verified (recovery_prob={res.recovery_probability:.2f})")

    # 2. Test Failure Pattern Learner & Guardrail Compilation
    learner = FailurePatternLearner()
    rule = learner.extract_failure_pattern(nodes, error_node_id="n3")
    assert rule is not None, "Failure pattern extraction failed"
    assert "@behavior_contract" in rule.generated_code, "Contract decorator code missing"
    print("  [✓] Privacy-Preserving Failure Pattern Learner verified")

    # 3. Test Bayesian Epistemic Network Engine
    bayes = BayesianEpistemicNetwork()
    posteriors = bayes.update_beliefs(nodes, edges)
    assert len(posteriors) == 3, "Bayesian update missing node probabilities"
    print(f"  [✓] Bayesian Epistemic Network Engine verified (posteriors: {len(posteriors)})")


if __name__ == "__main__":
    print("==========================================================")
    print("🧬 VERI Deep Intelligence Suite (Simulation & Learning)")
    print("==========================================================")
    
    test_deep_intelligence_suite()
    
    print("\n🎉 ALL DEEP INTELLIGENCE MODULES VERIFIED SUCCESSFULLY!")
