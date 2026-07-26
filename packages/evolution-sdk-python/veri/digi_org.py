"""
VERI Digital Organization & Behavioral Economics — BehaviorOS v6.0

Models enterprise digital organizations where every employee role is an AI agent.
Manages organizational hierarchies and multi-budget economic allocations:

Multi-Budget System per Agent:
  - ComputeBudget     ──► CPU/GPU allocation
  - ReasoningBudget   ──► LLM token & reasoning depth cap
  - TrustBudget       ──► Autonomy level & permission radius
  - TokenBudget       ──► Daily token spend quota
  - FinancialBudget   ──► Real USD transaction authorization limit
"""

import time
from typing import List, Dict, Any, Optional


# ── Multi-Budget Economic Allocation ──────────────────────────────


class AgentBudgetBundle:
    """The complete multi-budget bundle allocated to an AI employee."""

    def __init__(
        self,
        compute_budget: float = 1.0,     # GPU/CPU cores
        reasoning_budget: int = 100000,   # Tokens
        trust_budget: float = 0.8,        # [0, 1] Trust radius
        financial_budget: float = 100.0,  # USD limit
    ):
        self.compute_budget = compute_budget
        self.reasoning_budget = reasoning_budget
        self.trust_budget = trust_budget
        self.financial_budget = financial_budget

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compute_budget_cores": self.compute_budget,
            "reasoning_budget_tokens": self.reasoning_budget,
            "trust_budget_radius": self.trust_budget,
            "financial_budget_usd": round(self.financial_budget, 2),
        }


# ── Digital Employee & Department ──────────────────────────────────


class DigitalEmployee:
    """An AI agent serving a formal role in a Digital Organization."""

    def __init__(
        self,
        employee_id: str,
        title: str,
        role: str,
        manager_id: Optional[str] = None,
        budget_bundle: Optional[AgentBudgetBundle] = None,
    ):
        self.employee_id = employee_id
        self.title = title
        self.role = role
        self.manager_id = manager_id
        self.budget_bundle = budget_bundle or AgentBudgetBundle()
        self.subordinates: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "title": self.title,
            "role": self.role,
            "manager_id": self.manager_id,
            "budget": self.budget_bundle.to_dict(),
            "subordinates_count": len(self.subordinates),
        }


class DigitalOrganization:
    """
    Complete Digital Organization hierarchy where departments, teams,
    managers, and employees are autonomous AI agents governed by BehaviorOS.
    """

    def __init__(self, org_id: str, name: str):
        self.org_id = org_id
        self.name = name
        self.employees: Dict[str, DigitalEmployee] = {}

    def add_employee(
        self,
        employee_id: str,
        title: str,
        role: str,
        manager_id: Optional[str] = None,
        financial_budget: float = 100.0,
    ) -> DigitalEmployee:
        """Adds a new AI employee to the digital org chart."""
        budget = AgentBudgetBundle(financial_budget=financial_budget)
        emp = DigitalEmployee(employee_id, title, role, manager_id, budget)

        if manager_id and manager_id in self.employees:
            self.employees[manager_id].subordinates.append(employee_id)

        self.employees[employee_id] = emp
        return emp

    def get_org_chart(self) -> Dict[str, Any]:
        """Returns the full hierarchical digital org chart."""
        return {
            "org_id": self.org_id,
            "name": self.name,
            "total_ai_employees": len(self.employees),
            "total_financial_budget_usd": sum(e.budget_bundle.financial_budget for e in self.employees.values()),
            "employees": [e.to_dict() for e in self.employees.values()],
        }
