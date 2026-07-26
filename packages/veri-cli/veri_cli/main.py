"""
VERI CLI Developer Tooling — BehaviorOS v6.0

Command-Line Interface (CLI) for developers and operators:
  - veri ps                      ──► List active Behavior Processes
  - veri bql "<query>"           ──► Execute BQL query against Behavioral Database
  - veri run <container>         ──► Execute Behavior Container in BVM
  - veri compile <session_id>    ──► Run 7-stage Compiler 2.0 pipeline
  - veri ifs <path>              ──► Inspect Intelligence File System (/sys/behavior/...)
  - veri install <package>       ──► Install Behavior Package via bpkg
"""

import sys
import json
import argparse
from typing import List, Dict, Any

from veri.ikernel import IntelligenceKernel
from veri.behavior_db import BehavioralDatabase
from veri.ifs import IntelligenceFileSystem
from veri.compiler_v2 import BehaviorCompilerV2
from veri.bvm import BehaviorVirtualMachine, BVMInstruction, BVMOpcode
from veri.bcontainer import BehaviorContainer, BehaviorPackageManager
from veri.contracts import BehaviorContract
from veri.genome import BehaviorGenome


def main():
    parser = argparse.ArgumentParser(
        prog="veri",
        description="VERI Intelligence Operating System CLI Tool",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available VERI commands")

    # 1. veri ps
    ps_parser = subparsers.add_parser("ps", help="List active Behavior Processes (ikernel)")

    # 2. veri bql
    bql_parser = subparsers.add_parser("bql", help="Execute Behavior Query Language (BQL) query")
    bql_parser.add_argument("query", type=str, help="BQL query string (e.g. 'FIND workflows WHERE...')")

    # 3. veri run
    run_parser = subparsers.add_parser("run", help="Execute a Behavior Container in BVM")
    run_parser.add_argument("container", type=str, help="Container package key (e.g. 'finance-trader:v4.2')")

    # 4. veri compile
    compile_parser = subparsers.add_parser("compile", help="Run 7-stage Compiler 2.0 pipeline")
    compile_parser.add_argument("session_id", type=str, help="Target session ID")

    # 5. veri ifs
    ifs_parser = subparsers.add_parser("ifs", help="Inspect virtual Intelligence File System")
    ifs_parser.add_argument("path", type=str, nargs="?", default="/sys/behavior", help="Virtual path (default: /sys/behavior)")

    # 6. veri install
    install_parser = subparsers.add_parser("install", help="Install a Behavior Package via bpkg")
    install_parser.add_argument("package", type=str, help="Package name (e.g. 'finance-agent')")

    args = parser.parse_args()

    if args.command == "ps":
        kernel = IntelligenceKernel()
        kernel.create_process("agent_alpha", "Execute High-Frequency Trade")
        kernel.create_process("agent_beta", "Verify Audit Compliance")
        print(json.dumps(kernel.list_processes(), indent=2))

    elif args.command == "bql":
        db = BehavioralDatabase()
        res = db.execute_bql(args.query)
        print(json.dumps(res.to_dict(), indent=2))

    elif args.command == "run":
        bvm = BehaviorVirtualMachine()
        instructions = [
            BVMInstruction(BVMOpcode.OP_INSPECT_MEMORY, {"key": "context"}),
            BVMInstruction(BVMOpcode.OP_VERIFY_POLICY, {"rule": "max_cost"}),
            BVMInstruction(BVMOpcode.OP_EXECUTE_TOOL, {"tool": "order_book_api"}),
            BVMInstruction(BVMOpcode.OP_HALT, {}),
        ]
        res = bvm.execute_program(f"run_{args.container}", instructions)
        print(json.dumps(res.to_dict(), indent=2))

    elif args.command == "compile":
        compiler = BehaviorCompilerV2()
        artifact = compiler.compile(args.session_id, [], [])
        print(json.dumps(artifact.to_dict(), indent=2))

    elif args.command == "ifs":
        ifs = IntelligenceFileSystem()
        ifs.write("/sys/behavior/goals/g_101", "Achieve 5% Arbitrage Yield", object_type="goal")
        ifs.write("/sys/behavior/decisions/d_202", "Approved Payment #8812", object_type="decision")
        res = ifs.ls(args.path)
        print(json.dumps(res, indent=2))

    elif args.command == "install":
        pkg_mgr = BehaviorPackageManager()
        genome = BehaviorGenome({"decisiveness": 0.85, "cost_efficiency": 0.90})
        contract = BehaviorContract(max_cost=10.0)
        container = BehaviorContainer(args.package, "v4.2", f"Installed package {args.package}", genome, contract, ["trading"])
        key = pkg_mgr.install(container)
        print(json.dumps({"installed_package": key, "status": "SUCCESS"}, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
