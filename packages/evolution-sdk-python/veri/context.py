"""
VERI Session & Span Context — The operational core.

Tracks hierarchical execution state via contextvars (async-safe),
computes parent-child span relationships dynamically, and enforces
L0 circuit-breakers (cost limit, call limit) entirely in-process
with zero network round-trips.
"""

import json
import time
import contextvars
import threading
from typing import Any, Dict, List, Optional, Tuple

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
from .ir_ref import IRRef, extract_refs
from .escalation import (
    EscalationEngine,
    EscalationPolicy,
    EscalationRecord,
    EscalationRequired,
    EscalationAborted,
)


# ── L0 Guardrail Exceptions ────────────────────────────────────────


class VeriL0Exception(Exception):
    """Base exception for L0 circuit-breaker activations."""

    pass


class VeriCostLimitExceeded(VeriL0Exception):
    """Raised when session USD spend exceeds the configured cap."""

    pass


class VeriCallLimitExceeded(VeriL0Exception):
    """Raised when LLM call count exceeds the configured cap."""

    pass


# ── Thread-Safe Context Variables ──────────────────────────────────

active_session_context: contextvars.ContextVar[Optional["AgentSessionContext"]] = (
    contextvars.ContextVar("veri_active_session", default=None)
)
active_span_stack: contextvars.ContextVar[List[Tuple[str, str]]] = contextvars.ContextVar(
    "veri_span_stack", default=[]
)


# ── Serialization Boundary ─────────────────────────────────────────


def safe_serialize(obj: Any) -> str:
    """
    Graceful serialization — never crashes, always produces useful output.

    For serializable objects: returns JSON string.
    For non-serializable objects (DB cursors, file handles, class instances):
    returns a fingerprint with type, truncated repr, and object id.
    """
    if isinstance(obj, IRRef):
        obj = obj.unwrap()

    if isinstance(obj, (str, int, float, bool, type(None))):
        return json.dumps(obj)

    memo = set()

    def clean(o):
        if id(o) in memo:
            return {"__veri_cycle__": True, "id": id(o)}
        if isinstance(o, (str, int, float, bool, type(None))):
            return o

        memo.add(id(o))
        try:
            if isinstance(o, dict):
                return {str(k): clean(v) for k, v in o.items()}
            if isinstance(o, (list, tuple, set)):
                return [clean(v) for v in o]
            return {
                "__veri_unserializable__": True,
                "type": type(o).__name__,
                "repr": repr(o)[:250],
                "id": id(o),
            }
        finally:
            memo.remove(id(o))

    try:
        return json.dumps(clean(obj), ensure_ascii=False)
    except Exception:
        return json.dumps(
            {
                "__veri_unserializable__": True,
                "type": type(obj).__name__,
                "repr": repr(obj)[:250],
                "id": id(obj),
            }
        )


# ── Session Context ────────────────────────────────────────────────


class ReplayNode:
    def __init__(
        self,
        id: str,
        category: str,
        name: str,
        input_data: Any,
        output_data: Any = None,
        capabilities: Optional[List[str]] = None,
        replay_fn: Optional[Any] = None,
        replay_args: Optional[Tuple] = None,
        replay_kwargs: Optional[Dict] = None,
    ):
        self.id = id
        self.category = category
        self.name = name
        self.input_data = input_data
        self.output_data = output_data
        self.capabilities = capabilities or []
        self.replay_fn = replay_fn
        self.replay_args = replay_args or ()
        self.replay_kwargs = replay_kwargs or {}


class ReplayGraph:
    def __init__(self):
        self.nodes: Dict[str, ReplayNode] = {}
        self.edges: List[Tuple[str, str, str]] = []  # (source, target, kind)

    def add_node(self, node: ReplayNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, source_id: str, target_id: str, kind: str) -> None:
        self.edges.append((source_id, target_id, kind))


_session_registry: Dict[str, "AgentSessionContext"] = {}


class AgentSessionContext:
    """
    Tracks a single agent execution session. Manages:
    - Hierarchical span relationships (parent-child via stack)
    - Cumulative cost and call-count tracking
    - L0 guardrail enforcement (local, no network)
    - Session lifecycle events (started/completed/failed)
    - Semantic context managers for Universal Runtime IR (intent, reasoning, etc)
    """

    def __init__(
        self,
        client,
        session_id: str,
        agent_id: str,
        project_id: str,
        cost_limit: float,
        call_limit: int,
        escalation_engine: Optional[EscalationEngine] = None,
    ):
        self.client = client
        self.session_id = session_id
        self.agent_id = agent_id
        self.project_id = project_id

        self.cost_limit = cost_limit
        self.call_limit = call_limit
        self.replay_graph = ReplayGraph()

        self.total_cost_usd: float = 0.0
        self.llm_call_count: int = 0
        self._lock = threading.Lock()

        # Escalation engine — loaded from gateway on session start
        self.escalation_engine = escalation_engine or EscalationEngine(enabled=False)

        self._session_token = None
        self._span_token = None

    def __enter__(self):
        self._session_token = active_session_context.set(self)
        self._span_token = active_span_stack.set([])
        _session_registry[self.session_id] = self

        # Load escalation policies for this project
        self.escalation_engine.load_policies(self.project_id)

        self.client.emit_async(
            {
                "id": ulid.new().str,
                "project_id": self.project_id,
                "agent_id": self.agent_id,
                "session_id": self.session_id,
                "category": "system",
                "type": "session.started",
                "timestamp": time.time(),
            }
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        status = "completed" if exc_type is None else "failed"
        payload: Dict[str, Any] = {}
        if exc_val:
            payload["error"] = {
                "code": exc_type.__name__ if exc_type else "Unknown",
                "message": str(exc_val),
            }

        self.client.emit_async(
            {
                "id": ulid.new().str,
                "project_id": self.project_id,
                "agent_id": self.agent_id,
                "session_id": self.session_id,
                "category": "system",
                "type": f"session.{status}",
                "payload": payload,
                "metrics": {
                    "total_cost_usd": self.total_cost_usd,
                    "llm_call_count": self.llm_call_count,
                },
                "timestamp": time.time(),
            }
        )

        active_session_context.reset(self._session_token)
        active_span_stack.reset(self._span_token)

        # Don't suppress L0 exceptions — let them propagate
        return False

    def increment_and_verify_l0(self, cost_delta: float) -> None:
        """
        Updates session counters and enforces L0 guardrails.
        Entirely local — zero network calls. Sub-microsecond latency.
        """
        with self._lock:
            self.total_cost_usd += cost_delta
            self.llm_call_count += 1

            if self.total_cost_usd > self.cost_limit:
                raise VeriCostLimitExceeded(
                    f"Session cost ${self.total_cost_usd:.4f} exceeded "
                    f"limit ${self.cost_limit:.4f}. Execution halted."
                )
            if self.llm_call_count > self.call_limit:
                raise VeriCallLimitExceeded(
                    f"LLM call count {self.llm_call_count} exceeded "
                    f"limit {self.call_limit}. Execution halted."
                )

    # ── Semantic Context Managers for Runtime IR ───────────────────

    def intent(self, label: str, constraints: Optional[List[str]] = None, budget: Optional[float] = None):
        from .ir import NodeKind
        return ExecutionSpanScope(
            self.client, NodeKind.INTENT, label,
            content={"constraints": constraints or [], "budget": budget}
        )

    def knowledge(self, label: str, assumptions: Optional[List[str]] = None, evidence: Optional[List[str]] = None):
        from .ir import NodeKind
        return ExecutionSpanScope(
            self.client, NodeKind.KNOWLEDGE, label,
            assumptions=assumptions, evidence=evidence
        )

    def reasoning(self, label: str, assumptions: Optional[List[str]] = None):
        from .ir import NodeKind
        return ExecutionSpanScope(
            self.client, NodeKind.REASONING, label,
            assumptions=assumptions
        )

    def action(self, label: str, tool_name: Optional[str] = None):
        from .ir import NodeKind
        return ExecutionSpanScope(
            self.client, NodeKind.ACTION, label,
            content={"tool_name": tool_name}
        )

    def decision(self, label: str, alternatives: Optional[List[str]] = None, reasoning: Optional[str] = None):
        from .ir import NodeKind
        return ExecutionSpanScope(
            self.client, NodeKind.DECISION, label,
            content={"alternatives": alternatives or [], "reasoning": reasoning}
        )

    def escalate(
        self,
        label: str,
        action_type: str,
        risk: float = 0.0,
        content: Optional[Dict[str, Any]] = None,
    ):
        """
        Explicit escalation point — developer marks a high-risk action
        that requires human approval regardless of automatic policy matching.

        Usage:
            with session.escalate("Process refund $450", action_type="refund", risk=0.9) as esc:
                esc.complete(result, metrics={"amount": 450.0})
        """
        from .ir import NodeKind
        return ExecutionSpanScope(
            self.client, NodeKind.ESCALATION, label,
            content={"action_type": action_type, "risk": risk, **(content or {})},
            capabilities=["is_decision_point", "has_dataflow_deps", "affects_cost"],
            force_escalation_action_type=action_type,
            force_escalation_risk=risk,
        )

    def analyze_failure(self, baseline_session_id: str) -> Optional[str]:
        """
        Runs counterfactual golden-baseline substitution over the graph.
        For each replayable node in the current session:
          1. Find the corresponding node in the baseline session (by label/name).
          2. If the baseline node exists, run the node's replay_fn using the baseline input.
          3. Determine if the output matches the baseline output (recovered).
          4. If it does, we have verified that substituting this baseline input resolves the failure,
             indicating this node is the causal culprit!
        """
        baseline_session = _session_registry.get(baseline_session_id)
        if not baseline_session:
            return None

        baseline_nodes_by_name = {n.name: n for n in baseline_session.replay_graph.nodes.values()}

        for node_id, node in self.replay_graph.nodes.items():
            if "is_replayable" in node.capabilities and node.replay_fn:
                base_node = baseline_nodes_by_name.get(node.name)
                if base_node:
                    try:
                        replayed_output = node.replay_fn(base_node.input_data, *node.replay_args, **node.replay_kwargs)
                        if replayed_output == base_node.output_data:
                            return node.id
                    except Exception:
                        pass
        return None


# ── Execution Span ─────────────────────────────────────────────────


def get_edge_kind(parent_kind: str, child_kind: str) -> str:
    from .ir import NodeKind, EdgeKind
    if parent_kind == NodeKind.INTENT and child_kind in (NodeKind.INTENT, NodeKind.SUBGOAL):
        return EdgeKind.DECOMPOSES_INTO
    if parent_kind == NodeKind.REASONING and child_kind in (NodeKind.ACTION, NodeKind.TOOL_INVOCATION, NodeKind.LLM_CALL):
        return EdgeKind.CAUSES
    if parent_kind == NodeKind.DECISION and child_kind in (NodeKind.ACTION, NodeKind.TOOL_INVOCATION):
        return EdgeKind.CAUSES
    if parent_kind == NodeKind.ACTION and child_kind == NodeKind.OUTCOME:
        return EdgeKind.CAUSES
    if parent_kind == NodeKind.KNOWLEDGE and child_kind == NodeKind.REASONING:
        return EdgeKind.SUPPORTS
    if parent_kind == NodeKind.ASSUMPTION and child_kind == NodeKind.REASONING:
        return EdgeKind.ASSUMES
    return EdgeKind.DEPENDS_ON


class ExecutionSpanScope:
    """
    Tracks a single logical step within a session (an LLM call,
    tool execution, reasoning step, etc).

    Automatically establishes parent-child relationships via the
    span stack in the active context, emitting RuntimeNodes and RuntimeEdges.
    """

    def __init__(
        self,
        client,
        category: str,
        name: str,
        input_data: Any = None,
        content: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        uncertainty: Optional[float] = None,
        evidence: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
        # v2 fields
        capabilities: Optional[List[str]] = None,
        confidence_source: Optional[str] = None,
        confidence_method: Optional[str] = None,
        # Accountability fields
        force_escalation_action_type: Optional[str] = None,
        force_escalation_risk: float = 0.0,
        # Replay fields
        replay_fn: Optional[Any] = None,
        replay_args: Optional[Tuple] = None,
        replay_kwargs: Optional[Dict] = None,
    ):
        self.client = client
        from .ir import NodeKind
        category_map = {
            "llm": NodeKind.LLM_CALL,
            "tool": NodeKind.TOOL_INVOCATION,
            "reasoning": NodeKind.REASONING,
            "system": NodeKind.WORLD_STATE,
        }
        self.category = category_map.get(category, category)
        self.name = name
        self.input_data = input_data

        self.content = content or {}
        self.confidence = confidence
        self.uncertainty = uncertainty
        self.evidence = evidence or []
        self.assumptions = assumptions or []

        # Derive capabilities based on Category/Kind if not provided
        if capabilities is None:
            caps = ["has_dataflow_deps"]
            if self.category in (NodeKind.LLM_CALL, NodeKind.REASONING):
                caps.extend(["has_measurable_confidence", "affects_cost"])
            elif self.category == NodeKind.DECISION:
                caps.extend(["is_decision_point", "affects_cost"])
            elif self.category in (NodeKind.TOOL_INVOCATION, NodeKind.ACTION):
                caps.extend(["is_replayable", "affects_cost"])
            self.capabilities = caps
        else:
            self.capabilities = capabilities

        # Derive confidence source
        if confidence_source is None:
            if confidence is not None:
                self.confidence_source = "self_reported"
            else:
                self.confidence_source = "unavailable"
        else:
            self.confidence_source = confidence_source
        self.confidence_method = confidence_method or ""

        # Extract IRRef references from inputs for measured dependency edges
        self.measured_dependencies = extract_refs(
            input_data, self.content, confidence, uncertainty, evidence, assumptions
        )

        self.span_id = ulid.new().str
        self.parent_span_id: Optional[str] = None
        self.start_time: float = 0.0

        # Accountability: escalation trigger params
        self._force_escalation_action_type = force_escalation_action_type
        self._force_escalation_risk = force_escalation_risk
        self._escalation_record: Optional[EscalationRecord] = None

        self.replay_fn = replay_fn
        self.replay_args = replay_args
        self.replay_kwargs = replay_kwargs

    def __enter__(self):
        session = active_session_context.get(None)
        if not session:
            return self

        stack = active_span_stack.get([])
        parent_category = None
        if stack:
            self.parent_span_id, parent_category = stack[-1]
        stack.append((self.span_id, self.category))

        self.start_time = time.time()

        # Add node to session replay graph
        session.replay_graph.add_node(ReplayNode(
            id=self.span_id,
            category=self.category,
            name=self.name,
            input_data=self.input_data,
            capabilities=self.capabilities,
            replay_fn=self.replay_fn,
            replay_args=self.replay_args,
            replay_kwargs=self.replay_kwargs,
        ))

        # 1. Emit measured dataflow edges based on extracted IRRefs
        for source_node_id, source_field in self.measured_dependencies:
            edge_payload = {
                "id": ulid.new().str,
                "project_id": session.project_id,
                "agent_id": session.agent_id,
                "session_id": session.session_id,
                "category": "edge",
                "type": "edge.created",
                "name": "depends_on",
                "payload": {
                    "source": source_node_id,
                    "target": self.span_id,
                    "weight": 1.0,
                    "metadata": {"source_field": source_field}
                },
                "timestamp": self.start_time,
                "edge_confidence_source": "measured"
            }
            self.client.emit_async(edge_payload)
            session.replay_graph.add_edge(source_node_id, self.span_id, "depends_on")

        # 2. If there's a parent, dynamically build and emit a structural RuntimeEdge
        if self.parent_span_id and parent_category:
            from .ir import RuntimeEdge
            edge_kind = get_edge_kind(parent_category, self.category)
            edge = RuntimeEdge(
                source=self.parent_span_id,
                target=self.span_id,
                kind=edge_kind,
                session_id=session.session_id,
            )
            edge_dict = edge.to_dict()
            edge_dict.update({
                "project_id": session.project_id,
                "agent_id": session.agent_id,
                "category": "edge",
                "type": "edge.created",
                "name": edge_kind,
                "payload": {
                    "source": edge.source,
                    "target": edge.target,
                    "weight": edge.weight,
                    "metadata": edge.metadata
                },
                "timestamp": self.start_time,
                "edge_confidence_source": "inferred"
            })
            self.client.emit_async(edge_dict)
            session.replay_graph.add_edge(self.parent_span_id, self.span_id, edge_kind)

        # 3. Emit RuntimeNode starting event
        self.client.emit_async(
            {
                "id": self.span_id,
                "parent_span_id": self.parent_span_id,
                "span_id": self.span_id,
                "project_id": session.project_id,
                "agent_id": session.agent_id,
                "session_id": session.session_id,
                "category": self.category,
                "type": f"{self.category}.started",
                "name": self.name,
                "payload": {"input": safe_serialize(self.input_data)},
                "timestamp": self.start_time,
                "kind": self.category,
                "label": self.name,
                "content": {"input": safe_serialize(self.input_data), **self.content},
                "confidence": self.confidence,
                "uncertainty": self.uncertainty,
                "evidence": self.evidence,
                "assumptions": self.assumptions,
                # v2 fields
                "confidence_value": self.confidence,
                "confidence_source": self.confidence_source,
                "confidence_method": self.confidence_method,
                "capabilities": self.capabilities,
            }
        )

        # 4. Evaluate escalation policies (Accountability Layer)
        # This is the hook that makes VERI a gatekeeper, not just an observer.
        self._evaluate_escalation(session)

        return self

    def _evaluate_escalation(self, session) -> None:
        """Checks this node against loaded escalation policies and triggers if matched."""
        engine = session.escalation_engine
        if engine is None:
            return

        # Determine action type from content or force parameter
        action_type = self._force_escalation_action_type
        if action_type is None and isinstance(self.content, dict):
            action_type = self.content.get("action_type") or self.content.get("tool_name")

        risk = self._force_escalation_risk

        matched_policy = engine.evaluate(
            node_kind=self.category,
            capabilities=self.capabilities,
            confidence_value=self.confidence,
            confidence_source=self.confidence_source,
            action_type=action_type,
            cost=0.0,  # cost not known at span start
            risk=risk,
        )

        if matched_policy is None:
            return

        # Trigger escalation
        record = engine.trigger_escalation(
            policy=matched_policy,
            session_id=session.session_id,
            project_id=session.project_id,
            agent_id=session.agent_id,
            node_id=self.span_id,
            node_kind=self.category,
            node_label=self.name,
            node_content=self.content,
            node_confidence_value=self.confidence,
            node_confidence_source=self.confidence_source,
            node_capabilities=self.capabilities,
        )

        if record is None:
            return

        self._escalation_record = record

        # Emit an escalation edge in the IR graph
        from .ir import EdgeKind
        self.client.emit_async({
            "id": ulid.new().str,
            "project_id": session.project_id,
            "agent_id": session.agent_id,
            "session_id": session.session_id,
            "category": "edge",
            "type": "edge.created",
            "name": EdgeKind.ESCALATES,
            "payload": {
                "source": self.span_id,
                "target": record.id,
                "weight": 1.0,
                "metadata": {
                    "policy_id": matched_policy.id,
                    "policy_name": matched_policy.name,
                    "behavior": matched_policy.timeout_behavior,
                }
            },
            "timestamp": time.time(),
            "edge_confidence_source": "measured"
        })

        # Add escalation capability tag to the node
        if "is_escalated" not in self.capabilities:
            self.capabilities.append("is_escalated")

        # Enforce behavior
        if matched_policy.timeout_behavior == "abort":
            raise EscalationAborted(
                escalation_id=record.id,
                policy_name=matched_policy.name,
                message=f"Action '{self.name}' aborted by escalation policy "
                        f"'{matched_policy.name}'. Escalation ID: {record.id}",
            )
        elif matched_policy.timeout_behavior == "block":
            # Block and poll for resolution
            engine.poll_resolution(
                escalation_id=record.id,
                timeout_seconds=matched_policy.timeout_seconds,
            )
        # 'proceed_with_flag' — continue execution, escalation logged for review

    def __exit__(self, exc_type, exc_val, exc_tb):
        stack = active_span_stack.get([])
        if stack and stack[-1][0] == self.span_id:
            stack.pop()

        if exc_type is not None:
            session = active_session_context.get(None)
            if session:
                node = session.replay_graph.nodes.get(self.span_id)
                if node:
                    node.output_data = f"Error: {exc_val}"
                duration_ms = int((time.time() - self.start_time) * 1000)
                self.client.emit_async(
                    {
                        "id": ulid.new().str,
                        "span_id": self.span_id,
                        "parent_span_id": self.parent_span_id,
                        "project_id": session.project_id,
                        "agent_id": session.agent_id,
                        "session_id": session.session_id,
                        "category": self.category,
                        "type": f"{self.category}.failed",
                        "name": self.name,
                        "payload": {
                            "error": {
                                "code": exc_type.__name__,
                                "message": str(exc_val),
                            }
                        },
                        "timestamp": time.time(),
                        "kind": self.category,
                        "label": self.name,
                        "content": {"input": safe_serialize(self.input_data), "error": str(exc_val), **self.content},
                        "confidence": 0.0,
                        "latency": duration_ms,
                        "duration": duration_ms,
                        # v2 fields
                        "confidence_value": 0.0,
                        "confidence_source": "unavailable",
                        "capabilities": self.capabilities + ["is_error"],
                    }
                )
        return False

    def complete(
        self, output_data: Any, metrics: Optional[Dict[str, Any]] = None
    ) -> IRRef:
        """
        Manually completes the span with output data and metrics.
        Returns a transparent IRRef tracking wrapper.
        """
        session = active_session_context.get(None)
        if session:
            node = session.replay_graph.nodes.get(self.span_id)
            if node:
                node.output_data = output_data

        if not session:
            return IRRef(output_data, self.span_id, "content")

        stack = active_span_stack.get([])
        if stack and stack[-1][0] == self.span_id:
            stack.pop()

        duration_ms = int((time.time() - self.start_time) * 1000)
        base_metrics: Dict[str, Any] = {"latency_ms": duration_ms, "cost_usd": 0.0}
        if metrics:
            base_metrics.update(metrics)

        self.client.emit_async(
            {
                "id": self.span_id,
                "parent_span_id": self.parent_span_id,
                "span_id": self.span_id,
                "project_id": session.project_id,
                "agent_id": session.agent_id,
                "session_id": session.session_id,
                "category": self.category,
                "type": f"{self.category}.completed",
                "name": self.name,
                "payload": {"output": safe_serialize(output_data)},
                "metrics": base_metrics,
                "timestamp": time.time(),
                "kind": self.category,
                "label": self.name,
                "content": {"input": safe_serialize(self.input_data), "output": safe_serialize(output_data), **self.content},
                "confidence": self.confidence,
                "uncertainty": self.uncertainty,
                "evidence": self.evidence,
                "assumptions": self.assumptions,
                "cost": base_metrics.get("cost_usd", 0.0),
                "latency": base_metrics.get("latency_ms", 0.0),
                "tokens": {
                    "input": base_metrics.get("tokens_input", 0),
                    "output": base_metrics.get("tokens_output", 0),
                },
                "duration": duration_ms,
                # v2 fields
                "confidence_value": self.confidence,
                "confidence_source": self.confidence_source,
                "confidence_method": self.confidence_method,
                "capabilities": self.capabilities,
            }
        )
        return IRRef(output_data, self.span_id, "content")
