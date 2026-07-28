"""
VERI Intelligence Kernel (ikernel) — BehaviorOS v6.0

The Linux equivalent for autonomous AI systems.
Manages Behavior Processes (BID), Reasoning Budgets (CPU), Context Windows (RAM),
Memory Layers (Disk), Concurrent Thoughts (Threads), and Security Boundaries.

Linux vs ikernel Equivalents:
  - PID               ──► Behavior ID (BID)
  - CPU Time          ──► Reasoning Budget (Tokens / Flops)
  - RAM               ──► Context Window Allotment
  - Disk              ──► Hierarchical Memory Layers (L1-L6)
  - Network           ──► Behavior Protocol (BPROTO)
  - Threads           ──► Concurrent Thought Threads
"""

import time
try:
    import ulid
except ImportError:
    import uuid as _uuid

    class _ULIDFallback:
        @property
        def str(self) -> str:
            return str(_uuid.uuid4())

    class ulid:  # type: ignore[no-redef]
        @staticmethod
        def new() -> _ULIDFallback:
            return _ULIDFallback()

import threading
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple, Callable

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind


# ── Process State Enum ─────────────────────────────────────────────


class ProcessState(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    THINKING = "thinking"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    FAULTED = "faulted"


# ── OS Resource Budgets ───────────────────────────────────────────


class ReasoningBudget:
    """Reasoning Budget (the CPU equivalent for AI processes)."""

    def __init__(self, max_tokens: int = 100000, max_cost_usd: float = 5.0):
        self.max_tokens = max_tokens
        self.consumed_tokens = 0
        self.max_cost_usd = max_cost_usd
        self.consumed_cost_usd = 0.0

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.consumed_tokens)

    @property
    def remaining_cost_usd(self) -> float:
        return max(0.0, self.max_cost_usd - self.consumed_cost_usd)

    def consume(self, tokens: int, cost_usd: float) -> bool:
        """Consumes budget. Returns True if within limit, False if exhausted."""
        self.consumed_tokens += tokens
        self.consumed_cost_usd += cost_usd

        if self.consumed_tokens > self.max_tokens or self.consumed_cost_usd > self.max_cost_usd:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "consumed_tokens": self.consumed_tokens,
            "remaining_tokens": self.remaining_tokens,
            "max_cost_usd": round(self.max_cost_usd, 4),
            "consumed_cost_usd": round(self.consumed_cost_usd, 4),
            "remaining_cost_usd": round(self.remaining_cost_usd, 4),
        }


class ContextWindowAllotment:
    """Context Window Allotment (the RAM equivalent for AI processes)."""

    def __init__(self, max_context_tokens: int = 128000):
        self.max_context_tokens = max_context_tokens
        self.active_tokens = 0

    def allocate(self, tokens: int) -> bool:
        if self.active_tokens + tokens > self.max_context_tokens:
            return False
        self.active_tokens += tokens
        return True

    def free(self, tokens: int) -> None:
        self.active_tokens = max(0, self.active_tokens - tokens)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_context_tokens": self.max_context_tokens,
            "active_tokens": self.active_tokens,
            "utilization": round(self.active_tokens / max(1, self.max_context_tokens), 4),
        }


class ConcurrentThought:
    """A concurrent thought thread inside a BehaviorProcess."""

    def __init__(self, thought_id: str, label: str, prompt: str):
        self.thought_id = thought_id
        self.label = label
        self.prompt = prompt
        self.status = "active"
        self.output: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thought_id": self.thought_id,
            "label": self.label,
            "status": self.status,
            "output": self.output,
        }


# ── Behavior Process ───────────────────────────────────────────────


class BehaviorProcess:
    """
    The fundamental unit of execution in the Intelligence OS (Linux process equivalent).

    Controlled by a unique Behavior ID (BID), with dedicated reasoning budget,
    context window RAM, memory layers, and concurrent thought threads.
    """

    def __init__(
        self,
        agent_id: str,
        goal: str,
        bid: Optional[str] = None,
        reasoning_budget: Optional[ReasoningBudget] = None,
        context_allotment: Optional[ContextWindowAllotment] = None,
        parent_bid: Optional[str] = None,
    ):
        self.bid = bid or f"bid_{ulid.new().str}"
        self.agent_id = agent_id
        self.goal = goal
        self.parent_bid = parent_bid
        self.state = ProcessState.INITIALIZING
        self.reasoning_budget = reasoning_budget or ReasoningBudget()
        self.context_allotment = context_allotment or ContextWindowAllotment()

        self.thoughts: Dict[str, ConcurrentThought] = {}
        self.executed_nodes: List[RuntimeNode] = []

        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.terminated_at: Optional[float] = None

    def spawn_thought(self, label: str, prompt: str) -> ConcurrentThought:
        """Spawns a concurrent thought thread (OS thread equivalent)."""
        tid = f"thought_{len(self.thoughts) + 1}"
        thought = ConcurrentThought(tid, label, prompt)
        self.thoughts[tid] = thought
        return thought

    def update_state(self, new_state: ProcessState) -> None:
        self.state = new_state
        if new_state == ProcessState.RUNNING and not self.started_at:
            self.started_at = time.time()
        elif new_state in (ProcessState.TERMINATED, ProcessState.FAULTED):
            self.terminated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bid": self.bid,
            "agent_id": self.agent_id,
            "goal": self.goal,
            "parent_bid": self.parent_bid,
            "state": self.state.value,
            "reasoning_budget": self.reasoning_budget.to_dict(),
            "context_allotment": self.context_allotment.to_dict(),
            "active_thoughts_count": len(self.thoughts),
            "executed_nodes_count": len(self.executed_nodes),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "terminated_at": self.terminated_at,
        }


# ── Intelligence Kernel Manager ────────────────────────────────────


class IntelligenceKernel:
    """
    The master process kernel (`ikernel`).
    Manages process lifecycle, process tables, resource scheduling,
    IPC, and security boundary isolation.
    """

    def __init__(self, max_concurrent_processes: int = 100):
        self.max_concurrent_processes = max_concurrent_processes
        self.process_table: Dict[str, BehaviorProcess] = {}
        self._lock = threading.Lock()

    def create_process(
        self,
        agent_id: str,
        goal: str,
        max_tokens: int = 100000,
        max_cost_usd: float = 5.0,
        parent_bid: Optional[str] = None,
    ) -> BehaviorProcess:
        """Spawns a new BehaviorProcess and assigns a unique Behavior ID (BID)."""
        with self._lock:
            budget = ReasoningBudget(max_tokens=max_tokens, max_cost_usd=max_cost_usd)
            allotment = ContextWindowAllotment()
            proc = BehaviorProcess(
                agent_id=agent_id,
                goal=goal,
                reasoning_budget=budget,
                context_allotment=allotment,
                parent_bid=parent_bid,
            )
            proc.update_state(ProcessState.RUNNING)
            self.process_table[proc.bid] = proc
            return proc

    def terminate_process(self, bid: str, reason: str = "normal_exit") -> bool:
        """Terminates a running process (kill equivalent)."""
        with self._lock:
            proc = self.process_table.get(bid)
            if proc:
                proc.update_state(ProcessState.TERMINATED)
                return True
            return False

    def suspend_process(self, bid: str) -> bool:
        """Suspends a process (SIGSTOP equivalent)."""
        with self._lock:
            proc = self.process_table.get(bid)
            if proc:
                proc.update_state(ProcessState.SUSPENDED)
                return True
            return False

    def resume_process(self, bid: str) -> bool:
        """Resumes a suspended process (SIGCONT equivalent)."""
        with self._lock:
            proc = self.process_table.get(bid)
            if proc and proc.state == ProcessState.SUSPENDED:
                proc.update_state(ProcessState.RUNNING)
                return True
            return False

    def get_process(self, bid: str) -> Optional[BehaviorProcess]:
        return self.process_table.get(bid)

    def list_processes(self) -> List[Dict[str, Any]]:
        """Returns process table entries (ps equivalent)."""
        with self._lock:
            return [p.to_dict() for p in self.process_table.values()]

    def get_kernel_stats(self) -> Dict[str, Any]:
        """Kernel operational statistics (top / htop equivalent)."""
        with self._lock:
            active = sum(1 for p in self.process_table.values() if p.state == ProcessState.RUNNING)
            suspended = sum(1 for p in self.process_table.values() if p.state == ProcessState.SUSPENDED)
            terminated = sum(1 for p in self.process_table.values() if p.state in (ProcessState.TERMINATED, ProcessState.FAULTED))

            return {
                "total_processes": len(self.process_table),
                "active_processes": active,
                "suspended_processes": suspended,
                "terminated_processes": terminated,
                "max_concurrent_capacity": self.max_concurrent_processes,
            }
