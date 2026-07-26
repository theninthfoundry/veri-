# type: ignore
"""
Verification script for VERI Multi-Pass Runtime Optimization Compiler.
Tests Redundant Reasoning, Unnecessary Retrieval, Serial-Parallelizable, and Dead Branch passes.
"""


import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "evolution-sdk-python"))

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind, EdgeKind
from veri.optimizer import (
    Optimization,
    RedundantReasoningPass,
    UnnecessaryRetrievalPass,
    SerialParallelizablePass,
    DeadBranchPass,
    run_optimization_passes,
)


def test_optimization_compiler():
    print("Testing Multi-Pass Runtime Optimization Compiler...")

    session_id = "sess_opt_01"
    agent_id = "agent-1"
    project_id = "proj-1"

    # Node setup
    n1 = RuntimeNode(NodeKind.INTENT, "Process order", agent_id, session_id, project_id, id="n1")
    n2 = RuntimeNode(NodeKind.KNOWLEDGE, "Fetch user profile", agent_id, session_id, project_id, id="n2", cost=0.002, latency=180.0)
    n3 = RuntimeNode(NodeKind.REASONING, "Determine discount rate", agent_id, session_id, project_id, id="n3", cost=0.003, latency=300.0)
    n4 = RuntimeNode(NodeKind.REASONING, "Determine discount rate", agent_id, session_id, project_id, id="n4", cost=0.003, latency=300.0) # Redundant
    n5 = RuntimeNode(NodeKind.TOOL_INVOCATION, "Call Payment API", agent_id, session_id, project_id, id="n5", latency=250.0)
    n6 = RuntimeNode(NodeKind.TOOL_INVOCATION, "Call Shipping API", agent_id, session_id, project_id, id="n6", latency=200.0) # Parallelizable
    n7 = RuntimeNode(NodeKind.ERROR, "Database connection timeout", agent_id, session_id, project_id, id="n7", cost=0.004, latency=500.0) # Dead branch

    nodes = [n1, n2, n3, n4, n5, n6, n7]
    edges = [
        RuntimeEdge("n1", "n3", EdgeKind.CAUSES, session_id),
        RuntimeEdge("n3", "n4", EdgeKind.CAUSES, session_id),
        RuntimeEdge("n4", "n5", EdgeKind.CAUSES, session_id),
    ]

    # 1. Test Redundant Reasoning Pass
    r_opts = RedundantReasoningPass().analyze(nodes, edges)
    assert len(r_opts) == 1, "Redundant reasoning pass failed to trigger"
    assert r_opts[0].optimization_type == "redundant_reasoning", "Wrong opt type"
    print("  [✓] Redundant Reasoning Elimination pass verified")

    # 2. Test Unnecessary Retrieval Pass
    u_opts = UnnecessaryRetrievalPass().analyze(nodes, edges)
    assert len(u_opts) == 1, "Unnecessary retrieval pass failed to trigger"
    assert u_opts[0].affected_nodes == ["n2"], "Wrong affected node"
    print("  [✓] Unnecessary Retrieval Pruning pass verified")

    # 3. Test Serial Parallelizable Pass
    p_opts = SerialParallelizablePass().analyze(nodes, edges)
    assert len(p_opts) == 1, "Serial parallelizable pass failed to trigger"
    assert p_opts[0].optimization_type == "serial_parallelizable", "Wrong opt type"
    print("  [✓] Serial-to-Parallel Transformation pass verified")

    # 4. Test Dead Branch Pass
    d_opts = DeadBranchPass().analyze(nodes, edges)
    assert len(d_opts) == 1, "Dead branch pass failed to trigger"
    assert d_opts[0].affected_nodes == ["n7"], "Wrong affected node"
    print("  [✓] Dead Branch Elimination pass verified")

    # 5. Full Optimization Pipeline
    all_opts = run_optimization_passes(nodes, edges)
    assert len(all_opts) >= 4, "Full pass suite failed"
    print(f"  [✓] Full Multi-Pass Optimization Suite verified ({len(all_opts)} optimizations generated)")


if __name__ == "__main__":
    print("==========================================================")
    print("⚡ VERI Optimization Compiler Pass Verification")
    print("==========================================================")
    
    test_optimization_compiler()
    
    print("\n🎉 ALL OPTIMIZATION COMPILER PASSES VERIFIED SUCCESSFULLY!")
