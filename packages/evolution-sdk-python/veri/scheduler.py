"""
VERI Behavior Scheduler — BehaviorOS v5.0

Multi-agent priority and resource scheduling engine.
Answers: "In a fleet of 100,000 agents, who runs first, who waits, and who gets paused?"

Priority Dispatch Function:
  Score = w1 * Priority - w2 * Risk + w3 * ResourceAvail + w4 * Trust - w5 * Cost + w6 * Impact
"""

import time
import math
from typing import List, Dict, Any, Optional, Tuple

from veri.ir import RuntimeNode


# ── Data Structures ────────────────────────────────────────────────


class AgentTask:
    """An agent task queued for execution in the Behavior Scheduler."""

    def __init__(
        self,
        task_id: str,
        agent_id: str,
        session_id: str,
        priority: float = 0.5,        # [0, 1] Base business priority
        risk_score: float = 0.1,      # [0, 1] Predicted operational risk
        resource_req: float = 0.2,    # [0, 1] Required compute/token resources
        trust_score: float = 0.8,     # [0, 1] Agent trust score
        estimated_cost: float = 0.01, # USD cost
        business_impact: float = 0.5, # [0, 1] Impact of execution
    ):
        self.task_id = task_id
        self.agent_id = agent_id
        self.session_id = session_id
        self.priority = priority
        self.risk_score = risk_score
        self.resource_req = resource_req
        self.trust_score = trust_score
        self.estimated_cost = estimated_cost
        self.business_impact = business_impact
        self.queued_at = time.time()
        self.scheduled_at: Optional[float] = None
        self.status: str = "queued"  # "queued", "running", "paused", "completed"

    def compute_dispatch_score(
        self,
        w_priority: float = 0.25,
        w_risk: float = 0.20,
        w_resource: float = 0.15,
        w_trust: float = 0.15,
        w_cost: float = 0.10,
        w_impact: float = 0.15,
    ) -> float:
        """
        Calculates the multi-objective dispatch priority score.
        Higher score = earlier execution.
        """
        # Age boost: prevent starvation (0.01 per second queued)
        age_boost = min(0.2, (time.time() - self.queued_at) * 0.01)

        score = (
            w_priority * self.priority
            - w_risk * self.risk_score
            + w_resource * (1.0 - self.resource_req)
            + w_trust * self.trust_score
            - w_cost * min(1.0, self.estimated_cost / 1.0)
            + w_impact * self.business_impact
            + age_boost
        )
        return max(0.0, score)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "priority": self.priority,
            "risk_score": self.risk_score,
            "resource_req": self.resource_req,
            "trust_score": self.trust_score,
            "estimated_cost": round(self.estimated_cost, 4),
            "business_impact": self.business_impact,
            "dispatch_score": round(self.compute_dispatch_score(), 4),
            "status": self.status,
            "queued_at": self.queued_at,
        }


# ── Behavior Scheduler ─────────────────────────────────────────────


class BehaviorScheduler:
    """
    Multi-tenant, multi-agent Behavior Scheduler for enterprise fleets.
    Manages task queues, resource allocation, and risk-aware dispatching.
    """

    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_queue: List[AgentTask] = []
        self.running_tasks: List[AgentTask] = []
        self.paused_tasks: List[AgentTask] = []
        self.completed_tasks: List[AgentTask] = []

    def enqueue_task(self, task: AgentTask) -> None:
        """Enqueues a new agent task for scheduling."""
        self.task_queue.append(task)

    def schedule_next(self) -> List[AgentTask]:
        """
        Runs the priority dispatch algorithm over the queue and returns
        the next batch of tasks to execute up to max_concurrent_tasks.
        """
        # Re-sort queue by dispatch score descending
        self.task_queue.sort(key=lambda t: t.compute_dispatch_score(), reverse=True)

        dispatched = []
        while len(self.running_tasks) < self.max_concurrent_tasks and self.task_queue:
            task = self.task_queue.pop(0)
            task.status = "running"
            task.scheduled_at = time.time()
            self.running_tasks.append(task)
            dispatched.append(task)

        return dispatched

    def pause_task(self, task_id: str, reason: str = "") -> Optional[AgentTask]:
        """Pauses a running task (e.g. high risk or human approval needed)."""
        for i, t in enumerate(self.running_tasks):
            if t.task_id == task_id:
                t.status = "paused"
                self.running_tasks.pop(i)
                self.paused_tasks.append(t)
                return t
        return None

    def complete_task(self, task_id: str) -> Optional[AgentTask]:
        """Marks a running task as completed and frees scheduler slot."""
        for i, t in enumerate(self.running_tasks):
            if t.task_id == task_id:
                t.status = "completed"
                self.running_tasks.pop(i)
                self.completed_tasks.append(t)
                return t
        return None

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Returns full scheduler operational status."""
        return {
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "queued_count": len(self.task_queue),
            "running_count": len(self.running_tasks),
            "paused_count": len(self.paused_tasks),
            "completed_count": len(self.completed_tasks),
            "queue": [t.to_dict() for t in self.task_queue[:10]],
            "running": [t.to_dict() for t in self.running_tasks],
        }
