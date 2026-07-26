"""
Multi-Stakeholder Intent Alignment Engine for VERI BehaviorOS.
Tracks goals and constraints across Agent, User, Policy, and Environment layers,
detecting pre-execution intent misalignments.
"""

from typing import List, Dict, Any, Optional


class Intent:
    """Represents a stakeholder's goal and operational boundaries."""
    def __init__(
        self,
        stakeholder: str,
        goal: str,
        priority: int = 1,
        constraints: Optional[List[str]] = None,
        max_budget: Optional[float] = None,
        max_time_seconds: Optional[float] = None
    ):
        self.stakeholder = stakeholder  # "agent", "user", "policy", "environment"
        self.goal = goal
        self.priority = priority
        self.constraints = constraints or []
        self.max_budget = max_budget
        self.max_time_seconds = max_time_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stakeholder": self.stakeholder,
            "goal": self.goal,
            "priority": self.priority,
            "constraints": self.constraints,
            "max_budget": self.max_budget,
            "max_time_seconds": self.max_time_seconds,
        }


class IntentConflict:
    """Represents a detected conflict between two stakeholder intents."""
    def __init__(self, between: List[str], description: str, severity: str, resolution: str):
        self.between = between
        self.description = description
        self.severity = severity  # "low", "medium", "high", "critical"
        self.resolution = resolution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "between": self.between,
            "description": self.description,
            "severity": self.severity,
            "resolution": self.resolution,
        }


class IntentAlignmentReport:
    """Evaluates total alignment across all stakeholder layers."""
    def __init__(self, aligned: bool, conflicts: List[IntentConflict], risk_score: float):
        self.aligned = aligned
        self.conflicts = conflicts
        self.risk_score = max(0.0, min(1.0, risk_score))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aligned": self.aligned,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "risk_score": self.risk_score,
        }


def align_intents(
    agent_intent: Intent,
    user_intent: Intent,
    policy_intent: Optional[Intent] = None,
    env_constraints: Optional[List[str]] = None
) -> IntentAlignmentReport:
    """
    Evaluates alignment between agent goal, user expectation, organizational policy, and environment reality.
    """
    conflicts = []

    # 1. Check budget conflict between Agent & User / Policy
    if agent_intent.max_budget and user_intent.max_budget:
        if agent_intent.max_budget > user_intent.max_budget:
            conflicts.append(IntentConflict(
                between=["agent", "user"],
                description=f"Agent planned budget (${agent_intent.max_budget}) exceeds user max budget limit (${user_intent.max_budget}).",
                severity="high",
                resolution="Cap agent sub-goal cost or prompt user for budget approval."
            ))

    # 2. Check keyword/constraint collisions
    env_list = env_constraints or []
    for c in user_intent.constraints:
        c_lower = c.lower()
        for env in env_list:
            if "blocked" in env.lower() and any(w in env.lower() for w in c_lower.split()):
                conflicts.append(IntentConflict(
                    between=["user", "environment"],
                    description=f"User constraint '{c}' collides with environment boundary '{env}'.",
                    severity="critical",
                    resolution="Re-route workflow to alternative path or notify user of environmental block."
                ))

    # 3. Check Policy rules vs Agent plan
    if policy_intent and policy_intent.constraints:
        for p_rule in policy_intent.constraints:
            if "forbidden" in p_rule.lower() and any(w in agent_intent.goal.lower() for w in p_rule.lower().split()):
                conflicts.append(IntentConflict(
                    between=["agent", "policy"],
                    description=f"Agent goal '{agent_intent.goal}' violates organizational policy constraint '{p_rule}'.",
                    severity="critical",
                    resolution="Halt tool execution and route for human manager escalation."
                ))

    aligned = (len(conflicts) == 0)
    risk = 0.0
    if len(conflicts) > 0:
        severities = [c.severity for c in conflicts]
        if "critical" in severities:
            risk = 0.95
        elif "high" in severities:
            risk = 0.70
        else:
            risk = 0.40

    return IntentAlignmentReport(aligned=aligned, conflicts=conflicts, risk_score=risk)
