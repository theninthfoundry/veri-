"""
Multi-Pass Runtime Optimization Compiler for VERI BehaviorOS.
Performs static graph analysis over agent execution graphs to identify cost,
latency, and quality optimization opportunities.
"""

from typing import List, Dict, Any, Optional
from veri.ir import RuntimeNode, RuntimeEdge, NodeKind


class Optimization:
    """Represents a calculated graph optimization opportunity."""
    def __init__(
        self,
        optimization_type: str,
        description: str,
        cost_reduction: float,
        latency_reduction: float,
        confidence: float,
        suggestion: str,
        affected_nodes: List[str]
    ):
        self.optimization_type = optimization_type
        self.description = description
        self.cost_reduction = cost_reduction
        self.latency_reduction = latency_reduction
        self.confidence = confidence
        self.suggestion = suggestion
        self.affected_nodes = affected_nodes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "optimization_type": self.optimization_type,
            "description": self.description,
            "impact": {
                "cost_reduction": self.cost_reduction,
                "latency_reduction": self.latency_reduction,
            },
            "confidence": self.confidence,
            "suggestion": self.suggestion,
            "affected_nodes": self.affected_nodes,
        }


class RedundantReasoningPass:
    """Detects when an agent reasons about the same topic multiple times without new observations."""
    def analyze(self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]) -> List[Optimization]:
        opts = []
        reasoning_nodes = [n for n in nodes if n.kind in (NodeKind.REASONING, NodeKind.REFLECTION)]
        
        for i in range(1, len(reasoning_nodes)):
            prev = reasoning_nodes[i - 1]
            curr = reasoning_nodes[i]
            if prev.label == curr.label:
                opts.append(Optimization(
                    optimization_type="redundant_reasoning",
                    description=f"Reasoning step '{curr.label}' is identical to earlier step without new observation data.",
                    cost_reduction=curr.cost or 0.002,
                    latency_reduction=curr.latency or 350.0,
                    confidence=0.90,
                    suggestion=f"Cache output of '{prev.label}' and skip re-reasoning when state is unchanged.",
                    affected_nodes=[prev.id, curr.id]
                ))
        return opts


class UnnecessaryRetrievalPass:
    """Identifies memory/RAG retrieval calls whose data was never referenced downstream."""
    def analyze(self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]) -> List[Optimization]:
        opts = []
        knowledge_nodes = [n for n in nodes if n.kind in (NodeKind.KNOWLEDGE, NodeKind.OBSERVATION)]
        
        # Check if knowledge node ID is in any downstream edge source
        edge_sources = set(e.source_id for e in edges)
        for k in knowledge_nodes:
            if k.id not in edge_sources:
                opts.append(Optimization(
                    optimization_type="unnecessary_retrieval",
                    description=f"Knowledge retrieval '{k.label}' was fetched but never consumed downstream.",
                    cost_reduction=k.cost or 0.001,
                    latency_reduction=k.latency or 150.0,
                    confidence=0.85,
                    suggestion=f"Defer or eliminate retrieval '{k.label}' unless requested by active sub-goal.",
                    affected_nodes=[k.id]
                ))
        return opts


class SerialParallelizablePass:
    """Detects adjacent independent tool invocations that lack mutual dependencies."""
    def analyze(self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]) -> List[Optimization]:
        opts = []
        tool_nodes = [n for n in nodes if n.kind in (NodeKind.TOOL_INVOCATION, NodeKind.ACTION)]
        
        if len(tool_nodes) >= 2:
            for i in range(len(tool_nodes) - 1):
                t1 = tool_nodes[i]
                t2 = tool_nodes[i + 1]
                # Check if t2 depends on t1
                dependent = any(e.source_id == t1.id and e.target_id == t2.id for e in edges)
                if not dependent:
                    savings_ms = min(t1.latency or 200.0, t2.latency or 200.0)
                    opts.append(Optimization(
                        optimization_type="serial_parallelizable",
                        description=f"Tool invocations '{t1.label}' and '{t2.label}' run sequentially but have no data dependency.",
                        cost_reduction=0.0,
                        latency_reduction=savings_ms,
                        confidence=0.80,
                        suggestion=f"Execute '{t1.label}' and '{t2.label}' concurrently in asyncio.gather().",
                        affected_nodes=[t1.id, t2.id]
                    ))
        return opts


class DeadBranchPass:
    """Prunes execution branches that ended in unhandled errors or abandoned sub-goals."""
    def analyze(self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]) -> List[Optimization]:
        opts = []
        error_nodes = [n for n in nodes if n.kind == NodeKind.ERROR]
        for err in error_nodes:
            opts.append(Optimization(
                optimization_type="dead_branch",
                description=f"Execution path led to unrecovered error '{err.label}'.",
                cost_reduction=err.cost or 0.003,
                latency_reduction=err.latency or 500.0,
                confidence=0.95,
                suggestion="Prune dead-end planning path and add pre-execution contract guardrail.",
                affected_nodes=[err.id]
            ))
        return opts


def run_optimization_passes(nodes: List[RuntimeNode], edges: List[RuntimeEdge]) -> List[Optimization]:
    """Runs all 4 static optimization passes over an execution graph."""
    all_opts = []
    
    passes = [
        RedundantReasoningPass(),
        UnnecessaryRetrievalPass(),
        SerialParallelizablePass(),
        DeadBranchPass(),
    ]

    for p in passes:
        all_opts.extend(p.analyze(nodes, edges))

    return all_opts
