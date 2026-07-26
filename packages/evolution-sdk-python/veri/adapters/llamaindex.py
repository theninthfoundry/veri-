"""
LlamaIndex Framework Adapter for VERI BehaviorOS.
Tracks RAG retrievals, node score rankings, vector store queries, and response synthesis
into verified Knowledge Runtime IR nodes.
"""

import time
import functools
from typing import Any, Dict, List, Optional, Callable
from veri.ir import RuntimeNode, RuntimeEdge, NodeKind, Confidence
from veri.context import VERIContext


class VERILlamaIndexCallbackHandler:
    """Callback handler compatible with LlamaIndex event tracer API."""
    
    def __init__(self, agent_id: str = "llamaindex-retriever"):
        self.agent_id = agent_id

    def on_retrieve_start(self, query: str) -> RuntimeNode:
        ctx = VERIContext.get_current()
        node = RuntimeNode(
            kind=NodeKind.INTENT,
            label=f"LlamaIndex Retrieve: {query[:50]}",
            content={"query": query},
            confidence=Confidence.measured(1.0),
            agent_id=self.agent_id
        )
        ctx.push_node(node)
        return node

    def on_retrieve_end(self, parent_node: RuntimeNode, nodes: List[Any], duration_ms: float = 0.0):
        ctx = VERIContext.get_current()
        retrieved_summaries = []
        for idx, item in enumerate(nodes[:5]):
            text = getattr(item, "text", str(item))
            score = getattr(item, "score", 1.0)
            retrieved_summaries.append({"rank": idx + 1, "score": score, "snippet": text[:150]})
        
        kn_node = RuntimeNode(
            kind=NodeKind.KNOWLEDGE,
            label=f"LlamaIndex Retrieved ({len(nodes)} chunks)",
            content={"retrieved": retrieved_summaries},
            confidence=Confidence.measured(0.92),
            latency=duration_ms,
            agent_id=self.agent_id
        )
        ctx.push_node(kn_node)
        ctx.add_edge(RuntimeEdge(
            source_id=parent_node.id,
            target_id=kn_node.id,
            kind="retrieved_from"
        ))
        ctx.pop_node()


def patch_llamaindex(query_engine_class=None):
    """
    Wraps LlamaIndex query engine `query` calls to record retrieval and response synthesis.
    """
    handler = VERILlamaIndexCallbackHandler()
    
    def instrument_query(query_func: Callable) -> Callable:
        @functools.wraps(query_func)
        def wrapper(engine_self, str_or_query_bundle, *args, **kwargs):
            start = time.time()
            query_str = str(str_or_query_bundle)
            parent_node = handler.on_retrieve_start(query_str)
            
            try:
                response = query_func(engine_self, str_or_query_bundle, *args, **kwargs)
                duration_ms = (time.time() - start) * 1000.0
                
                source_nodes = getattr(response, "source_nodes", [])
                handler.on_retrieve_end(parent_node, source_nodes, duration_ms)
                
                ctx = VERIContext.get_current()
                synthesis_node = RuntimeNode(
                    kind=NodeKind.OUTCOME,
                    label="LlamaIndex Synthesis",
                    content={"response": str(response)[:500]},
                    confidence=Confidence.measured(0.95),
                    latency=duration_ms,
                    agent_id=handler.agent_id
                )
                ctx.push_node(synthesis_node)
                ctx.add_edge(RuntimeEdge(
                    source_id=parent_node.id,
                    target_id=synthesis_node.id,
                    kind="causes"
                ))
                return response
            except Exception as e:
                ctx = VERIContext.get_current()
                err_node = RuntimeNode(
                    kind=NodeKind.ERROR,
                    label=f"LlamaIndex Exception: {type(e).__name__}",
                    content={"error": str(e)},
                    confidence=Confidence.measured(1.0),
                    agent_id=handler.agent_id
                )
                ctx.push_node(err_node)
                ctx.add_edge(RuntimeEdge(
                    source_id=parent_node.id,
                    target_id=err_node.id,
                    kind="causes"
                ))
                raise e

        return wrapper

    if query_engine_class and hasattr(query_engine_class, "query"):
        query_engine_class.query = instrument_query(query_engine_class.query)
        return query_engine_class

    return instrument_query
