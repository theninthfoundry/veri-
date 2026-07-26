"""
CrewAI Framework Adapter for VERI BehaviorOS.
Automatically instruments CrewAI agents and tasks to compile execution paths
into structured Runtime IR subgraphs with confidence provenance.
"""

import time
import functools
from typing import Any, Dict, Optional, Callable
from veri.ir import RuntimeNode, RuntimeEdge, NodeKind, Confidence
from veri.context import VERIContext


class VERICrewAIAdapter:
    """Instruments CrewAI Agent and Task executions."""
    
    def __init__(self, agent_id: str = "crewai-agent"):
        self.agent_id = agent_id

    def instrument_task(self, task_func: Callable) -> Callable:
        @functools.wraps(task_func)
        def wrapper(task_self, *args, **kwargs):
            start_time = time.time()
            ctx = VERIContext.get_current()
            
            task_description = getattr(task_self, "description", str(task_self))
            agent_role = getattr(getattr(task_self, "agent", None), "role", "CrewAgent")
            
            # Emit Intent / Task Node
            task_node = RuntimeNode(
                kind=NodeKind.INTENT,
                label=f"CrewAI Task: {agent_role}",
                content={
                    "description": task_description,
                    "agent_role": agent_role,
                    "expected_output": str(getattr(task_self, "expected_output", ""))
                },
                confidence=Confidence.measured(1.0),
                agent_id=self.agent_id
            )
            
            parent_node = ctx.get_active_node()
            ctx.push_node(task_node)
            
            if parent_node:
                ctx.add_edge(RuntimeEdge(
                    source_id=parent_node.id,
                    target_id=task_node.id,
                    kind="decomposes_into"
                ))

            try:
                result = task_func(task_self, *args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000.0
                
                # Emit Outcome Node
                outcome_node = RuntimeNode(
                    kind=NodeKind.OUTCOME,
                    label=f"CrewAI Task Completed: {agent_role}",
                    content={"output": str(result)},
                    confidence=Confidence.measured(0.95),
                    latency=duration_ms,
                    agent_id=self.agent_id
                )
                ctx.push_node(outcome_node)
                ctx.add_edge(RuntimeEdge(
                    source_id=task_node.id,
                    target_id=outcome_node.id,
                    kind="causes"
                ))
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000.0
                error_node = RuntimeNode(
                    kind=NodeKind.ERROR,
                    label=f"CrewAI Task Failed: {type(e).__name__}",
                    content={"error": str(e)},
                    confidence=Confidence.measured(1.0),
                    latency=duration_ms,
                    agent_id=self.agent_id
                )
                ctx.push_node(error_node)
                ctx.add_edge(RuntimeEdge(
                    source_id=task_node.id,
                    target_id=error_node.id,
                    kind="causes"
                ))
                raise e
            finally:
                ctx.pop_node()

        return wrapper


def patch_crewai(target_class=None):
    """
    Auto-patches CrewAI Task class or wraps custom agent execution functions.
    """
    adapter = VERICrewAIAdapter()
    if target_class and hasattr(target_class, "execute_sync"):
        orig_execute = target_class.execute_sync
        target_class.execute_sync = adapter.instrument_task(orig_execute)
        return target_class
    return adapter
