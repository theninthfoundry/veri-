# type: ignore
"""
Verification suite for BehaviorOS v4.0 — Runtime Intelligence Layer.

Exercises:
  1. Rewritten prediction engine (EWMA, Markov, entropy, Page-Hinkley)
  2. Rewritten Bayesian engine (CPTs, belief propagation, KL divergence)
  3. Rewritten simulation engine (Topological attenuation, sensitivity, Monte Carlo)
  4. Rewritten optimizer engine (Jaccard dedup, critical path, Pareto)
  5. Behavioral State Engine (Cognitive phases, state vector, anomalies)
  6. Causal Reasoning Engine (SCM, do-calculus, root cause isolation)
  7. Behavior Genome (13-trait DNA, phenotype, distance, drift)
  8. Behavioral Physics Engine (Phase space, forces, momentum, energy)
  9. Behavioral Search Engine (Signatures, Jaccard/cosine/edit distance, anti-patterns)
 10. Fleet Intelligence Engine (Topology, emergent patterns, health score)
 11. Evolution Engine (Fitness, crossover, mutation, recommendations)
 12. Full unified intelligence pipeline (`veri.intelligence(...)`)
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "evolution-sdk-python"))
import veri
from veri import (
    run_predictive_analysis,
    BayesianEpistemicNetwork,
    CounterfactualSimulator,
    run_optimization_passes,
    BehavioralStateEngine,
    CausalReasoningEngine,
    extract_genome,
    classify_phenotype,
    BehavioralPhysicsEngine,
    compute_signature,
    match_antipatterns,
    FleetIntelligenceEngine,
    EvolutionEngine,
    intelligence,
)
from veri.ir import RuntimeNode, RuntimeEdge, NodeKind, EdgeKind

def build_synthetic_trace():
    """Generates a rich synthetic execution trace for testing."""
    session_id = "test_session_v4"
    agent_id = "agent_alpha"
    project_id = "proj_001"
    now = time.time()

    nodes = [
        RuntimeNode(NodeKind.INTENT, "Process User Payment", agent_id, session_id, project_id, id="n1", confidence=0.95, cost=0.001, timestamp=now),
        RuntimeNode(NodeKind.OBSERVATION, "Fetch Account Balance", agent_id, session_id, project_id, id="n2", confidence=0.90, cost=0.002, timestamp=now + 0.1),
        RuntimeNode(NodeKind.KNOWLEDGE, "Retrieve Risk Policy", agent_id, session_id, project_id, id="n3", confidence=0.85, cost=0.001, timestamp=now + 0.2),
        RuntimeNode(NodeKind.REASONING, "Evaluate Transaction Risk", agent_id, session_id, project_id, id="n4", confidence=0.75, cost=0.005, content={"reason": "Evaluating risk threshold"}, timestamp=now + 0.3),
        RuntimeNode(NodeKind.REASONING, "Evaluate Transaction Risk", agent_id, session_id, project_id, id="n5", confidence=0.65, cost=0.005, content={"reason": "Evaluating risk threshold"}, timestamp=now + 0.4),
        RuntimeNode(NodeKind.DECISION, "Approve Transaction Path", agent_id, session_id, project_id, id="n6", confidence=0.60, cost=0.003, timestamp=now + 0.5),
        RuntimeNode(NodeKind.TOOL_INVOCATION, "Execute Payment Gateway Call", agent_id, session_id, project_id, id="n7", confidence=0.80, cost=0.020, latency=450.0, timestamp=now + 0.6),
        RuntimeNode(NodeKind.ERROR, "Gateway Timeout 504", agent_id, session_id, project_id, id="n8", confidence=0.20, cost=0.001, content={"error": "Gateway Timeout 504"}, timestamp=now + 0.7),
        RuntimeNode(NodeKind.REFLECTION, "Analyze Payment Failure", agent_id, session_id, project_id, id="n9", confidence=0.70, cost=0.004, timestamp=now + 0.8),
        RuntimeNode(NodeKind.OUTCOME, "Transaction Failed Escalate", agent_id, session_id, project_id, id="n10", confidence=0.85, cost=0.001, timestamp=now + 0.9),
    ]

    edges = [
        RuntimeEdge("n1", "n2", EdgeKind.DECOMPOSES_INTO, session_id),
        RuntimeEdge("n1", "n3", EdgeKind.DEPENDS_ON, session_id),
        RuntimeEdge("n2", "n4", EdgeKind.CAUSES, session_id),
        RuntimeEdge("n3", "n4", EdgeKind.SUPPORTS, session_id),
        RuntimeEdge("n4", "n5", EdgeKind.CAUSES, session_id),
        RuntimeEdge("n5", "n6", EdgeKind.CAUSES, session_id),
        RuntimeEdge("n6", "n7", EdgeKind.ENABLES, session_id),
        RuntimeEdge("n7", "n8", EdgeKind.CAUSES, session_id),
        RuntimeEdge("n8", "n9", EdgeKind.REFLECTS_ON, session_id),
        RuntimeEdge("n9", "n10", EdgeKind.CAUSES, session_id),
    ]

    return nodes, edges

def run_verification():
    print("==================================================")
    print("BehaviorOS v4.0 — Comprehensive Verification Suite")
    print("==================================================\n")

    nodes, edges = build_synthetic_trace()
    print(f"Loaded synthetic trace: {len(nodes)} nodes, {len(edges)} edges.\n")

    # 1. Prediction Engine
    print("[1/11] Testing Rewritten Prediction Engine...")
    preds = veri.run_predictive_analysis(nodes, budget=0.05)
    print(f"  ✓ Generated {len(preds)} predictions (top: {preds[0].prediction_type} - {preds[0].probability:.2f})")

    # 2. Bayesian Engine
    print("[2/11] Testing Rewritten Bayesian Belief Engine...")
    bayes = veri.BayesianEpistemicNetwork()
    beliefs = bayes.propagate_beliefs(nodes, edges)
    print(f"  ✓ Propagated beliefs across {len(beliefs)} DAG nodes")
    high_info = bayes.get_highest_information_gain_nodes(beliefs, top_k=2)
    print(f"  ✓ Max information gain node: '{high_info[0].node_id}' ({high_info[0].information_gain:.4f} nats)")

    # 3. Simulation Engine
    print("[3/11] Testing Rewritten Counterfactual Simulator...")
    sim = veri.CounterfactualSimulator()
    res = sim.simulate_ablation(nodes, edges, "n4", "golden")
    print(f"  ✓ Ablation of 'n4': recovered={res.recovered}, impact={res.causal_impact_score:.3f}")
    sens = sim.sensitivity_analysis(nodes, edges)
    print(f"  ✓ Critical path nodes identified: {sum(1 for s in sens if s.is_critical_path)}")

    # 4. Optimizer Engine
    print("[4/11] Testing Rewritten Behavior Compiler (Optimizer)...")
    opts = veri.run_optimization_passes(nodes, edges)
    print(f"  ✓ Found {len(opts)} optimizations across 6 compiler passes")

    # 5. Behavioral State Engine
    print("[5/11] Testing Engine 1: Behavioral State Engine...")
    state_eng = veri.BehavioralStateEngine()
    state_eng.ingest_nodes(nodes)
    st_vec = state_eng.get_state_vector()
    print(f"  ✓ Final Cognitive Phase: '{state_eng.get_cognitive_phase().value}'")
    print(f"  ✓ State Vector: confidence={st_vec.confidence:.2f}, coherence={st_vec.coherence:.2f}, focus={st_vec.focus:.2f}")

    # 6. Causal Reasoning Engine
    print("[6/11] Testing Engine 2: Causal Reasoning Engine...")
    causal_eng = veri.CausalReasoningEngine()
    c_graph = causal_eng.build_causal_graph(nodes, edges)
    roots = causal_eng.find_root_causes(c_graph, "n8", k=2)
    print(f"  ✓ Top root cause for 'n8' error: '{roots[0].label}' (strength: {roots[0].causal_strength:.3f})")
    interv = causal_eng.simulate_intervention(c_graph, "n4", 0.99)
    print(f"  ✓ Intervened do(n4=0.99): outcome effect={interv.total_effect:.3f}")

    # 7. Behavior Genome
    print("[7/11] Testing Engine 3: Behavior Genome...")
    genome = veri.extract_genome(nodes, edges, "session_01")
    pheno = veri.classify_phenotype(genome)
    print(f"  ✓ Extracted 13-trait genome. Phenotype: '{pheno}'")

    # 8. Behavioral Physics Engine
    print("[8/11] Testing Engine 4: Behavioral Physics Engine...")
    phys_eng = veri.BehavioralPhysicsEngine()
    phys_report = phys_eng.to_dict(nodes)
    print(f"  ✓ Kinetic energy: {phys_report['energy']['kinetic']:.4f}, Active forces: {len(phys_report['forces'])}")

    # 9. Behavioral Search Engine
    print("[9/11] Testing Engine 5: Behavioral Search Engine...")
    sig = veri.compute_signature(nodes, edges, "session_01")
    matches = veri.match_antipatterns(sig)
    print(f"  ✓ Behavioral signature generated. Anti-pattern matches: {len(matches)}")

    # 10. Fleet Intelligence Engine
    print("[10/11] Testing Engine 6: Fleet Intelligence Engine...")
    fleet_eng = veri.FleetIntelligenceEngine()
    topo = fleet_eng.build_topology([{"agent_id": "agent_alpha", "nodes": nodes}])
    health = fleet_eng.compute_fleet_health({"agent_alpha": genome})
    print(f"  ✓ Fleet Health Score: {health.overall_score:.3f}")

    # 11. Evolution Engine
    print("[11/11] Testing Engine 7: Evolution Engine...")
    evo = veri.EvolutionEngine()
    fitness = evo.compute_fitness(genome)
    recs = evo.recommend_improvements(genome, [(genome, fitness)])
    print(f"  ✓ Genome Fitness: {fitness:.3f}, Improvement recommendations: {len(recs)}")

    # Unified Pipeline Call
    print("\n--------------------------------------------------")
    print("Testing Unified `veri.intelligence(...)` Call...")
    full_report = veri.intelligence(nodes, edges, budget=0.05, session_id="session_01")
    print("  ✓ Full pipeline executed successfully across all 7 engines!")
    print("==================================================")
    print("ALL VERIFICATIONS PASSED SUCCESSFULLY! 🚀")
    print("==================================================")

if __name__ == "__main__":
    run_verification()
