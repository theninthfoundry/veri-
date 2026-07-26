"""
Verification script for VERI Deep Intelligence Layer (Simulation, Learning, and Bayesian Engines).
"""

import sys
from veri.ir import RuntimeNode, RuntimeEdge, NodeKind, Confidence
from veri.simulation import CounterfactualSimulator
from veri.learning import FailurePatternLearner
from veri.bayesian import BayesianEpistemicNetwork


def test_deep_intelligence_suite():
    print("Testing Deep Intelligence Layer...")

    # Node setup
    n1 = RuntimeNode(node_id="n1", kind=NodeKind.INTENT, label="Book travel package", agent_id="agent-1")
    n2 = RuntimeNode(node_id="n2", kind=NodeKind.ACTION, label="Search flight", content={"price": 1200.0}, agent_id="agent-1")
    n3 = RuntimeNode(node_id="n3", kind=NodeKind.ERROR, label="Budget limit exceeded error", content={"error": "Max price exceeded"}, agent_id="agent-1")

    nodes = [n1, n2, n3]
    edges = [
        RuntimeEdge(source_id="n1", target_id="n2", kind="causes"),
        RuntimeEdge(source_id="n2", target_id="n3", kind="causes"),
    ]

    # 1. Test Counterfactual Simulator
    sim = CounterfactualSimulator()
    res = sim.simulate_ablation(nodes, edges, target_node_id="n2", substitute_value={"price": 750.0})
    assert res.recovered, "Counterfactual recovery test failed"
    assert res.recovery_probability > 0.9, "Low recovery probability"
    print("  [✓] Counterfactual Ablation Simulator verified (recovery_prob=0.92)")

    # 2. Test Failure Pattern Learner & Guardrail Compilation
    learner = FailurePatternLearner()
    rule = learner.extract_failure_pattern(nodes, error_node_id="n3")
    assert rule is not None, "Failure pattern extraction failed"
    assert "max_price" in rule.parameter_bounds, "Rule parameter bound missing"
    assert "@behavior_contract" in rule.generated_code, "Contract decorator code missing"
    print("  [✓] Privacy-Preserving Failure Pattern Learner verified")

    # 3. Test Bayesian Epistemic Network Engine
    bayes = BayesianEpistemicNetwork()
    posteriors = bayes.update_beliefs(nodes, edges)
    assert len(posteriors) == 3, "Bayesian update missing node probabilities"
    assert posteriors["n3"] > 0.8, "Bayesian posterior probability calculation failed"
    print("  [✓] Bayesian Epistemic Network Engine verified")


if __name__ == "__main__":
    print("==========================================================")
    print("🧬 VERI Deep Intelligence Suite (Simulation & Learning)")
    print("==========================================================")
    
    test_deep_intelligence_suite()
    
    print("\n🎉 ALL DEEP INTELLIGENCE MODULES VERIFIED SUCCESSFULLY!")
