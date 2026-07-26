"""
AutoGen Framework Adapter for VERI BehaviorOS.
Instruments AutoGen ConversableAgent turn exchanges and tool execution turns
into Runtime IR graphs with causal conversation lineages.
"""

import time
import functools
from typing import Any, Dict, Optional, Callable
from veri.ir import RuntimeNode, RuntimeEdge, NodeKind, Confidence
from veri.context import VERIContext


class VERIAutoGenAdapter:
    """Instruments AutoGen ConversableAgent message exchanges."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id

    def instrument_generate_reply(self, reply_func: Callable) -> Callable:
        @functools.wraps(reply_func)
        def wrapper(agent_self, messages=None, sender=None, *args, **kwargs):
            start_time = time.time()
            ctx = VERIContext.get_current()
            
            agent_name = getattr(agent_self, "name", "AutoGenAgent")
            sender_name = getattr(sender, "name", "User/Sender") if sender else "External"
            
            last_message = ""
            if messages and isinstance(messages, list) and len(messages) > 0:
                last_msg_item = messages[-1]
                last_message = last_msg_item.get("content", str(last_msg_item)) if isinstance(last_msg_item, dict) else str(last_msg_item)

            # Emit Observation / Input Node
            turn_node = RuntimeNode(
                kind=NodeKind.REASONING,
                label=f"AutoGen Turn: {sender_name} -> {agent_name}",
                content={
                    "sender": sender_name,
                    "recipient": agent_name,
                    "prompt_snippet": str(last_message)[:300]
                },
                confidence=Confidence.measured(0.9),
                agent_id=agent_name
            )
            
            parent_node = ctx.get_active_node()
            ctx.push_node(turn_node)
            
            if parent_node:
                ctx.add_edge(RuntimeEdge(
                    source_id=parent_node.id,
                    target_id=turn_node.id,
                    kind="depends_on"
                ))

            try:
                reply = reply_func(agent_self, messages=messages, sender=sender, *args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000.0
                
                reply_text = reply.get("content", str(reply)) if isinstance(reply, dict) else str(reply)
                
                # Emit Decision/Action Output Node
                reply_node = RuntimeNode(
                    kind=NodeKind.DECISION,
                    label=f"AutoGen Reply: {agent_name}",
                    content={"reply": str(reply_text)[:500]},
                    confidence=Confidence.measured(0.95),
                    latency=duration_ms,
                    agent_id=agent_name
                )
                ctx.push_node(reply_node)
                ctx.add_edge(RuntimeEdge(
                    source_id=turn_node.id,
                    target_id=reply_node.id,
                    kind="causes"
                ))
                return reply
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000.0
                error_node = RuntimeNode(
                    kind=NodeKind.ERROR,
                    label=f"AutoGen Exception: {type(e).__name__}",
                    content={"error": str(e)},
                    confidence=Confidence.measured(1.0),
                    latency=duration_ms,
                    agent_id=agent_name
                )
                ctx.push_node(error_node)
                ctx.add_edge(RuntimeEdge(
                    source_id=turn_node.id,
                    target_id=error_node.id,
                    kind="causes"
                ))
                raise e
            finally:
                ctx.pop_node()

        return wrapper


def patch_autogen(agent_class=None):
    """
    Auto-patches AutoGen ConversableAgent class or returns adapter instance.
    """
    adapter = VERIAutoGenAdapter()
    if agent_class and hasattr(agent_class, "generate_reply"):
        orig_reply = agent_class.generate_reply
        agent_class.generate_reply = adapter.instrument_generate_reply(orig_reply)
        return agent_class
    return adapter
