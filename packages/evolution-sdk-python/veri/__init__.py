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

# ── Intelligence Layer 4/5 (Rewritten with real mathematical foundations) ──
from .prediction import (
    Prediction, run_predictive_analysis,
    EWMATracker, MarkovTransitionModel, PageHinkleyDetector,
    compute_shannon_entropy,
)
from .intent import Intent, IntentConflict, IntentAlignmentReport, align_intents
from .compressor import RealityGraph, StateDelta, compress_session
from .optimizer import Optimization, run_optimization_passes, ParetoPoint

# ── Deep Intelligence Layer (Rewritten) ──
from .simulation import CounterfactualSimulator, SimulationResult, SensitivityReport, MultiAblationResult
from .learning import FailurePatternLearner, LearnedGuardrailRule
from .bayesian import BayesianEpistemicNetwork, BeliefState, ConditionalProbabilityTable

# ── BehaviorOS v4.0 Intelligence Engines ──
from .state_engine import (
    BehavioralStateEngine, CognitivePhase, StateTransition,
    CognitiveStateVector, CognitiveAnomaly,
)
from .causal import (
    CausalReasoningEngine, CausalGraph, CausalStrength,
    CausalLink, RootCause, InterventionResult,
)
from .genome import (
    BehaviorGenome, extract_genome, compute_distance,
    classify_phenotype, detect_drift, get_trait_stability,
    DriftReport, TRAIT_NAMES,
)
from .physics import (
    BehavioralPhysicsEngine, BehavioralState, BehavioralForce,
    MomentumVector, BehavioralEnergy, PhaseTransition, Attractor,
)
from .search import (
    BehaviorSignature, compute_signature, compute_similarity,
    search_similar, match_antipatterns, SignatureIndex,
    SearchResult, AntipatternMatch,
)
from .fleet import (
    FleetIntelligenceEngine, AgentTopology, EmergentPattern,
    FleetHealthReport, DelegationReport, CollectiveDriftReport,
)
from .evolution import (
    EvolutionEngine, SessionOutcome, ImprovementRecommendation,
    GenerationReport,
)

# ── BehaviorOS v5.0 / v6.0 Operating System Subsystems ──
from .kernel import BehaviorKernel, KernelStepResult
from .behavior_memory import BehavioralMemoryStore, BehavioralEpisode, EpisodeSearchResult
from .behavior_db import BehavioralDatabase, BQLQueryResult, SessionRecord
from .behavior_graph import UnifiedBehaviorGraph, BehaviorGraphNode, BehaviorGraphEdge, CognitiveNodeKind, CognitiveEdgeKind
from .scheduler import BehaviorScheduler, AgentTask
from .planner import BehaviorPlanner, VerifiedPlan, PlanStep
from .compiler_v2 import BehaviorCompilerV2, CompiledDeploymentArtifact
from .behavior_models import FailurePredictionModel, PlanningOptimizationModel, AnomalyClassificationModel, RecoveryRecommendationModel
from .enterprise import Organization, Workspace, ComplianceAuditExporter

# ── BehaviorOS v6.0 The Intelligence Operating System ──
from .ikernel import IntelligenceKernel, BehaviorProcess, ProcessState, ReasoningBudget, ContextWindowAllotment, ConcurrentThought
from .memory_manager import HierarchicalMemoryManager, MemoryLayer, MemoryItem
from .ifs import IntelligenceFileSystem, KnowledgeObject
from .bproto import BProtoSession, BProtoPacket, BProtoMessageType
from .bvm import BehaviorVirtualMachine, BVMInstruction, BVMOpcode, BVMExecutionResult
from .bcontainer import BehaviorContainer, BehaviorPackageManager
from .ik8s import IntelligenceKubernetes, AgentPod
from .digi_org import DigitalOrganization, DigitalEmployee, AgentBudgetBundle
from .civilization import CivilizationEngine, CivilizationStatus




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


# ── BehaviorOS v4.0 Intelligence Pipeline ─────────────────────────


def intelligence(
    nodes: List[RuntimeNode],
    edges: List[RuntimeEdge],
    budget: float = 5.0,
    session_id: str = "",
) -> dict:
    """
    Runs the full BehaviorOS v4.0 intelligence pipeline in a single call.

    Returns a comprehensive intelligence report from all 7 engines:
      - state: Cognitive state machine analysis
      - causal: Causal reasoning and root cause analysis
      - genome: Behavioral DNA extraction
      - physics: Behavioral dynamics and forces
      - predictions: Adaptive anomaly predictions
      - optimizations: Compiler optimization opportunities
      - search: Anti-pattern matching
      - beliefs: Bayesian belief propagation
    """
    # 1. Behavioral State Engine
    state_engine = BehavioralStateEngine()
    state_engine.ingest_nodes(nodes)
    state_report = state_engine.to_dict()

    # 2. Causal Reasoning Engine
    causal_engine = CausalReasoningEngine()
    causal_graph = causal_engine.build_causal_graph(nodes, edges)
    # Find error nodes for root cause analysis
    error_nodes = [n for n in nodes if n.kind == NodeKind.ERROR]
    root_causes = []
    for err in error_nodes[:3]:  # Analyze top 3 errors
        causes = causal_engine.find_root_causes(causal_graph, err.id, k=3)
        root_causes.extend([c.to_dict() for c in causes])

    # 3. Behavior Genome
    genome = extract_genome(nodes, edges, session_id)

    # 4. Behavioral Physics
    physics_engine = BehavioralPhysicsEngine()
    physics_report = physics_engine.to_dict(nodes)

    # 5. Predictions
    predictions = run_predictive_analysis(nodes, budget)

    # 6. Optimizations
    optimizations = run_optimization_passes(nodes, edges)

    # 7. Behavioral Search (anti-pattern matching)
    signature = compute_signature(nodes, edges, session_id)
    antipatterns = match_antipatterns(signature)

    # 8. Bayesian Beliefs
    bayesian = BayesianEpistemicNetwork()
    belief_states = bayesian.propagate_beliefs(nodes, edges)

    return {
        "state": state_report,
        "causal": {
            "root_causes": root_causes,
            "graph_size": len(causal_graph.nodes),
        },
        "genome": genome.to_dict(),
        "physics": physics_report,
        "predictions": [p.to_dict() for p in predictions],
        "optimizations": [o.to_dict() for o in optimizations],
        "antipatterns": [a.to_dict() for a in antipatterns],
        "beliefs": {
            nid: bs.to_dict() for nid, bs in list(belief_states.items())[:20]
        },
    }
