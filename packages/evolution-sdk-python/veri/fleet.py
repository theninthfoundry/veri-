"""
VERI Fleet Intelligence Engine — BehaviorOS v4.0

Cross-agent organizational intelligence:
  - Inter-agent communication topology mapping
  - Emergent pattern detection (cascading failures, load imbalance)
  - Aggregate fleet behavioral health scoring
  - Delegation efficiency analysis
  - Collective behavioral drift detection

This engine answers: "How do agents behave as an ORGANIZATION, not just individually?"
"""

import math
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter, defaultdict

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind
from veri.genome import BehaviorGenome, compute_distance, TRAIT_NAMES


# ── Data Structures ────────────────────────────────────────────────


class AgentTopology:
    """Directed graph of delegation/communication between agents."""

    def __init__(self):
        self.agents: Set[str] = set()
        self.edges: Dict[Tuple[str, str], int] = defaultdict(int)  # (from, to) → count
        self.delegation_count: Dict[str, int] = defaultdict(int)
        self.receive_count: Dict[str, int] = defaultdict(int)

    def add_delegation(self, from_agent: str, to_agent: str) -> None:
        self.agents.add(from_agent)
        self.agents.add(to_agent)
        self.edges[(from_agent, to_agent)] += 1
        self.delegation_count[from_agent] += 1
        self.receive_count[to_agent] += 1

    @property
    def agent_count(self) -> int:
        return len(self.agents)

    @property
    def edge_count(self) -> int:
        return sum(self.edges.values())

    def get_hub_agents(self, top_k: int = 3) -> List[Tuple[str, int]]:
        """Agents with highest combined delegation + receive activity."""
        activity = {
            a: self.delegation_count[a] + self.receive_count[a]
            for a in self.agents
        }
        return sorted(activity.items(), key=lambda x: x[1], reverse=True)[:top_k]

    def get_bottleneck_agents(self) -> List[Tuple[str, float]]:
        """Agents receiving disproportionate delegation load."""
        if not self.agents:
            return []
        avg_receive = sum(self.receive_count.values()) / max(1, len(self.agents))
        bottlenecks = [
            (a, count / max(1.0, avg_receive))
            for a, count in self.receive_count.items()
            if count > avg_receive * 1.5
        ]
        return sorted(bottlenecks, key=lambda x: x[1], reverse=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_count": self.agent_count,
            "edge_count": self.edge_count,
            "agents": sorted(self.agents),
            "edges": [
                {"from": f, "to": t, "count": c}
                for (f, t), c in sorted(self.edges.items(), key=lambda x: x[1], reverse=True)
            ],
            "hub_agents": [{"agent": a, "activity": c} for a, c in self.get_hub_agents()],
            "bottleneck_agents": [{"agent": a, "load_ratio": round(r, 2)} for a, r in self.get_bottleneck_agents()],
        }


class EmergentPattern:
    """A behavioral pattern only visible at the fleet level."""

    def __init__(
        self,
        pattern_type: str,
        severity: str,
        agents_involved: List[str],
        description: str,
        evidence: Dict[str, Any],
    ):
        self.pattern_type = pattern_type
        self.severity = severity
        self.agents_involved = agents_involved
        self.description = description
        self.evidence = evidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "severity": self.severity,
            "agents_involved": self.agents_involved,
            "description": self.description,
            "evidence": self.evidence,
        }


class FleetHealthReport:
    """Aggregate behavioral health across all agents."""

    def __init__(
        self,
        overall_score: float,
        agent_scores: Dict[str, float],
        behavioral_diversity: float,
        avg_genome_distance: float,
        weakest_agents: List[Tuple[str, float]],
        strongest_agents: List[Tuple[str, float]],
    ):
        self.overall_score = overall_score
        self.agent_scores = agent_scores
        self.behavioral_diversity = behavioral_diversity
        self.avg_genome_distance = avg_genome_distance
        self.weakest_agents = weakest_agents
        self.strongest_agents = strongest_agents

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 3),
            "agent_scores": {k: round(v, 3) for k, v in self.agent_scores.items()},
            "behavioral_diversity": round(self.behavioral_diversity, 3),
            "avg_genome_distance": round(self.avg_genome_distance, 3),
            "weakest_agents": [
                {"agent": a, "score": round(s, 3)} for a, s in self.weakest_agents
            ],
            "strongest_agents": [
                {"agent": a, "score": round(s, 3)} for a, s in self.strongest_agents
            ],
        }


class DelegationReport:
    """Analysis of multi-agent task decomposition quality."""

    def __init__(
        self,
        efficiency_score: float,
        bottleneck_agents: List[str],
        underutilized_agents: List[str],
        delegation_loops: int,
        explanation: str,
    ):
        self.efficiency_score = efficiency_score
        self.bottleneck_agents = bottleneck_agents
        self.underutilized_agents = underutilized_agents
        self.delegation_loops = delegation_loops
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "efficiency_score": round(self.efficiency_score, 3),
            "bottleneck_agents": self.bottleneck_agents,
            "underutilized_agents": self.underutilized_agents,
            "delegation_loops": self.delegation_loops,
            "explanation": self.explanation,
        }


class CollectiveDriftReport:
    """Fleet-wide behavioral shift detection."""

    def __init__(
        self,
        is_drifting: bool,
        drift_direction: Dict[str, float],
        affected_agents: List[str],
        magnitude: float,
        explanation: str,
    ):
        self.is_drifting = is_drifting
        self.drift_direction = drift_direction
        self.affected_agents = affected_agents
        self.magnitude = magnitude
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_drifting": self.is_drifting,
            "drift_direction": {k: round(v, 4) for k, v in self.drift_direction.items()},
            "affected_agents": self.affected_agents,
            "magnitude": round(self.magnitude, 4),
            "explanation": self.explanation,
        }


# ── Fleet Intelligence Engine ────────────────────────────────────


class FleetIntelligenceEngine:
    """Cross-agent organizational intelligence engine."""

    def build_topology(
        self, sessions: List[Dict[str, Any]]
    ) -> AgentTopology:
        """
        Construct inter-agent communication graph from session data.

        Each session dict should have:
          - "agent_id": str
          - "nodes": List[RuntimeNode]
        """
        topology = AgentTopology()

        for session in sessions:
            agent_id = session.get("agent_id", "unknown")
            nodes = session.get("nodes", [])
            topology.agents.add(agent_id)

            for node in nodes:
                if isinstance(node, RuntimeNode):
                    if node.kind == NodeKind.DELEGATION:
                        # Extract target agent from content or label
                        target_agent = node.content.get("target_agent", node.label)
                        if target_agent and target_agent != agent_id:
                            topology.add_delegation(agent_id, target_agent)

        return topology

    def detect_emergent_patterns(
        self,
        topology: AgentTopology,
        agent_genomes: Dict[str, BehaviorGenome],
    ) -> List[EmergentPattern]:
        """Detect patterns visible only at fleet level."""
        patterns: List[EmergentPattern] = []

        # 1. Cascading failure: delegation chain where errors propagate
        bottlenecks = topology.get_bottleneck_agents()
        if bottlenecks:
            for agent, load_ratio in bottlenecks:
                if load_ratio > 2.0:
                    patterns.append(EmergentPattern(
                        pattern_type="bottleneck_overload",
                        severity="high",
                        agents_involved=[agent],
                        description=(
                            f"Agent '{agent}' receiving {load_ratio:.1f}x average delegation load. "
                            f"Single point of failure risk."
                        ),
                        evidence={"load_ratio": load_ratio, "receive_count": topology.receive_count[agent]},
                    ))

        # 2. Load imbalance: some agents overworked, others idle
        if topology.agents and len(topology.agents) > 2:
            activities = {
                a: topology.delegation_count.get(a, 0) + topology.receive_count.get(a, 0)
                for a in topology.agents
            }
            if activities:
                max_activity = max(activities.values())
                min_activity = min(activities.values())
                if max_activity > 0 and min_activity == 0:
                    idle_agents = [a for a, v in activities.items() if v == 0]
                    patterns.append(EmergentPattern(
                        pattern_type="load_imbalance",
                        severity="medium",
                        agents_involved=idle_agents,
                        description=(
                            f"{len(idle_agents)} agents have zero activity while others are heavily loaded. "
                            f"Delegation strategy may need rebalancing."
                        ),
                        evidence={"idle_agents": idle_agents, "max_activity": max_activity},
                    ))

        # 3. Behavioral monoculture: all agents have very similar genomes
        if len(agent_genomes) >= 3:
            genome_list = list(agent_genomes.values())
            distances = []
            for i in range(len(genome_list)):
                for j in range(i + 1, len(genome_list)):
                    distances.append(compute_distance(genome_list[i], genome_list[j]))
            if distances:
                avg_distance = sum(distances) / len(distances)
                if avg_distance < 0.15:
                    patterns.append(EmergentPattern(
                        pattern_type="behavioral_monoculture",
                        severity="medium",
                        agents_involved=list(agent_genomes.keys()),
                        description=(
                            f"All {len(agent_genomes)} agents exhibit highly similar behavioral patterns "
                            f"(avg genome distance: {avg_distance:.3f}). "
                            f"Fleet lacks behavioral diversity for resilience."
                        ),
                        evidence={"avg_genome_distance": avg_distance},
                    ))

        return patterns

    def compute_fleet_health(
        self, agent_genomes: Dict[str, BehaviorGenome]
    ) -> FleetHealthReport:
        """Aggregate behavioral health across all agents."""
        if not agent_genomes:
            return FleetHealthReport(
                overall_score=0.0, agent_scores={}, behavioral_diversity=0.0,
                avg_genome_distance=0.0, weakest_agents=[], strongest_agents=[],
            )

        # Per-agent health score: weighted combination of positive traits
        agent_scores: Dict[str, float] = {}
        for agent_id, genome in agent_genomes.items():
            t = genome.traits
            score = (
                t["cost_efficiency"] * 0.20
                + t["confidence_calibration"] * 0.20
                + t["recovery_speed"] * 0.15
                + t["decisiveness"] * 0.15
                + t["focus_persistence"] * 0.10
                + t["learning_rate"] * 0.10
                + (1.0 - t["risk_tolerance"]) * 0.10  # Lower risk = healthier
            )
            agent_scores[agent_id] = score

        overall = sum(agent_scores.values()) / len(agent_scores)

        # Behavioral diversity: average pairwise genome distance
        genome_list = list(agent_genomes.values())
        distances = []
        for i in range(len(genome_list)):
            for j in range(i + 1, len(genome_list)):
                distances.append(compute_distance(genome_list[i], genome_list[j]))
        avg_distance = sum(distances) / max(1, len(distances))
        diversity = min(1.0, avg_distance * 3.0)  # Normalize

        sorted_scores = sorted(agent_scores.items(), key=lambda x: x[1])
        weakest = sorted_scores[:3]
        strongest = sorted_scores[-3:][::-1]

        return FleetHealthReport(
            overall_score=overall,
            agent_scores=agent_scores,
            behavioral_diversity=diversity,
            avg_genome_distance=avg_distance,
            weakest_agents=weakest,
            strongest_agents=strongest,
        )

    def analyze_delegation_efficiency(
        self, topology: AgentTopology
    ) -> DelegationReport:
        """Measure whether multi-agent task decomposition is optimal."""
        if not topology.agents:
            return DelegationReport(
                efficiency_score=1.0, bottleneck_agents=[], underutilized_agents=[],
                delegation_loops=0, explanation="No agents in topology.",
            )

        # Detect delegation loops (A→B→A)
        loops = 0
        for (a, b), count_ab in topology.edges.items():
            count_ba = topology.edges.get((b, a), 0)
            if count_ab > 0 and count_ba > 0:
                loops += 1

        # Identify bottlenecks and underutilized
        avg_receive = sum(topology.receive_count.values()) / max(1, len(topology.agents))
        bottlenecks = [a for a in topology.agents if topology.receive_count.get(a, 0) > avg_receive * 1.5]
        underutilized = [a for a in topology.agents if topology.receive_count.get(a, 0) == 0 and topology.delegation_count.get(a, 0) == 0]

        # Efficiency score
        loop_penalty = min(0.3, loops * 0.1)
        bottleneck_penalty = min(0.3, len(bottlenecks) * 0.1)
        utilization_penalty = min(0.2, len(underutilized) / max(1, len(topology.agents)) * 0.5)

        efficiency = max(0.0, 1.0 - loop_penalty - bottleneck_penalty - utilization_penalty)

        parts = []
        if loops:
            parts.append(f"{loops} delegation loops detected")
        if bottlenecks:
            parts.append(f"{len(bottlenecks)} bottleneck agents")
        if underutilized:
            parts.append(f"{len(underutilized)} underutilized agents")
        if not parts:
            parts.append("Delegation structure is well-balanced")

        return DelegationReport(
            efficiency_score=efficiency,
            bottleneck_agents=bottlenecks,
            underutilized_agents=underutilized,
            delegation_loops=loops,
            explanation=". ".join(parts) + ".",
        )

    def detect_collective_drift(
        self,
        genome_histories: Dict[str, List[BehaviorGenome]],
    ) -> Optional[CollectiveDriftReport]:
        """
        Detect fleet-wide behavioral shift.
        If >50% of agents drift in the same trait direction, it's collective.
        """
        if len(genome_histories) < 2:
            return None

        # Per-agent trait deltas (latest vs historical mean)
        agent_deltas: Dict[str, Dict[str, float]] = {}
        for agent_id, history in genome_histories.items():
            if len(history) < 2:
                continue
            latest = history[-1]
            earlier = history[:-1]
            avg_traits = {}
            for trait in TRAIT_NAMES:
                vals = [g.traits[trait] for g in earlier]
                avg_traits[trait] = sum(vals) / len(vals)
            agent_deltas[agent_id] = {
                trait: latest.traits[trait] - avg_traits[trait]
                for trait in TRAIT_NAMES
            }

        if not agent_deltas:
            return None

        # Find traits where majority of agents drift in same direction
        drift_direction: Dict[str, float] = {}
        affected_agents: List[str] = []

        for trait in TRAIT_NAMES:
            deltas = [d[trait] for d in agent_deltas.values() if abs(d[trait]) > 0.05]
            if not deltas:
                continue

            positive = sum(1 for d in deltas if d > 0)
            negative = sum(1 for d in deltas if d < 0)
            total = len(deltas)

            if positive / max(1, total) > 0.6:
                avg_delta = sum(d for d in deltas if d > 0) / max(1, positive)
                drift_direction[trait] = avg_delta
            elif negative / max(1, total) > 0.6:
                avg_delta = sum(d for d in deltas if d < 0) / max(1, negative)
                drift_direction[trait] = avg_delta

        if not drift_direction:
            return None

        magnitude = math.sqrt(sum(v ** 2 for v in drift_direction.values()))
        is_drifting = magnitude > 0.1 and len(drift_direction) >= 2

        if is_drifting:
            affected_agents = list(agent_deltas.keys())

        trait_descriptions = [
            f"{trait}: {'↑' if delta > 0 else '↓'} {abs(delta)*100:.1f}%"
            for trait, delta in sorted(drift_direction.items(), key=lambda x: abs(x[1]), reverse=True)
        ]

        return CollectiveDriftReport(
            is_drifting=is_drifting,
            drift_direction=drift_direction,
            affected_agents=affected_agents,
            magnitude=magnitude,
            explanation=(
                f"{'Collective' if is_drifting else 'Minor'} behavioral drift detected across "
                f"{len(affected_agents)} agents. Drifting traits: {'; '.join(trait_descriptions[:5])}."
            ),
        )
