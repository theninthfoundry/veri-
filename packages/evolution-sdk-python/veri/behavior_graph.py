"""
VERI Behavior Graph Engine - BehaviorOS v5.0

Unified Behavior Graph Engine that unifies raw execution traces into
a true cognitive knowledge, belief, and hypothesis graph.

Node Kinds:
  - belief, hypothesis, memory, goal, plan, evidence, constraint, tool, human

Edge Kinds:
  - supports, contradicts, causes, depends_on, influences, learned_from, evolved_into

This engine turns the trace graph itself into living intelligence.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind, EdgeKind


# -- Extended Cognitive Node & Edge Kinds ------------------------------------


class CognitiveNodeKind:
    BELIEF = "belief"
    HYPOTHESIS = "hypothesis"
    MEMORY = "memory"
    GOAL = "goal"
    PLAN = "plan"
    EVIDENCE = "evidence"
    CONSTRAINT = "constraint"
    TOOL = "tool"
    HUMAN = "human"


class CognitiveEdgeKind:
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CAUSES = "causes"
    DEPENDS_ON = "depends_on"
    INFLUENCES = "influences"
    LEARNED_FROM = "learned_from"
    EVOLVED_INTO = "evolved_into"


# -- Behavior Graph ---------------------------------------------------------


class BehaviorGraphNode:
    """A node in the unified cognitive behavior graph."""

    def __init__(
        self,
        node_id: str,
        kind: str,
        label: str,
        content: Optional[Dict[str, Any]] = None,
        confidence: float = 0.5,
    ):
        self.node_id = node_id
        self.kind = kind
        self.label = label
        self.content = content or {}
        self.confidence = max(0.0, min(1.0, confidence))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "kind": self.kind,
            "label": self.label,
            "content": self.content,
            "confidence": round(self.confidence, 4),
        }


class BehaviorGraphEdge:
    """A directed edge in the unified cognitive behavior graph."""

    def __init__(
        self,
        source_id: str,
        target_id: str,
        kind: str,
        weight: float = 1.0,
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.kind = kind
        self.weight = weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "kind": self.kind,
            "weight": round(self.weight, 4),
        }


class UnifiedBehaviorGraph:
    """
    Unified cognitive graph structure supporting complex belief, hypothesis,
    evidence, and contradiction networks.
    """

    def __init__(self):
        self.nodes: Dict[str, BehaviorGraphNode] = {}
        self.edges: List[BehaviorGraphEdge] = []
        self.adjacency: Dict[str, List[BehaviorGraphEdge]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[BehaviorGraphEdge]] = defaultdict(list)

    def add_node(self, node: BehaviorGraphNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: BehaviorGraphEdge) -> None:
        self.edges.append(edge)
        self.adjacency[edge.source_id].append(edge)
        self.reverse_adjacency[edge.target_id].append(edge)

    def ingest_runtime_nodes(
        self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]
    ) -> None:
        """Ingests raw RuntimeIR nodes and maps them into cognitive graph representations."""
        for n in nodes:
            cog_kind = self._map_kind(n.kind)
            cog_node = BehaviorGraphNode(
                node_id=n.id,
                kind=cog_kind,
                label=n.label,
                content=n.content,
                confidence=n.confidence if n.confidence is not None else 0.5,
            )
            self.add_node(cog_node)

        for e in edges:
            cog_edge_kind = self._map_edge_kind(e.kind)
            cog_edge = BehaviorGraphEdge(
                source_id=e.source,
                target_id=e.target,
                kind=cog_edge_kind,
                weight=e.weight if e.weight is not None else 1.0,
            )
            self.add_edge(cog_edge)

    def find_contradictions(self) -> List[Dict[str, Any]]:
        """Identifies contradicting belief/hypothesis edges in the cognitive graph."""
        contradictions = []
        for e in self.edges:
            if e.kind == CognitiveEdgeKind.CONTRADICTS:
                src_node = self.nodes.get(e.source_id)
                tgt_node = self.nodes.get(e.target_id)
                if src_node and tgt_node:
                    contradictions.append({
                        "source": src_node.to_dict(),
                        "target": tgt_node.to_dict(),
                        "weight": e.weight,
                        "explanation": f"Belief '{src_node.label}' contradicts '{tgt_node.label}'",
                    })
        return contradictions

    def get_supported_hypotheses(self, min_confidence: float = 0.7) -> List[BehaviorGraphNode]:
        """Returns hypotheses that have supporting evidence above min_confidence."""
        supported = []
        for nid, node in self.nodes.items():
            if node.kind == CognitiveNodeKind.HYPOTHESIS:
                incoming = self.reverse_adjacency.get(nid, [])
                has_support = any(
                    e.kind == CognitiveEdgeKind.SUPPORTS and self.nodes[e.source_id].confidence >= min_confidence
                    for e in incoming if e.source_id in self.nodes
                )
                if has_support:
                    supported.append(node)
        return supported

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "contradictions": self.find_contradictions(),
            "supported_hypotheses": [n.to_dict() for n in self.get_supported_hypotheses()],
        }

    # -- Internal Kind Mapping -----------------------------------------------

    def _map_kind(self, kind: str) -> str:
        mapping = {
            NodeKind.BELIEF: CognitiveNodeKind.BELIEF,
            NodeKind.REASONING: CognitiveNodeKind.HYPOTHESIS,
            NodeKind.OBSERVATION: CognitiveNodeKind.EVIDENCE,
            NodeKind.KNOWLEDGE: CognitiveNodeKind.MEMORY,
            NodeKind.INTENT: CognitiveNodeKind.GOAL,
            NodeKind.SUBGOAL: CognitiveNodeKind.GOAL,
            NodeKind.PLAN: CognitiveNodeKind.PLAN,
            NodeKind.CONSTRAINT: CognitiveNodeKind.CONSTRAINT,
            NodeKind.TOOL_INVOCATION: CognitiveNodeKind.TOOL,
            NodeKind.ACTION: CognitiveNodeKind.TOOL,
            NodeKind.ESCALATION: CognitiveNodeKind.HUMAN,
        }
        return mapping.get(kind, CognitiveNodeKind.BELIEF)

    def _map_edge_kind(self, kind: str) -> str:
        mapping = {
            EdgeKind.SUPPORTS: CognitiveEdgeKind.SUPPORTS,
            EdgeKind.REFUTES: CognitiveEdgeKind.CONTRADICTS,
            EdgeKind.CAUSES: CognitiveEdgeKind.CAUSES,
            EdgeKind.DEPENDS_ON: CognitiveEdgeKind.DEPENDS_ON,
            EdgeKind.LEARNS_FROM: CognitiveEdgeKind.LEARNED_FROM,
            EdgeKind.OPTIMIZES: CognitiveEdgeKind.EVOLVED_INTO,
        }
        return mapping.get(kind, CognitiveEdgeKind.INFLUENCES)
