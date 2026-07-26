import os
import logging
from typing import List, Optional
from .client import VeriClient as VeriClient
from .ir import NodeKind as NodeKind, EdgeKind as EdgeKind, RuntimeNode as RuntimeNode, RuntimeEdge as RuntimeEdge
from .ir_ref import IRRef as IRRef
from .escalation import (
    EscalationRequired as EscalationRequired,
    EscalationAborted as EscalationAborted,
    EscalationTimedOut as EscalationTimedOut,
    EscalationPolicy as EscalationPolicy,
    EscalationRecord as EscalationRecord,
    EscalationEngine as EscalationEngine,
    compute_approval_signature as compute_approval_signature,
    verify_approval_signature as verify_approval_signature,
)
from .fingerprint import RuntimeFingerprint as RuntimeFingerprint, capture_current_fingerprint as capture_current_fingerprint, compute_behavior_hash as compute_behavior_hash
from .contracts import BehaviorContract as BehaviorContract, ContractViolation as ContractViolation, behavior_contract as behavior_contract
from .lineage import BehaviorBOM as BehaviorBOM

# ── Submodules Re-exported for Pyright Type Checking ──
from . import prediction as prediction
from . import intent as intent
from . import compressor as compressor
from . import optimizer as optimizer
from . import simulation as simulation
from . import learning as learning
from . import bayesian as bayesian
from . import state_engine as state_engine
from . import causal as causal
from . import genome as genome
from . import physics as physics
from . import search as search
from . import fleet as fleet
from . import evolution as evolution
from . import kernel as kernel
from . import behavior_memory as behavior_memory
from . import behavior_db as behavior_db
from . import behavior_graph as behavior_graph
from . import scheduler as scheduler
from . import planner as planner
from . import compiler_v2 as compiler_v2
from . import behavior_models as behavior_models
from . import enterprise as enterprise
from . import ikernel as ikernel
from . import memory_manager as memory_manager
from . import ifs as ifs
from . import bproto as bproto
from . import bvm as bvm
from . import bcontainer as bcontainer
from . import ik8s as ik8s
from . import digi_org as digi_org
from . import civilization as civilization
from . import ci_runner as ci_runner
from . import adapters as adapters

# ── Intelligence Layer 4/5 ──
from .prediction import (
    Prediction as Prediction, run_predictive_analysis as run_predictive_analysis,
    EWMATracker as EWMATracker, MarkovTransitionModel as MarkovTransitionModel, PageHinkleyDetector as PageHinkleyDetector,
    compute_shannon_entropy as compute_shannon_entropy,
)
from .intent import Intent as Intent, IntentConflict as IntentConflict, IntentAlignmentReport as IntentAlignmentReport, align_intents as align_intents
from .compressor import RealityGraph as RealityGraph, StateDelta as StateDelta, compress_session as compress_session
from .optimizer import Optimization as Optimization, run_optimization_passes as run_optimization_passes, ParetoPoint as ParetoPoint

# ── Deep Intelligence Layer ──
from .simulation import CounterfactualSimulator as CounterfactualSimulator, SimulationResult as SimulationResult, SensitivityReport as SensitivityReport, MultiAblationResult as MultiAblationResult
from .learning import FailurePatternLearner as FailurePatternLearner, LearnedGuardrailRule as LearnedGuardrailRule
from .bayesian import BayesianEpistemicNetwork as BayesianEpistemicNetwork, BeliefState as BeliefState, ConditionalProbabilityTable as ConditionalProbabilityTable

# ── BehaviorOS v4.0 Intelligence Engines ──
from .state_engine import (
    BehavioralStateEngine as BehavioralStateEngine, CognitivePhase as CognitivePhase, StateTransition as StateTransition,
    CognitiveStateVector as CognitiveStateVector, CognitiveAnomaly as CognitiveAnomaly,
)
from .causal import (
    CausalReasoningEngine as CausalReasoningEngine, CausalGraph as CausalGraph, CausalStrength as CausalStrength,
    CausalLink as CausalLink, RootCause as RootCause, InterventionResult as InterventionResult,
)
from .genome import (
    BehaviorGenome as BehaviorGenome, extract_genome as extract_genome, compute_distance as compute_distance,
    classify_phenotype as classify_phenotype, detect_drift as detect_drift, get_trait_stability as get_trait_stability,
    DriftReport as DriftReport, TRAIT_NAMES as TRAIT_NAMES,
)
from .physics import (
    BehavioralPhysicsEngine as BehavioralPhysicsEngine, BehavioralState as BehavioralState, BehavioralForce as BehavioralForce,
    MomentumVector as MomentumVector, BehavioralEnergy as BehavioralEnergy, PhaseTransition as PhaseTransition, Attractor as Attractor,
)
from .search import (
    BehaviorSignature as BehaviorSignature, compute_signature as compute_signature, compute_similarity as compute_similarity,
    search_similar as search_similar, match_antipatterns as match_antipatterns, SignatureIndex as SignatureIndex,
    SearchResult as SearchResult, AntipatternMatch as AntipatternMatch,
)
from .fleet import (
    FleetIntelligenceEngine as FleetIntelligenceEngine, AgentTopology as AgentTopology, EmergentPattern as EmergentPattern,
    FleetHealthReport as FleetHealthReport, DelegationReport as DelegationReport, CollectiveDriftReport as CollectiveDriftReport,
)
from .evolution import (
    EvolutionEngine as EvolutionEngine, SessionOutcome as SessionOutcome, ImprovementRecommendation as ImprovementRecommendation,
    GenerationReport as GenerationReport,
)

# ── BehaviorOS v5.0 / v6.0 Operating System Subsystems ──
from .kernel import BehaviorKernel as BehaviorKernel, KernelStepResult as KernelStepResult
from .behavior_memory import BehavioralMemoryStore as BehavioralMemoryStore, BehavioralEpisode as BehavioralEpisode, EpisodeSearchResult as EpisodeSearchResult
from .behavior_db import BehavioralDatabase as BehavioralDatabase, BQLQueryResult as BQLQueryResult, SessionRecord as SessionRecord
from .behavior_graph import UnifiedBehaviorGraph as UnifiedBehaviorGraph, BehaviorGraphNode as BehaviorGraphNode, BehaviorGraphEdge as BehaviorGraphEdge, CognitiveNodeKind as CognitiveNodeKind, CognitiveEdgeKind as CognitiveEdgeKind
from .scheduler import BehaviorScheduler as BehaviorScheduler, AgentTask as AgentTask
from .planner import BehaviorPlanner as BehaviorPlanner, VerifiedPlan as VerifiedPlan, PlanStep as PlanStep
from .compiler_v2 import BehaviorCompilerV2 as BehaviorCompilerV2, CompiledDeploymentArtifact as CompiledDeploymentArtifact
from .behavior_models import FailurePredictionModel as FailurePredictionModel, PlanningOptimizationModel as PlanningOptimizationModel, AnomalyClassificationModel as AnomalyClassificationModel, RecoveryRecommendationModel as RecoveryRecommendationModel
from .enterprise import Organization as Organization, Workspace as Workspace, ComplianceAuditExporter as ComplianceAuditExporter

# ── BehaviorOS v6.0 The Intelligence Operating System ──
from .ikernel import IntelligenceKernel as IntelligenceKernel, BehaviorProcess as BehaviorProcess, ProcessState as ProcessState, ReasoningBudget as ReasoningBudget, ContextWindowAllotment as ContextWindowAllotment, ConcurrentThought as ConcurrentThought
from .memory_manager import HierarchicalMemoryManager as HierarchicalMemoryManager, MemoryLayer as MemoryLayer, MemoryItem as MemoryItem
from .ifs import IntelligenceFileSystem as IntelligenceFileSystem, KnowledgeObject as KnowledgeObject
from .bproto import BProtoSession as BProtoSession, BProtoPacket as BProtoPacket, BProtoMessageType as BProtoMessageType
from .bvm import BehaviorVirtualMachine as BehaviorVirtualMachine, BVMInstruction as BVMInstruction, BVMOpcode as BVMOpcode, BVMExecutionResult as BVMExecutionResult
from .bcontainer import BehaviorContainer as BehaviorContainer, BehaviorPackageManager as BehaviorPackageManager
from .ik8s import IntelligenceKubernetes as IntelligenceKubernetes, AgentPod as AgentPod
from .digi_org import DigitalOrganization as DigitalOrganization, DigitalEmployee as DigitalEmployee, AgentBudgetBundle as AgentBudgetBundle
from .civilization import CivilizationEngine as CivilizationEngine, CivilizationStatus as CivilizationStatus

__all__ = [
    "init", "get_client", "reset", "instrument", "session", "intelligence", "VeriClient",
    "NodeKind", "EdgeKind", "RuntimeNode", "RuntimeEdge", "IRRef",
    "EscalationRequired", "EscalationAborted", "EscalationTimedOut", "EscalationPolicy",
    "EscalationRecord", "EscalationEngine", "compute_approval_signature", "verify_approval_signature",
    "RuntimeFingerprint", "capture_current_fingerprint", "compute_behavior_hash",
    "BehaviorContract", "ContractViolation", "behavior_contract", "BehaviorBOM",
    "Prediction", "run_predictive_analysis", "EWMATracker", "MarkovTransitionModel",
    "PageHinkleyDetector", "compute_shannon_entropy",
    "Intent", "IntentConflict", "IntentAlignmentReport", "align_intents",
    "RealityGraph", "StateDelta", "compress_session",
    "Optimization", "run_optimization_passes", "ParetoPoint",
    "CounterfactualSimulator", "SimulationResult", "SensitivityReport", "MultiAblationResult",
    "FailurePatternLearner", "LearnedGuardrailRule",
    "BayesianEpistemicNetwork", "BeliefState", "ConditionalProbabilityTable",
    "BehavioralStateEngine", "CognitivePhase", "StateTransition", "CognitiveStateVector", "CognitiveAnomaly",
    "CausalReasoningEngine", "CausalGraph", "CausalStrength", "CausalLink", "RootCause", "InterventionResult",
    "BehaviorGenome", "extract_genome", "compute_distance", "classify_phenotype", "detect_drift", "get_trait_stability", "DriftReport", "TRAIT_NAMES",
    "BehavioralPhysicsEngine", "BehavioralState", "BehavioralForce", "MomentumVector", "BehavioralEnergy", "PhaseTransition", "Attractor",
    "BehaviorSignature", "compute_signature", "compute_similarity", "search_similar", "match_antipatterns", "SignatureIndex", "SearchResult", "AntipatternMatch",
    "FleetIntelligenceEngine", "AgentTopology", "EmergentPattern", "FleetHealthReport", "DelegationReport", "CollectiveDriftReport",
    "EvolutionEngine", "SessionOutcome", "ImprovementRecommendation", "GenerationReport",
    "BehaviorKernel", "KernelStepResult",
    "BehavioralMemoryStore", "BehavioralEpisode", "EpisodeSearchResult",
    "BehavioralDatabase", "BQLQueryResult", "SessionRecord",
    "UnifiedBehaviorGraph", "BehaviorGraphNode", "BehaviorGraphEdge", "CognitiveNodeKind", "CognitiveEdgeKind",
    "BehaviorScheduler", "AgentTask",
    "BehaviorPlanner", "VerifiedPlan", "PlanStep",
    "BehaviorCompilerV2", "CompiledDeploymentArtifact",
    "FailurePredictionModel", "PlanningOptimizationModel", "AnomalyClassificationModel", "RecoveryRecommendationModel",
    "Organization", "Workspace", "ComplianceAuditExporter",
    "IntelligenceKernel", "BehaviorProcess", "ProcessState", "ReasoningBudget", "ContextWindowAllotment", "ConcurrentThought",
    "HierarchicalMemoryManager", "MemoryLayer", "MemoryItem",
    "IntelligenceFileSystem", "KnowledgeObject",
    "BProtoSession", "BProtoPacket", "BProtoMessageType",
    "BehaviorVirtualMachine", "BVMInstruction", "BVMOpcode", "BVMExecutionResult",
    "BehaviorContainer", "BehaviorPackageManager",
    "IntelligenceKubernetes", "AgentPod",
    "DigitalOrganization", "DigitalEmployee", "AgentBudgetBundle",
    "CivilizationEngine", "CivilizationStatus",
    "prediction", "intent", "compressor", "optimizer", "simulation", "learning", "bayesian",
    "state_engine", "causal", "genome", "physics", "search", "fleet", "evolution",
    "kernel", "behavior_memory", "behavior_db", "behavior_graph", "scheduler", "planner",
    "compiler_v2", "behavior_models", "enterprise", "ikernel", "memory_manager", "ifs",
    "bproto", "bvm", "bcontainer", "ik8s", "digi_org", "civilization", "ci_runner", "adapters",
]

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
            line = line.split("#")[0].strip()
            if not line:
                continue
            section_match = re.match(r"^(\w+):$", line)
            if section_match:
                current_section = section_match.group(1)
                config[current_section] = {}
                continue
            indented_match = re.match(r"^(\w+):\s*([^\s]+)", line)
            if indented_match:
                k = indented_match.group(1)
                v = indented_match.group(2)
                if current_section:
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
    global _global_client, _global_escalation_engine

    if _global_client is not None:
        logger.warning("VERI SDK is already initialized. Skipping redundant initialization.")
        return

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
    global _global_client
    if _global_client is None:
        raise RuntimeError("VERI Runtime Client accessed before init() was invoked.")
    return _global_client


def reset() -> None:
    global _global_client, _global_escalation_engine
    if _global_client is not None:
        _global_client.shutdown()
        _global_client = None
    _global_escalation_engine = None


def instrument(frameworks: List[str]) -> None:
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


def intelligence(
    nodes: List[RuntimeNode],
    edges: List[RuntimeEdge],
    budget: float = 5.0,
    session_id: str = "",
) -> dict:
    state_engine = BehavioralStateEngine()
    state_engine.ingest_nodes(nodes)
    state_report = state_engine.to_dict()

    causal_engine = CausalReasoningEngine()
    causal_graph = causal_engine.build_causal_graph(nodes, edges)
    error_nodes = [n for n in nodes if n.kind == NodeKind.ERROR]
    root_causes = []
    for err in error_nodes[:3]:
        causes = causal_engine.find_root_causes(causal_graph, err.id, k=3)
        root_causes.extend([c.to_dict() for c in causes])

    genome = extract_genome(nodes, edges, session_id)

    physics_engine = BehavioralPhysicsEngine()
    physics_report = physics_engine.to_dict(nodes)

    predictions = run_predictive_analysis(nodes, budget)
    optimizations = run_optimization_passes(nodes, edges)

    signature = compute_signature(nodes, edges, session_id)
    antipatterns = match_antipatterns(signature)

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
