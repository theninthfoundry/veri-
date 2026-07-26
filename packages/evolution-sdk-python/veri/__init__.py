import os
import logging
from typing import List, Optional
from .client import VeriClient
from .ir import NodeKind, EdgeKind, RuntimeNode, RuntimeEdge
from .ir_ref import IRRef
from .escalation import (
    EscalationRequired,
    EscalationAborted,
    EscalationTimedOut,
    EscalationPolicy,
    EscalationRecord,
    EscalationEngine,
    compute_approval_signature,
    verify_approval_signature,
)
from .fingerprint import RuntimeFingerprint, capture_current_fingerprint, compute_behavior_hash
from .contracts import BehaviorContract, ContractViolation, behavior_contract
from .lineage import BehaviorBOM
from .prediction import Prediction, run_predictive_analysis
from .intent import Intent, IntentConflict, IntentAlignmentReport, align_intents
from .compressor import RealityGraph, StateDelta, compress_session
from .optimizer import Optimization, run_optimization_passes
from .simulation import CounterfactualSimulator, SimulationResult
from .learning import FailurePatternLearner, LearnedGuardrailRule
from .bayesian import BayesianEpistemicNetwork

logger = logging.getLogger("veri")

_global_client: Optional[VeriClient] = None
_global_escalation_engine: Optional[EscalationEngine] = None


def _load_yaml_config(path: str) -> dict:
    config = {}
    if not os.path.exists(path):
        return config
    import re
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        current_section = None
        for line in lines:
            # Strip comments and whitespace
            line = line.split("#")[0].strip()
            if not line:
                continue
            
            # Match top-level sections like "guardrails:"
            section_match = re.match(r"^(\w+):$", line)
            if section_match:
                current_section = section_match.group(1)
                config[current_section] = {}
                continue
            
            # Match indented keys under a section
            indented_match = re.match(r"^(\w+):\s*([^\s]+)", line)
            if indented_match:
                k = indented_match.group(1)
                v = indented_match.group(2)
                
                # Check for nested values if we are inside a section
                if current_section:
                    # Clean quotes and parse numeric values
                    try:
                        if "." in v:
                            v = float(v)
                        else:
                            v = int(v)
                    except ValueError:
                        v = v.strip("'\"")
                    config[current_section][k] = v
                else:
                    config[k] = v
    except Exception as e:
        logger.warning("Failed to load veri.yaml: %s", str(e))
    return config


def init(
    api_key: Optional[str] = None,
    endpoint: str = "http://localhost:8080/api/v1/ingest",
    gateway_endpoint: str = "http://localhost:8080",
    cost_limit: float = 5.00,
    call_limit: int = 100,
    disabled: bool = False,
    escalation_enabled: bool = True,
) -> None:
    """
    Initializes the global VERI runtime client.
    Loads settings from veri.yaml in the working directory if present.

    Args:
        api_key: VERI API key. Falls back to VERI_API_KEY env var.
        endpoint: Gateway ingest URL.
        gateway_endpoint: Gateway base URL (for escalation policy loading, etc.).
        cost_limit: Maximum USD spend per session before L0 kill-switch.
        call_limit: Maximum LLM calls per session before L0 kill-switch.
        disabled: If True, SDK is inert — no events emitted, no guardrails.
        escalation_enabled: If True, load and enforce escalation policies.
    """
    global _global_client, _global_escalation_engine

    if _global_client is not None:
        logger.warning("VERI SDK is already initialized. Skipping redundant initialization.")
        return

    # Attempt to load from veri.yaml configuration
    local_config = _load_yaml_config("veri.yaml")
    guardrail_config = local_config.get("guardrails", {})
    
    effective_cost_limit = guardrail_config.get("cost_limit", cost_limit)
    effective_call_limit = guardrail_config.get("call_limit", call_limit)

    effective_key = api_key or os.getenv("VERI_API_KEY")
    if not effective_key and not disabled:
        raise ValueError(
            "Initialization failed: VERI_API_KEY must be provided or set via environment variable."
        )

    _global_client = VeriClient(
        api_key=effective_key or "disabled_key",
        endpoint=endpoint,
        cost_limit=effective_cost_limit,
        call_limit=effective_call_limit,
        disabled=disabled,
    )

    # Initialize Escalation Engine
    _global_escalation_engine = EscalationEngine(
        gateway_endpoint=gateway_endpoint,
        api_key=effective_key or "disabled_key",
        enabled=escalation_enabled and not disabled,
    )

    logger.info(
        "VERI SDK initialized (cost_limit=%s, call_limit=%s, escalation=%s) — capture loop active.",
        effective_cost_limit,
        effective_call_limit,
        "enabled" if escalation_enabled else "disabled",
    )


def get_client() -> VeriClient:
    """Returns the global VeriClient. Raises if init() was not called."""
    global _global_client
    if _global_client is None:
        raise RuntimeError("VERI Runtime Client accessed before init() was invoked.")
    return _global_client


def reset() -> None:
    """Tears down the global client. Useful for testing."""
    global _global_client, _global_escalation_engine
    if _global_client is not None:
        _global_client.shutdown()
        _global_client = None
    _global_escalation_engine = None


def instrument(frameworks: List[str]) -> None:
    """
    Applies auto-instrumentation hooks across target frameworks.

    Supported frameworks: "openai", "langchain", "crewai", "autogen", "llamaindex"
    """
    from .patching import patch_runtime
    from .adapters import patch_crewai, patch_autogen, patch_llamaindex

    client = get_client()
    if client.disabled:
        return
    for framework in frameworks:
        fw_lower = framework.lower()
        if fw_lower == "crewai":
            patch_crewai()
        elif fw_lower == "autogen":
            patch_autogen()
        elif fw_lower == "llamaindex":
            patch_llamaindex()
        else:
            patch_runtime(framework, client)



def session(session_id: str, agent_id: str, project_id: str):
    """Shorthand context manager for creating a tracked agent session."""
    client = get_client()
    from .context import AgentSessionContext
    return AgentSessionContext(
        client=client,
        session_id=session_id,
        agent_id=agent_id,
        project_id=project_id,
        cost_limit=client.cost_limit,
        call_limit=client.call_limit,
        escalation_engine=_global_escalation_engine,
    )
