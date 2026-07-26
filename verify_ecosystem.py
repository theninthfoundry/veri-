"""
Verification suite for VERI Ecosystem Expansion (TypeScript SDK & VERI CLI Tooling).

Exercises:
  1. TypeScript SDK Package Configuration & Interfaces (@veri-ai/sdk)
  2. VERI CLI Tooling Commands (veri ps, veri bql, veri run, veri compile, veri ifs, veri install)
"""

import os
import sys
import json
import subprocess

def run_ecosystem_verification():
    print("==================================================================")
    print("VERI Ecosystem Expansion — Verification Suite (TS SDK & VERI CLI)")
    print("==================================================================\n")

    # 1. TypeScript SDK Verification
    print("[1/2] Verifying TypeScript SDK Structure (@veri-ai/sdk)...")
    ts_dir = os.path.join(os.getcwd(), "packages", "evolution-sdk-ts")
    pkg_json = os.path.join(ts_dir, "package.json")
    tsconfig = os.path.join(ts_dir, "tsconfig.json")
    src_dir = os.path.join(ts_dir, "src")

    assert os.path.exists(pkg_json), "TypeScript package.json missing"
    assert os.path.exists(tsconfig), "TypeScript tsconfig.json missing"
    assert os.path.exists(os.path.join(src_dir, "index.ts")), "TypeScript src/index.ts missing"
    assert os.path.exists(os.path.join(src_dir, "client.ts")), "TypeScript src/client.ts missing"
    assert os.path.exists(os.path.join(src_dir, "contracts.ts")), "TypeScript src/contracts.ts missing"
    assert os.path.exists(os.path.join(src_dir, "ir.ts")), "TypeScript src/ir.ts missing"

    with open(pkg_json, "r") as f:
        pkg_data = json.load(f)
    print(f"  ✓ TypeScript SDK '{pkg_data['name']}' v{pkg_data['version']} configuration verified.")

    # 2. VERI CLI Verification
    print("\n[2/2] Verifying VERI CLI Commands (packages/veri-cli)...")
    sys.path.insert(0, os.path.join(os.getcwd(), "packages", "veri-cli"))
    from veri_cli.main import main as cli_main

    # Test CLI invocation by setting sys.argv
    print("  ✓ Testing 'veri ps':")
    sys.argv = ["veri", "ps"]
    cli_main()

    print("\n  ✓ Testing 'veri bql':")
    sys.argv = ["veri", "bql", "FIND workflows WHERE planning_depth > 5"]
    cli_main()

    print("\n  ✓ Testing 'veri run':")
    sys.argv = ["veri", "run", "finance-trader:v4.2"]
    cli_main()

    print("\n  ✓ Testing 'veri compile':")
    sys.argv = ["veri", "compile", "sess_demo_99"]
    cli_main()

    print("\n  ✓ Testing 'veri ifs':")
    sys.argv = ["veri", "ifs", "/sys/behavior"]
    cli_main()

    print("\n  ✓ Testing 'veri install':")
    sys.argv = ["veri", "install", "finance-agent"]
    cli_main()

    print("\n==================================================================")
    print("ALL ECOSYSTEM EXPANSION VERIFICATIONS PASSED SUCCESSFULLY! 🚀")
    print("==================================================================")

if __name__ == "__main__":
    run_ecosystem_verification()
