"""
Verification script for VERI Multi-Pass Runtime Optimization Compiler.
Tests Redundant Reasoning, Unnecessary Retrieval, Serial-Parallelizable, and Dead Branch passes.
"""

import sys
from veri.ir import RuntimeNode, RuntimeEdge, NodeKind
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

    # Node setup
    n1 = RuntimeNode(node_id="n1", kind=NodeKind.INTENT, label="Process order", agent_id="agent-1")
    n2 = RuntimeNode(node_id="n2", kind=NodeKind.KNOWLEDGE, label="Fetch user profile", cost=0.002, latency=180.0, agent_id="agent-1")
    n3 = RuntimeNode(node_id="n3", kind=NodeKind.REASONING, label="Determine discount rate", cost=0.003, latency=300.0, agent_id="agent-1")
    n4 = RuntimeNode(node_id="n4", kind=NodeKind.REASONING, label="Determine discount rate", cost=0.003, latency=300.0, agent_id="agent-1") # Redundant
    n5 = RuntimeNode(node_id="n5", kind=NodeKind.TOOL_INVOCATION, label="Call Payment API", latency=250.0, agent_id="agent-1")
    n6 = RuntimeNode(node_id="n6", kind=NodeKind.TOOL_INVOCATION, label="Call Shipping API", latency=200.0, agent_id="agent-1") # Parallelizable
    n7 = RuntimeNode(node_id="n7", kind=NodeKind.ERROR, label="Database connection timeout", cost=0.004, latency=500.0, agent_id="agent-1") # Dead branch

    nodes = [n1, n2, n3, n4, n5, n6, n7]
    edges = [
        RuntimeEdge(source_id="n1", target_id="n3", kind="causes"),
        RuntimeEdge(source_id="n3", target_id="n4", kind="causes"),
        RuntimeEdge(source_id="n4", target_id="n5", kind="causes"),
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

    # 5. Test Combined Execution
    all_opts = run_optimization_passes(nodes, edges)
    assert len(all_opts) == 4, f"Combined passes returned {len(all_opts)} optimizations (expected 4)"
    
    total_cost_saved = sum(o.cost_reduction for o in all_opts)
    total_latency_saved = sum(o.latency_reduction for o in all_opts)
    print(f"  [✓] Combined Optimization Compiler Suite verified (Savings: ${total_cost_saved:.4f}, {total_latency_saved:.0f}ms)")


if __name__ == "__main__":
    print("==========================================================")
    print("⚡ VERI Multi-Pass Optimization Compiler Verification Suite")
    print("==========================================================")
    
    test_optimization_compiler()
    
    print("\n🎉 ALL MULTI-PASS OPTIMIZATION COMPILER PASSES VERIFIED!")
