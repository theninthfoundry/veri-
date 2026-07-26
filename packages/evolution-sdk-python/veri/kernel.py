"""
VERI Behavior Kernel — BehaviorOS v5.0

The central runtime operating system kernel through which all agent execution flows.
Replaces "analytics on top of execution" with "intelligence INSIDE execution".

Execution Pipeline per Node:
  Agent Input
      │
      ▼
  1. Behavior State Engine    ──► Classifies cognitive phase & state vector
      │
      ▼
  2. Behavior Graph Engine    ──► Integrates node into unified cognitive belief graph
      │
      ▼
  3. Policy Engine            ──► Enforces active BehaviorContract guardrails
      │
      ▼
  4. Prediction Engine        ──► Evaluates anomaly risks & EWMA confidence
      │
      ▼
  5. Behavior Compiler        ──► Performs static graph pass optimizations
      │
      ▼
  6. Execution Dispatch       ──► Yields verified, safe, optimized execution step
"""

import time
from typing import List, Dict, Any, Optional, Tuple, Callable

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind
from veri.state_engine import BehavioralStateEngine, CognitivePhase, CognitiveStateVector
from veri.prediction import run_predictive_analysis, Prediction
from veri.optimizer import run_optimization_passes, Optimization
from veri.contracts import BehaviorContract, ContractViolation


# ── Kernel Kernel Context ──────────────────────────────────────────


class KernelStepResult:
    """The result of passing a single node through the Behavior Kernel."""

    def __init__(
        self,
        node: RuntimeNode,
        phase: CognitivePhase,
        state_vector: CognitiveStateVector,
        violations: List[ContractViolation],
        predictions: List[Prediction],
        optimizations: List[Optimization],
        allowed: bool,
        kernel_latency_ms: float,
    ):
        self.node = node
        self.phase = phase
        self.state_vector = state_vector
        self.violations = violations
        self.predictions = predictions
        self.optimizations = optimizations
        self.allowed = allowed
        self.kernel_latency_ms = kernel_latency_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node.id,
            "label": self.node.label,
            "kind": self.node.kind,
            "phase": self.phase.value,
            "state_vector": self.state_vector.to_dict(),
            "violations": [v.to_dict() for v in self.violations],
            "predictions": [p.to_dict() for p in self.predictions],
            "optimizations": [o.to_dict() for o in self.optimizations],
            "allowed": self.allowed,
            "kernel_latency_ms": round(self.kernel_latency_ms, 3),
        }


# ── Behavior Kernel ────────────────────────────────────────────────


class BehaviorKernel:
    """
    The central runtime operating system kernel.

    Maintains unified state across all agent operations in a session,
    enforcing policies, running predictions, and compiling optimizations
    in-flight before tool/LLM execution occurs.
    """

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        project_id: str,
        contract: Optional[BehaviorContract] = None,
        budget: float = 5.0,
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.project_id = project_id
        self.contract = contract or BehaviorContract()
        self.budget = budget

        # Core state engines
        self.state_engine = BehavioralStateEngine()
        self.nodes: List[RuntimeNode] = []
        self.edges: List[RuntimeEdge] = []
        self.step_history: List[KernelStepResult] = []

        # Circuit breaker state
        self.halted: bool = False
        self.halt_reason: Optional[str] = None

    def process_node(
        self, node: RuntimeNode, incoming_edges: Optional[List[RuntimeEdge]] = None
    ) -> KernelStepResult:
        """
        Processes a single node through the complete 6-stage Behavior Kernel pipeline.

        Raises RuntimeError if the kernel has been halted by a policy violation.
        """
        start_time = time.time()

        if self.halted:
            raise RuntimeError(
                f"Behavior Kernel is HALTED for session '{self.session_id}'. "
                f"Reason: {self.halt_reason}"
            )

        # 1. State Engine: Classify phase and update continuous state vector
        self.state_engine.ingest_node(node)
        current_phase = self.state_engine.get_cognitive_phase()
        state_vector = self.state_engine.get_state_vector()

        # Add node to active trace
        self.nodes.append(node)
        if incoming_edges:
            self.edges.extend(incoming_edges)

        # 2. Policy Engine: Verify trace against contracts
        serialized_nodes = [
            {
                "id": n.id,
                "name": n.label,
                "kind": n.kind,
                "content": n.content,
                "metrics": {"cost_usd": n.cost, "latency": n.latency},
            }
            for n in self.nodes
        ]
        violations = self.contract.verify_trace(serialized_nodes)

        # Halt kernel if critical contract violation occurs
        allowed = True
        if violations:
            for v in violations:
                if v.rule in ("forbidden_tools", "max_cost"):
                    allowed = False
                    self.halted = True
                    self.halt_reason = f"Contract violation [{v.rule}]: {v.message}"
                    break

        # 3. Prediction Engine: Analyze risks & anomalies
        predictions = run_predictive_analysis(self.nodes, budget=self.budget)

        # 4. Compiler: Run static graph pass optimizations
        optimizations = run_optimization_passes(self.nodes, self.edges)

        kernel_latency = (time.time() - start_time) * 1000.0

        step_result = KernelStepResult(
            node=node,
            phase=current_phase,
            state_vector=state_vector,
            violations=violations,
            predictions=predictions,
            optimizations=optimizations,
            allowed=allowed,
            kernel_latency_ms=kernel_latency,
        )
        self.step_history.append(step_result)
        return step_result

    def process_nodes(
        self, nodes: List[RuntimeNode], edges: Optional[List[RuntimeEdge]] = None
    ) -> List[KernelStepResult]:
        """Batch process a sequence of nodes through the kernel."""
        results = []
        for n in nodes:
            res = self.process_node(n, edges)
            results.append(res)
            if not res.allowed:
                break
        return results

    def get_kernel_status(self) -> Dict[str, Any]:
        """Returns the current operational status of the Behavior Kernel."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "project_id": self.project_id,
            "halted": self.halted,
            "halt_reason": self.halt_reason,
            "processed_nodes": len(self.nodes),
            "processed_edges": len(self.edges),
            "current_phase": self.state_engine.get_cognitive_phase().value,
            "state_vector": self.state_engine.get_state_vector().to_dict(),
            "active_violations": sum(len(r.violations) for r in self.step_history),
            "active_predictions": len(self.step_history[-1].predictions) if self.step_history else 0,
            "avg_kernel_latency_ms": round(
                sum(r.kernel_latency_ms for r in self.step_history) / max(1, len(self.step_history)), 3
            ),
        }
