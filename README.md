# 🌌 VERI — The Intelligence Operating System (BehaviorOS v6.0)

> **The Universal Operating System for Autonomous Intelligence. Process Management (BID), Hierarchical Memory (L1–L6), Virtual POSIX Filesystem (`/sys/behavior/...`), Cognitive Bytecode BVM, BPROTO Cognitive IPC, Intelligence Kubernetes (IK8s), Digital Organizations, and Enterprise Governance.**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI Status](https://img.shields.io/badge/CI-Passing-success.svg)]()
[![BehaviorOS](https://img.shields.io/badge/BehaviorOS-v6.0-blueviolet.svg)]()
[![TypeScript SDK](https://img.shields.io/badge/TS_SDK-v6.0.0-green.svg)](packages/evolution-sdk-ts)
[![Python SDK](https://img.shields.io/badge/Python_SDK-v6.0.0-yellow.svg)](packages/evolution-sdk-python)
[![VERI CLI](https://img.shields.io/badge/VERI_CLI-v6.0.0-orange.svg)](packages/veri-cli)
[![Runtime IR](https://img.shields.io/badge/Runtime_IR-v6.0.0-red.svg)](packages/runtime-ir)

---

## 💡 The Paradigm Shift: Operating System vs. Passive Observability

Traditional observability platforms (LangSmith, Braintrust, OpenTelemetry) treat AI execution as text logging and tracing for human debugging. They answer *"What text did the model return?"* long after execution has finished.

**VERI operates at a fundamentally higher abstraction.** As autonomous systems evolve into digital organizations and multi-agent fleets, they require infrastructure for **intelligence itself** — an **Intelligence Operating System** that governs execution, enforces safety contracts, allocates token/cost budgets, manages hierarchical memory, and orchestrates agent processes in real time.

```
┌──────────────────────────────────────────────┬────────────────────────────────────────────────────────┐
│ POSIX Operating System (Linux / Unix)        │ Intelligence Operating System (VERI BehaviorOS v6.0)  │
├──────────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ Process ID (PID)                             │ Behavior Process ID (BID)                              │
│ CPU Core & Time Allotment                    │ Reasoning Token & Financial Cost Budget                │
│ RAM Allotment & Page Eviction                │ Context Window Allotment & L1–L6 Memory Hierarchy      │
│ Virtual File System (VFS / proc / sys)       │ Intelligence File System (IFS) (`/sys/behavior/...`)   │
│ Inter-Process Communication (IPC / Sockets)  │ Behavior Protocol (BPROTO Cognitive IPC)               │
│ Virtual Machine / Bytecode (JVM / eBPF)      │ Behavior Virtual Machine (BVM Cognitive Bytecode)      │
│ Package Manager (apt / npm)                  │ Behavior Package Manager (`bpkg` & `.bcontainer`)      │
│ Container Orchestrator (Kubernetes / K8s)    │ Intelligence Kubernetes (IK8s Agent Pods)              │
│ Corporate Org Chart                          │ Digital Organization & Multi-Budget Governance         │
│ Macro Economy & Fiscal Policy                │ Civilization Macro Engine & GDP Stability              │
└──────────────────────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Topology & Core Subsystems

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
- Manages `BehaviorProcess` (`BID`) execution life-cycles across four explicit process states: `RUNNING`, `HALTED`, `ESCALATED`, and `TERMINATED`.
- Enforces strict multi-dimensional resource bounds (**Reasoning Token Budgets**, **USD Cost Caps**, **Execution Depth Limits**).
- Dispatches concurrent **thought threads** per process with pre-emptive scheduling and priority queue management.

### 2. 🧠 Hierarchical Memory Manager (`memory_manager.py`)
A 6-tier memory architecture with dynamic LRU page swapping and cross-tier cascading:

| Memory Tier | Name | Scope & Function | Eviction Strategy |
|---|---|---|---|
| **L1** | Working Memory | Active reasoning buffer & instantaneous thought state | Fast LRU Eviction |
| **L2** | Session Memory | Single execution workflow / task context | Workflow Termination |
| **L3** | Org Memory | Shared team, department & enterprise context | Frequency / TTL |
| **L4** | Behavior Memory | Operational behavioral patterns & learned execution paths | Pattern Utility Score |
| **L5** | Knowledge Base | Static domain knowledge & vector embeddings | Explicit Update |
| **L6** | Collective Memory | Cross-system multi-organization intelligence bank | Global System Sync |

### 3. 📂 Intelligence File System (`ifs.py`)
A POSIX-compliant virtual file system mounted under `/sys/behavior/...`:
- `/sys/behavior/processes/`: Live process state tree, budget descriptors, and execution statistics.
- `/sys/behavior/goals/`: Active organizational goals, subgoals, progress vectors, and status trees.
- `/sys/behavior/contracts/`: Active safety contracts, rate limits, and policy enforcement rules.
- **POSIX API Support**: Fully implements `read()`, `write()`, `stat()`, `ls()`, and `chmod()` operations over live cognitive runtime states.

### 4. 💬 Behavior Protocol (`bproto.py`)
Structured 6-stage cognitive Inter-Process Communication (IPC) for multi-agent coordination:
$$\text{PROPOSE\_GOAL} \xrightarrow{\quad} \text{REQUEST\_GOAL} \xrightarrow{\quad} \text{NEGOTIATE} \xrightarrow{\quad} \text{DELEGATE} \xrightarrow{\quad} \text{REJECT} \xrightarrow{\quad} \text{COMMIT}$$

### 5. 🔲 Behavior Virtual Machine (`bvm.py`)
Provider-agnostic cognitive bytecode VM executing instructions independently of underlying LLM provider APIs:
- `OP_THINK`: Execute cognitive reasoning block.
- `OP_INSPECT_MEMORY`: Retrieve state from L1–L6 memory hierarchy.
- `OP_VERIFY_POLICY`: Evaluate safety contract constraints.
- `OP_EXECUTE_TOOL`: Invoke external API/tool with safety checks.
- `OP_REFLECT`: Compute self-correction delta and adjust plan.

### 6. 📦 Behavior Containers & `bpkg` (`bcontainer.py`)
Portable, self-contained `.bcontainer` bundles packing Behavior Genome DNA, Contract Policies, and execution manifests. Package management and registry deployment powered by `bpkg`.

### 7. ☸️ Intelligence Kubernetes (`ik8s.py`)
Cluster orchestrator managing `AgentPod` process groups with auto-scaling based on cognitive workload spikes, token pressure, and goal-driven failover migration.

### 8. 🏢 Digital Organization & Economics (`digi_org.py`)
Models corporate org charts (AI Employees, Managers, Department Heads) paired with multi-budget enforcement across financial spend (USD), token consumption, and tool execution volume.

### 9. 🌐 Civilization Macro Engine (`civilization.py`)
Systemic governance framework measuring AI macro-economy output (AI GDP), market trade velocity, fleet safety index, and behavioral convergence across thousands of concurrent autonomous processes.

---

## 📦 Developer Ecosystem & SDKs

### Python SDK (`packages/evolution-sdk-python`)
```python
import veri
from veri.contracts import behavior_contract

# Initialize VERI Intelligence OS Engine
veri.init(api_key="veri_live_key_99", cost_limit=10.0)

# Enforce Behavioral Safety Contract
@behavior_contract(max_cost=2.50, forbidden_tools=["unapproved_transfer"])
def execute_trading_strategy(order_amount: float):
    # Instrumented session tracking with automatic IRRef dataflow tagging
    with veri.session(session_id="sess_trade_01", agent_id="agent_alpha", project_id="finance_dept"):
        # Live kernel execution under BID tracking
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
  // Autonomous agent execution guarded by AsyncLocalStorage context...
});
```

---

## 🛠️ VERI CLI Developer Suite (`packages/veri-cli`)

Inspect, debug, and manage the Intelligence OS directly from your terminal:

| Command | Description |
|---|---|
| `veri ps` | List active Behavior Processes in `ikernel` with BID, state, and budget utilization |
| `veri bql "<query>"` | Execute Behavior Query Language (BQL) queries over live intelligence graphs |
| `veri run <container>` | Execute a `.bcontainer` package inside the Behavior Virtual Machine (BVM) |
| `veri compile <session_id>` | Pass a session through the 7-stage Compiler 2.0 optimization pipeline |
| `veri ifs <path>` | Inspect virtual Intelligence File System paths (e.g. `/sys/behavior/goals`) |
| `veri install <package>` | Install a Behavior Package via `bpkg` package registry |
| `veri top` | Real-time interactive resource monitor for token budget & process load |
| `veri verify` | Run end-to-end OS verification test suite |

---

## 🖥️ Microservices Stack & Enterprise Cockpit

VERI includes a high-performance backend stack written in Go alongside an interactive web interface:

- **Go API Gateway (`services/gateway`)**: High-performance HTTP/gRPC gateway handling OS requests, BQL queries, BVM bytecode dispatch, Compiler 2.0 optimization pipelines, and real-time WebSocket streams.
- **Go Telemetry Analyzer (`services/analyzer`)**: Distributed background worker processing telemetry streams, calculating causal deltas, updating memory tiers, and evaluating macro-governance metrics.
- **Enterprise Cockpit Dashboard (`web/index.html`)**: Glassmorphic web interface featuring four dedicated workspaces:
  - **Executive Summary**: High-level macro metrics, AI GDP, total token burn, and organizational risk scores.
  - **Operations Center**: Real-time process tree (`ikernel`), live agent pod monitor (`ik8s`), and active policy alerts.
  - **Behavior Explorer**: Deep virtual filesystem browser (`/sys/behavior/...`) and interactive BQL query editor.
  - **Evolution Lab**: Replay engine, counterfactual ablation workspace, and BVM bytecode debugger.

---

## 🚀 Quickstart & Verification Suite

### 1. Launch Infrastructure Stack
```bash
docker compose up -d
```

### 2. Launch Gateway and Backend Services
```bash
.\run_end_to_end.bat
```

### 3. Run Verification Test Suites
Verify all subsystems of the Intelligence Operating System:

```bash
# BehaviorOS v6.0 Intelligence OS Suite (ikernel, IFS, BVM, BPROTO, memory)
python verify_v6.py

# BehaviorOS v5.0 Platform Suite (behavior graph, DB, engine)
python verify_v5.py

# BehaviorOS v4.0 Intelligence Engines (causal, prediction, optimizer)
python verify_behavioros.py

# Ecosystem Suite (TypeScript SDK & VERI CLI)
python verify_ecosystem.py

# Roadmap Verification Suite
python verify_roadmap.py

# Specialized Core Verification Suites
python verify_sdk.py
python verify_ir.py
python verify_matcher.py
python verify_optimizer.py
python verify_escalation.py
python verify_deep_intelligence.py
python verify_intelligence.py
```

---

## 📂 Project Directory Layout

```text
veri/
├── packages/
│   ├── evolution-sdk-python/   # BehaviorOS v6.0 Python SDK (ikernel, IFS, BVM, BPROTO, memory_manager)
│   ├── evolution-sdk-ts/       # @veri-ai/sdk TypeScript SDK with AsyncLocalStorage tracking
│   ├── runtime-ir/             # Universal Runtime IR type definitions & schema specifications
│   └── veri-cli/               # veri command-line developer suite (ps, bql, run, compile, ifs, install)
├── services/
│   ├── gateway/                # Go API Gateway (OS handlers, BQL engine, Compiler 2.0, REST/WS)
│   └── analyzer/               # Go background telemetry & intelligence aggregator service
├── web/
│   └── index.html              # Enterprise Cockpit Dashboard (Executive, Operations, Explorer, Lab)
├── infrastructure/             # Docker, Kubernetes & deployment manifests
├── veri.yaml                   # Intelligence OS configuration manifest
├── VERI_BUILD_SPEC.md          # Complete architectural specification & build requirements
└── docker-compose.yml          # Multi-service infrastructure orchestration manifest
```

---

## 📄 License
Licensed under the [Apache 2.0 License](LICENSE).
