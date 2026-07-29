"""
VERI Universal Runtime IR — Python representation.

Defines the core data structures for the Universal Runtime Intermediate Representation (Runtime IR).
All agent executions compile into this schema.
"""

import time
try:
    import ulid  # type: ignore # pyright: ignore[reportMissingImports]
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

from typing import Any, Dict, List, Optional


class NodeKind:
    # Intentional
    INTENT = "intent"
    SUBGOAL = "subgoal"
    PLAN = "plan"

    # Epistemic
    BELIEF = "belief"
    OBSERVATION = "observation"
    KNOWLEDGE = "knowledge"
    ASSUMPTION = "assumption"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"

    # Cognitive
    REASONING = "reasoning"
    DECISION = "decision"
    REFLECTION = "reflection"
    LEARNING = "learning"

    # Operational
    ACTION = "action"
    TOOL_INVOCATION = "tool_invocation"
    LLM_CALL = "llm_call"
    DELEGATION = "delegation"

    # Environmental
    WORLD_STATE = "world_state"
    CONSTRAINT = "constraint"
    RESOURCE = "resource"

    # Evaluative
    OUTCOME = "outcome"
    ERROR = "error"
    RISK = "risk"
    ANOMALY = "anomaly"

    # Accountability
    ESCALATION = "escalation"


class EdgeKind:
    CAUSES = "causes"
    CAUSED_BY = "caused_by"
    DEPENDS_ON = "depends_on"
    ENABLES = "enables"
    CONFLICTS_WITH = "conflicts_with"
    UPDATES = "updates"
    CONSTRAINS = "constrains"
    SUPPORTS = "supports"
    REFUTES = "refutes"
    DECOMPOSES_INTO = "decomposes_into"
    DELEGATES_TO = "delegates_to"
    LEARNS_FROM = "learns_from"
    PREDICTS = "predicts"
    OPTIMIZES = "optimizes"
    OBSERVES = "observes"
    ASSUMES = "assumes"
    REFLECTS_ON = "reflects_on"
    ESCALATES = "escalates"


class RuntimeNode:
    """
    A single node in the VERI Runtime IR graph.
    Represents an atomic semantic unit of agent state, perception, action, or intent.
    """

    def __init__(
        self,
        kind: str,
        label: str,
        agent_id: str,
        session_id: str,
        project_id: str,
        id: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        uncertainty: Optional[float] = None,
        evidence: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
        cost: float = 0.0,
        latency: float = 0.0,
        tokens: Optional[Dict[str, int]] = None,
        timestamp: Optional[float] = None,
        duration: Optional[float] = None,
    ):
        self.id = id or ulid.new().str
        self.kind = kind
        self.label = label
        self.content = content or {}
        self.confidence = confidence
        self.uncertainty = uncertainty
        self.evidence = evidence or []
        self.assumptions = assumptions or []
        self.cost = cost
        self.latency = latency
        self.tokens = tokens or {"input": 0, "output": 0}
        self.timestamp = timestamp or time.time()
        self.duration = duration
        self.agent_id = agent_id
        self.session_id = session_id
        self.project_id = project_id

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the node for ingestion gateway."""
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "content": self.content,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "evidence": self.evidence,
            "assumptions": self.assumptions,
            "cost": self.cost,
            "latency": self.latency,
            "tokens": self.tokens,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "project_id": self.project_id,
        }


class RuntimeEdge:
    """
    A directed, typed link between two RuntimeNodes.
    """

    def __init__(
        self,
        source: str = "",
        target: str = "",
        kind: str = "",
        session_id: Optional[str] = None,
        id: Optional[str] = None,
        weight: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
    ):
        self.id = id or ulid.new().str
        self.source = source_id if source_id is not None else source
        self.target = target_id if target_id is not None else target
        self.source_id = self.source
        self.target_id = self.target
        self.kind = kind
        self.session_id = session_id or ""
        self.weight = weight
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the edge for ingestion gateway."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "kind": self.kind,
            "session_id": self.session_id,
            "weight": self.weight,
            "metadata": self.metadata,
        }
