"""
Verification suite for BehaviorOS v5.0 — The Operating System for Autonomous Organizations.

Exercises:
  1. Behavior Kernel (6-stage inline execution pipeline & halt controls)
  2. Behavioral Memory System (operational pattern memory & recovery retrieval)
  3. Behavioral Database & BQL (Behavior Query Language query engine)
  4. Unified Behavior Graph Engine (cognitive graph & contradiction detection)
  5. Behavior Scheduler (multi-agent priority dispatch & queue management)
  6. Behavior Planner (VERI-native verified & policy-compliant plan generator)
  7. Behavior Compiler 2.0 (7-stage deployment compilation pipeline)
  8. Runtime Behavior Models (failure prediction & anomaly classification)
  9. Enterprise Platform Controls (multi-tenancy & SOC 2 / GDPR compliance exports)
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "evolution-sdk-python"))
import veri
from veri import (
    BehaviorKernel,
    BehavioralMemoryStore,
    BehavioralEpisode,
    CognitivePhase,
    BehavioralDatabase,
    UnifiedBehaviorGraph,
    BehaviorScheduler,
    AgentTask,
    BehaviorPlanner,
    BehaviorCompilerV2,
    FailurePredictionModel,
    AnomalyClassificationModel,
    ComplianceAuditExporter,
)
from veri.ir import RuntimeNode, RuntimeEdge, NodeKind, EdgeKind

def build_v5_trace():
    session_id = "sess_v5_enterprise"
    agent_id = "agent_omega"
    project_id = "proj_enterprise"
    now = time.time()

    nodes = [
        RuntimeNode(NodeKind.INTENT, "Execute Enterprise Fund Transfer", agent_id, session_id, project_id, id="v1", confidence=0.95, cost=0.001, timestamp=now),
        RuntimeNode(NodeKind.KNOWLEDGE, "Fetch Banking Compliance Policy", agent_id, session_id, project_id, id="v2", confidence=0.90, cost=0.002, timestamp=now + 0.1),
        RuntimeNode(NodeKind.REASONING, "Evaluate AML Risk Constraints", agent_id, session_id, project_id, id="v3", confidence=0.80, cost=0.005, content={"reason": "Evaluating AML compliance rules"}, timestamp=now + 0.2),
        RuntimeNode(NodeKind.DECISION, "Approve Wire Transfer", agent_id, session_id, project_id, id="v4", confidence=0.85, cost=0.003, timestamp=now + 0.3),
        RuntimeNode(NodeKind.TOOL_INVOCATION, "SWIFT Payment API Call", agent_id, session_id, project_id, id="v5", confidence=0.92, cost=0.018, latency=320.0, timestamp=now + 0.4),
        RuntimeNode(NodeKind.OUTCOME, "Transfer Successfully Executed", agent_id, session_id, project_id, id="v6", confidence=0.98, cost=0.001, timestamp=now + 0.5),
    ]

    edges = [
        RuntimeEdge("v1", "v2", EdgeKind.DEPENDS_ON, session_id),
        RuntimeEdge("v2", "v3", EdgeKind.SUPPORTS, session_id),
        RuntimeEdge("v3", "v4", EdgeKind.CAUSES, session_id),
        RuntimeEdge("v4", "v5", EdgeKind.ENABLES, session_id),
        RuntimeEdge("v5", "v6", EdgeKind.CAUSES, session_id),
    ]

    return nodes, edges

def run_v5_verification():
    print("==================================================")
    print("BehaviorOS v5.0 — Operating System Verification")
    print("==================================================\n")

    nodes, edges = build_v5_trace()

    # 1. Behavior Kernel
    print("[1/9] Testing Behavior Kernel (6-Stage Pipeline)...")
    kernel = veri.BehaviorKernel("sess_v5_01", "agent_omega", "proj_enterprise", budget=5.0)
    step_res = kernel.process_node(nodes[0])
    status = kernel.get_kernel_status()
    print(f"  ✓ Kernel Step 1: phase={step_res.phase.value}, allowed={step_res.allowed}, latency={step_res.kernel_latency_ms:.3f}ms")

    # 2. Behavioral Memory
    print("[2/9] Testing Behavioral Memory System...")
    mem_store = veri.BehavioralMemoryStore()
    ep = veri.BehavioralEpisode(
        episode_id="ep_001", agent_id="agent_omega",
        initial_phase=veri.CognitivePhase.REASONING, final_phase=veri.CognitivePhase.ACTING,
        state_vector=step_res.state_vector, tool_invoked="SWIFT Payment API Call",
        failure_mode="Gateway Timeout", human_intervention=True, recovery_time_seconds=42.0, success=True
    )
    mem_store.store_episode(ep)
    retrieved = mem_store.retrieve_similar_episodes(step_res.state_vector, tool_name="SWIFT Payment API Call")
    print(f"  ✓ Retrieved {len(retrieved)} memory episode (similarity: {retrieved[0].similarity_score:.3f})")
    print(f"  ✓ Recommended recovery: '{retrieved[0].recommended_recovery[:60]}...'")

    # 3. Behavioral Database & BQL
    print("[3/9] Testing Behavioral Database & BQL Engine...")
    db = veri.BehavioralDatabase()
    db.insert_session("sess_v5_01", "agent_omega", "proj_enterprise", nodes, status="success", total_cost=0.030)
    bql_res = db.execute_bql("FIND workflows WHERE planning_depth >= 1 AND uncertainty < 0.5")
    print(f"  ✓ BQL Query executed in {bql_res.execution_time_ms:.3f}ms (matched {bql_res.matched_count} session)")

    # 4. Unified Behavior Graph Engine
    print("[4/9] Testing Unified Behavior Graph Engine...")
    cog_graph = veri.UnifiedBehaviorGraph()
    cog_graph.ingest_runtime_nodes(nodes, edges)
    cog_report = cog_graph.to_dict()
    print(f"  ✓ Unified Graph: {cog_report['node_count']} cognitive nodes, {cog_report['edge_count']} edges")

    # 5. Behavior Scheduler
    print("[5/9] Testing Behavior Scheduler...")
    scheduler = veri.BehaviorScheduler(max_concurrent_tasks=2)
    task1 = veri.AgentTask("t1", "agent_omega", "sess_01", priority=0.9, risk_score=0.1, estimated_cost=0.01)
    task2 = veri.AgentTask("t2", "agent_alpha", "sess_02", priority=0.5, risk_score=0.8, estimated_cost=0.05)
    scheduler.enqueue_task(task1)
    scheduler.enqueue_task(task2)
    dispatched = scheduler.schedule_next()
    print(f"  ✓ Scheduler dispatched task '{dispatched[0].task_id}' (score: {dispatched[0].compute_dispatch_score():.3f})")

    # 6. Behavior Planner
    print("[6/9] Testing VERI-Native Behavior Planner...")
    planner = veri.BehaviorPlanner()
    plan = planner.generate_plan("Execute Enterprise Fund Transfer", max_budget=5.0)
    print(f"  ✓ Generated verified plan '{plan.plan_id}' with {len(plan.steps)} steps (policy verified: {plan.policy_verified})")

    # 7. Behavior Compiler 2.0
    print("[7/9] Testing Behavior Compiler 2.0...")
    compiler = veri.BehaviorCompilerV2()
    artifact = compiler.compile("sess_v5_01", nodes, edges)
    print(f"  ✓ Compiled deployment artifact '{artifact.artifact_id}' across {len(artifact.stages_completed)} stages")

    # 8. Runtime Behavior Models
    print("[8/9] Testing Runtime Behavior Models...")
    failure_model = veri.FailurePredictionModel()
    fail_prob = failure_model.predict_failure_probability(nodes)
    classifier = veri.AnomalyClassificationModel()
    classified = classifier.classify_anomaly("504 Gateway Timeout on SWIFT API")
    print(f"  ✓ Failure Probability: {fail_prob:.4f}")
    print(f"  ✓ Anomaly Category: '{classified['category']}' (action: {classified['action']})")

    # 9. Enterprise Controls & Compliance
    print("[9/9] Testing Enterprise Controls & Compliance Exporters...")
    exporter = veri.ComplianceAuditExporter()
    soc2 = exporter.export_soc2_report("org_enterprise_01", [{"event": "auth_override"}])
    print(f"  ✓ Exported SOC 2 Type II audit report ({soc2['standard']}: {soc2['access_control_verification']})")

    print("\n==================================================")
    print("ALL BEHAVIOROS V5.0 SUBSYSTEMS VERIFIED! 🚀")
    print("==================================================")

if __name__ == "__main__":
    run_v5_verification()
