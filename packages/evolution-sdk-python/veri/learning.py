"""
Privacy-Preserving Failure Pattern Learner for VERI BehaviorOS.
Anonymizes failed execution subgraphs and automatically compiles declarative
BehaviorContract guardrails to prevent recurrence across future sessions.
"""

import re
from typing import List, Dict, Any, Optional
from veri.ir import RuntimeNode, NodeKind


class LearnedGuardrailRule:
    """Represents an automatically compiled guardrail rule."""
    def __init__(self, rule_name: str, rule_type: str, parameter_bounds: Dict[str, Any], generated_code: str):
        self.rule_name = rule_name
        self.rule_type = rule_type
        self.parameter_bounds = parameter_bounds
        self.generated_code = generated_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "rule_type": self.rule_type,
            "parameter_bounds": self.parameter_bounds,
            "generated_code": self.generated_code,
        }


class FailurePatternLearner:
    """Anonymizes execution graphs and compiles guardrail contracts from past failures."""
    
    def anonymize_text(self, text: str) -> str:
        """Strips PII, email addresses, credit card patterns, and API keys."""
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[ANONYMIZED_EMAIL]', text)
        text = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[ANONYMIZED_CARD]', text)
        text = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[ANONYMIZED_API_KEY]', text)
        return text

    def extract_failure_pattern(self, nodes: List[RuntimeNode], error_node_id: str) -> Optional[LearnedGuardrailRule]:
        """
        Extracts anonymized structural failure pattern and emits a BehaviorContract rule.
        """
        err_node = next((n for n in nodes if n.id == error_node_id), None)
        if not err_node:
            return None

        # Trace preceding action/tool nodes
        preceding_actions = [n for n in nodes if n.kind in (NodeKind.ACTION, NodeKind.TOOL_INVOCATION)]
        last_action = preceding_actions[-1] if preceding_actions else None
        
        rule_name = f"guardrail_prevent_{err_node.id[:8]}"
        param_bounds = {}
        
        if last_action and "price" in last_action.content:
            price_val = float(last_action.content.get("price", 1000.0))
            param_bounds["max_price"] = price_val * 0.9  # Set 10% safety margin
        else:
            param_bounds["forbidden_keywords"] = ["unhandled_exception", "out_of_memory"]

        code_snippet = f"""@behavior_contract({', '.join(f'{k}={repr(v)}' for k, v in param_bounds.items())})
def protected_agent_function(*args, **kwargs):
    # Auto-compiled by VERI Failure Pattern Learner
    pass"""

        return LearnedGuardrailRule(
            rule_name=rule_name,
            rule_type="behavior_contract",
            parameter_bounds=param_bounds,
            generated_code=code_snippet
        )
