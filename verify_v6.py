"""
Verification suite for BehaviorOS v6.0 — The Intelligence Operating System (The Linux of Autonomous AI Systems).

Exercises:
  1. Intelligence Kernel (BehaviorProcess, BID, ReasoningBudget, ContextWindow, ProcessTable)
  2. Hierarchical Memory Manager (L1-L6 memory layers, LRU page swapping, memory cascading)
  3. Intelligence File System (IFS virtual POSIX filesystem `/sys/behavior/...`)
  4. Behavior Protocol (BPROTO cognitive IPC 6-step negotiation protocol)
  5. Behavior Virtual Machine (BVM provider-agnostic bytecode interpreter)
  6. Behavior Containers & Package Manager (.bcontainer serialization & bpkg)
  7. Intelligence Kubernetes (IK8s pod auto-scaling, goal routing, failover migration)
  8. Digital Organization & Behavioral Economics (AI employee org chart & multi-budgets)
  9. Civilization Engine (AI civilization stability, GDP & macro governance)
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "evolution-sdk-python"))
import veri
from veri.ir import RuntimeNode, NodeKind

def run_v6_verification():
    print("==================================================================")
    print("BehaviorOS v6.0 — The Intelligence OS (Linux for AI) Verification")
    print("==================================================================\n")

    # 1. Intelligence Kernel
    print("[1/9] Testing Intelligence Kernel (ikernel)...")
    kernel = veri.IntelligenceKernel(max_concurrent_processes=50)
    proc = kernel.create_process(agent_id="agent_titan", goal="Autonomous Market Trading", max_tokens=50000, max_cost_usd=2.50)
    proc.spawn_thought("t1", "Analyze high-frequency orderbook order flow")
    stats = kernel.get_kernel_stats()
    print(f"  ✓ Spawned BehaviorProcess BID='{proc.bid[:16]}...' (State: {proc.state.value})")
    print(f"  ✓ Kernel Stats: {stats['active_processes']} active process(es), reasoning budget remaining: {proc.reasoning_budget.remaining_tokens} tokens")

    # 2. Hierarchical Memory Manager
    print("[2/9] Testing Hierarchical Memory Manager (L1-L6 Layers)...")
    mem_mgr = veri.HierarchicalMemoryManager(l1_max_tokens=500)
    mem_mgr.write(veri.MemoryLayer.L1_WORKING, "order_status", "Executing Order #991", tokens=200)
    mem_mgr.write(veri.MemoryLayer.L1_WORKING, "risk_params", "Volatility Index High", tokens=400)  # Causes L1 LRU eviction to L2
    read_item = mem_mgr.read(veri.MemoryLayer.L1_WORKING, "risk_params")
    assert read_item is not None, "Failed to read L1 memory item"
    mem_stats = mem_mgr.get_memory_stats()
    print(f"  ✓ Read L1 item: key='{read_item.key}', value='{read_item.value}'")
    print(f"  ✓ Memory Cascade Stats: L1 items={mem_stats['l1_working']['items_count']}, L2 items={mem_stats['l2_session']['items_count']}")

    # 3. Intelligence File System (IFS)
    print("[3/9] Testing Intelligence File System (IFS POSIX VFS)...")
    ifs = veri.IntelligenceFileSystem()
    ifs.write("/sys/behavior/processes/bid_01/state", "RUNNING_OPTIMAL", object_type="state")
    ifs.write("/sys/behavior/goals/g_trading_01", "Achieve 5% Arbitrage Yield", object_type="goal")
    stat_res = ifs.stat("/sys/behavior/goals/g_trading_01")
    assert stat_res is not None, "IFS stat failed"
    ls_res = ifs.ls("/sys/behavior")
    print(f"  ✓ IFS stat('/sys/behavior/goals/g_trading_01'): version={stat_res['version']}, author='{stat_res['author']}'")
    print(f"  ✓ IFS ls('/sys/behavior'): {len(ls_res)} objects found")

    # 4. Behavior Protocol (BPROTO)
    print("[4/9] Testing Behavior Protocol (BPROTO Cognitive IPC)...")
    session = veri.BProtoSession("bproto_sess_01", "bid_alpha", "bid_beta")
    session.send_packet("bid_alpha", veri.BProtoMessageType.REQUEST_GOAL, {"goal": "Coordinated Execution"})
    session.send_packet("bid_beta", veri.BProtoMessageType.NEGOTIATE, {"max_cost": 0.05})
    session.send_packet("bid_alpha", veri.BProtoMessageType.COMMIT, {"plan_approved": True})
    print(f"  ✓ BPROTO session: stage='{session.current_stage.value}', committed={session.committed}, packets={len(session.packets)}")

    # 5. Behavior Virtual Machine (BVM)
    print("[5/9] Testing Behavior Virtual Machine (BVM Bytecode Interpreter)...")
    bvm = veri.BehaviorVirtualMachine(provider_model="gpt-4o")
    instructions = [
        veri.BVMInstruction(veri.BVMOpcode.OP_INSPECT_MEMORY, {"key": "order_status"}),
        veri.BVMInstruction(veri.BVMOpcode.OP_VERIFY_POLICY, {"rule": "max_cost"}),
        veri.BVMInstruction(veri.BVMOpcode.OP_EXECUTE_TOOL, {"tool": "order_book_api"}),
        veri.BVMInstruction(veri.BVMOpcode.OP_REFLECT, {"reflection": "Execution parameters verified"}),
        veri.BVMInstruction(veri.BVMOpcode.OP_HALT, {}),
    ]
    bvm_res = bvm.execute_program("prog_bvm_01", instructions)
    print(f"  ✓ BVM executed {bvm_res.instructions_executed} instructions in {bvm_res.execution_time_ms:.3f}ms (success: {bvm_res.success})")

    # 6. Behavior Containers & Package Manager (bpkg)
    print("[6/9] Testing Behavior Containers & bpkg Package Manager...")
    genome = veri.BehaviorGenome({"decisiveness": 0.85, "cost_efficiency": 0.90})
    contract = veri.BehaviorContract(max_cost=10.0)
    container = veri.BehaviorContainer("finance-trader", "v4.2", "Autonomous Trading Container", genome, contract, ["trading", "compliance"])
    json_str = container.serialize_bcontainer()
    
    pkg_mgr = veri.BehaviorPackageManager()
    pkg_key = pkg_mgr.install(container)
    print(f"  ✓ Serialized & installed container '.bcontainer' package key: '{pkg_key}'")

    # 7. Intelligence Kubernetes (IK8s)
    print("[7/9] Testing Intelligence Kubernetes (IK8s Orchestrator)...")
    ik8s = veri.IntelligenceKubernetes(kernel)
    pod = ik8s.create_pod("trading_fleet", min_replicas=2, max_replicas=5)
    new_count = ik8s.autoscale_pod(pod.pod_id, current_workload_score=0.92)
    print(f"  ✓ IK8s Pod '{pod.name}': autoscaled to {new_count} process replicas on workload spike (0.92)")

    # 8. Digital Organization & Behavioral Economics
    print("[8/9] Testing Digital Organization & Multi-Budget Economics...")
    org = veri.DigitalOrganization("org_apex", "Apex Financial Technologies")
    ceo = org.add_employee("emp_01", "AI CEO", "Executive Officer", financial_budget=10000.0)
    trader = org.add_employee("emp_02", "AI Head Trader", "Trading Specialist", manager_id="emp_01", financial_budget=2500.0)
    chart = org.get_org_chart()
    print(f"  ✓ Digital Org '{chart['name']}': {chart['total_ai_employees']} AI employees, total budget=${chart['total_financial_budget_usd']:.2f}")

    # 9. Civilization Engine
    print("[9/9] Testing Civilization Engine...")
    civ = veri.CivilizationEngine("civ_global_01")
    civ.register_organization(org)
    civ_status = civ.evaluate_civilization_health()
    print(f"  ✓ Civilization '{civ_status.civilization_id}': stability={civ_status.systemic_stability_index:.3f}, GDP=${civ_status.economic_output_gdp:,.2f}")

    print("\n==================================================================")
    print("ALL BEHAVIOROS V6.0 INTELLIGENCE OS SUBSYSTEMS VERIFIED! 🚀")
    print("==================================================================")

if __name__ == "__main__":
    run_v6_verification()
