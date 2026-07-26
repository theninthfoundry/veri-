# 🌌 VERI. — The Intelligence Operating System (BehaviorOS v6.0)

> **The Operating System for Autonomous Intelligence. Process Management (BID), Hierarchical Memory (L1–L6), Virtual POSIX Filesystem (`/sys/behavior/...`), Cognitive Bytecode BVM, BPROTO Cognitive IPC, Intelligence Kubernetes (IK8s), Digital Organizations, and Enterprise Governance.**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI Status](https://img.shields.io/badge/CI-Passing-success.svg)]()
[![BehaviorOS](https://img.shields.io/badge/BehaviorOS-v6.0-blueviolet.svg)]()
[![TypeScript SDK](https://img.shields.io/badge/TS_SDK-v6.0.0-green.svg)](packages/evolution-sdk-ts)
[![Python SDK](https://img.shields.io/badge/Python_SDK-v6.0.0-yellow.svg)](packages/evolution-sdk-python)
[![VERI CLI](https://img.shields.io/badge/VERI_CLI-v6.0.0-orange.svg)](packages/veri-cli)

---

## 💡 The Paradigm Shift: Linux for Autonomous Systems

Traditional observability platforms (LangSmith, Braintrust, OpenTelemetry) treat AI execution as text logging and tracing for human debugging. 

**VERI operates at a fundamentally higher abstraction.** As autonomous systems evolve into digital organizations and multi-agent fleets, they require infrastructure for **intelligence itself** — an **Intelligence Operating System**.

```
              POSIX Operating System (Linux)  │  Intelligence Operating System (VERI BehaviorOS v6.0)
─────────────────────────────────────────────┼────────────────────────────────────────────────────────
Process ID                                   │  Behavior ID (BID)
CPU Core Allotment                           │  Reasoning Token & Cost Budget
RAM Allotment                                │  Context Window Allotment & L1-L6 Hierarchy
Disk / VFS                                   │  Intelligence File System (IFS) (/sys/behavior/...)
IPC (Sockets, Pipes)                         │  Behavior Protocol (BPROTO Cognitive IPC)
Bytecode VM (JVM, eBPF)                      │  Behavior Virtual Machine (BVM Cognitive Bytecode)
Package Manager (apt, npm)                   │  Behavior Package Manager (bpkg & .bcontainer)
Kubernetes Cluster                           │  Intelligence Kubernetes (IK8s Process Pods)
Organization Chart                           │  Digital Organization & Behavioral Economics
Civilization Governance                      │  Civilization Macro Engine & GDP Stability
```

---

## 🏗️ Core Subsystems of BehaviorOS v6.0

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        VERI ENTERPRISE COCKPIT DASHBOARD                               │
│        Executive Summary  │  Operations Center  │  Behavior Explorer  │  Evolution Lab │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                       CIVILIZATION & DIGITAL ORG GOVERNANCE                            │
│           Digital Organization Chart  │  Multi-Budget Bundles  │  Civilization GDP     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                        INTELLIGENCE KUBERNETES (IK8s)                                  │
│           Agent Pod Auto-Scaling  │  Goal-Based Process Migration  │  Failover         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│               BEHAVIOR CONTAINER & PACKAGE MANAGER (bpkg & .bcontainer)                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                     BEHAVIOR VIRTUAL MACHINE (BVM BYTECODE VM)                         │
│     OP_THINK │ OP_INSPECT_MEMORY │ OP_VERIFY_POLICY │ OP_EXECUTE_TOOL │ OP_REFLECT       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                   BEHAVIOR PROTOCOL (BPROTO COGNITIVE IPC)                             │
│     PROPOSE_GOAL ──► REQUEST_GOAL ──► NEGOTIATE ──► DELEGATE ──► REJECT ──► COMMIT     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│               INTELLIGENCE FILE SYSTEM (IFS VIRTUAL POSIX /sys/behavior/...)           │
│     /sys/behavior/processes/  │  /sys/behavior/goals/  │  /sys/behavior/contracts/  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                   HIERARCHICAL MEMORY MANAGER (L1–L6 MEMORY)                           │
│  L1 Working ──► L2 Session ──► L3 Org ──► L4 Behavior ──► L5 Knowledge ──► L6 Collective│
├────────────────────────────────────────────────────────────────────────────────────────┤
│                         INTELLIGENCE KERNEL (ikernel)                                  │
│     Behavior Process Table  │  Reasoning Budget Allocator  │  Thought Threads         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. ⚙️ Intelligence Kernel (`ikernel.py`)
- Manages `BehaviorProcess` (`BID`) execution life-cycles (`RUNNING`, `HALTED`, `ESCALATED`, `TERMINATED`).
- Enforces strict **Reasoning Token Budgets** and **Context Window Allotments**.
- Dispatches concurrent thought threads per process with pre-emption and execution limits.

### 2. 🧠 Hierarchical Memory Manager (`memory_manager.py`)
Provides a 6-tier memory architecture with dynamic LRU page swapping and memory cascading:
- **L1 Working Memory**: Active reasoning buffer (fastest eviction).
- **L2 Session Memory**: Single workflow context.
- **L3 Org Memory**: Shared team & organizational knowledge.
- **L4 Behavior Memory**: Operational behavioral pattern library.
- **L5 Knowledge Base**: Vector indices & static documentation.
- **L6 Collective Memory**: Global multi-organization intelligence bank.

### 3. 📂 Intelligence File System (`ifs.py`)
Virtual POSIX-compliant filesystem mounted under `/sys/behavior/...`:
- `/sys/behavior/processes/`: Live process state tree & reasoning budget descriptors.
- `/sys/behavior/goals/`: Active organizational goals and subgoals.
- `/sys/behavior/contracts/`: Active safety contracts and policy enforcement rules.
- Supports POSIX `read()`, `write()`, `stat()`, `ls()`, and `chmod()` operations on knowledge objects.

### 4. 💬 Behavior Protocol (`bproto.py`)
Structured 6-stage cognitive inter-process communication (IPC):
1. `PROPOSE_GOAL` $\rightarrow$ 2. `REQUEST_GOAL` $\rightarrow$ 3. `NEGOTIATE` $\rightarrow$ 4. `DELEGATE` $\rightarrow$ 5. `REJECT` $\rightarrow$ 6. `COMMIT`.

### 5. 🔲 Behavior Virtual Machine (`bvm.py`)
Provider-agnostic cognitive bytecode VM executing instructions independently of underlying LLM APIs:
- `OP_THINK`: Execute cognitive reasoning block.
- `OP_INSPECT_MEMORY`: Retrieve state from memory hierarchy.
- `OP_VERIFY_POLICY`: Evaluate contract constraint.
- `OP_EXECUTE_TOOL`: Invoke external API/tool.
- `OP_REFLECT`: Compute self-correction delta.

### 6. 📦 Behavior Containers & `bpkg` (`bcontainer.py`)
Portable, self-contained `.bcontainer` bundles packing Behavior Genome DNA, Contract Policies, and execution manifests. Manageable via `bpkg` package registry.

### 7. ☸️ Intelligence Kubernetes (`ik8s.py`)
Cluster orchestrator managing `AgentPod` process groups with auto-scaling based on cognitive workload spikes and failover migration.

### 8. 🏢 Digital Organization & Economics (`digi_org.py`)
Full organizational hierarchy (AI Employees, Management Reporting, Org Charts) paired with multi-budget constraints (financial USD, reasoning tokens, tool call volume).

### 9. 🌐 Civilization Engine (`civilization.py`)
Macro-governance engine measuring systemic stability, GDP economic output, and emergent agent fleet behaviors.

---

## 📦 Developer Ecosystem & SDKs

### Python SDK (`packages/evolution-sdk-python`)
```python
import veri
from veri.contracts import behavior_contract

# Initialize VERI SDK
veri.init(api_key="veri_live_key_99", cost_limit=10.0)

# Enforce Behavioral Contract
@behavior_contract(max_cost=2.50, forbidden_tools=["unapproved_transfer"])
def execute_trading_strategy(order_amount: float):
    # Instrumented session tracking
    with veri.session(session_id="sess_trade_01", agent_id="agent_alpha", project_id="finance_dept"):
        return f"Order of ${order_amount} executed cleanly"
```

### TypeScript / Node.js SDK (`packages/evolution-sdk-ts`)
```typescript
import { init, session, BehaviorContract } from "@veri-ai/sdk";

// Initialize VERI TS SDK
init({ apiKey: "veri_live_key_99", costLimit: 10.0 });

// Run session with AsyncLocalStorage context propagation
await session("sess_ts_01", "agent_beta", "web_app", async () => {
  const contract = new BehaviorContract({ maxCost: 5.0, forbiddenTools: ["drop_database"] });
  // Autonomous execution guarded by AsyncLocalStorage context...
});
```

---

## 🛠️ VERI CLI Developer Suite (`packages/veri-cli`)

Developers can manage and inspect the Intelligence OS using the `veri` command-line utility:

```bash
# List active Behavior Processes in ikernel
veri ps

# Execute Behavior Query Language (BQL) queries
veri bql "FIND workflows WHERE planning_depth > 5"

# Execute a Behavior Container in BVM
veri run finance-trader:v4.2

# Compile a session via 7-stage Compiler 2.0 pipeline
veri compile sess_prod_882

# Inspect virtual Intelligence File System
veri ifs /sys/behavior/goals

# Install a Behavior Package via bpkg
veri install finance-agent
```

---

## 🚀 Quickstart & Verification Suite

### 1. Start Infrastructure Stack
```bash
docker compose up -d
```

### 2. Launch Gateway and Backend Services
```bash
.\run_end_to_end.bat
```

### 3. Run Automated Verification Suites
- **BehaviorOS v6.0 Intelligence OS Suite**: `python verify_v6.py`
- **BehaviorOS v5.0 Platform Suite**: `python verify_v5.py`
- **BehaviorOS v4.0 Intelligence Engines**: `python verify_behavioros.py`
- **Ecosystem TS & CLI Suite**: `python verify_ecosystem.py`
- **Roadmap Verification Suite**: `python verify_roadmap.py`

---

## 📂 Project Directory Layout

```text
├── packages/
│   ├── evolution-sdk-python/   # BehaviorOS v6.0 Python SDK (ikernel, IFS, BVM, BPROTO, memory_manager)
│   ├── evolution-sdk-ts/       # @veri-ai/sdk TypeScript SDK with AsyncLocalStorage context tracking
│   └── veri-cli/               # veri command-line developer suite
├── services/
│   ├── gateway/                # Go API Gateway (OS handlers, BQL, Compiler, REST endpoints)
│   └── analyzer/               # Go background telemetry & intelligence aggregator
└── web/
    └── index.html              # Enterprise Cockpit Workspaces (Executive, Ops, Explorer, Lab)
```

---

## 📄 License
Licensed under the [Apache 2.0 License](LICENSE).
