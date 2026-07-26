"""
VERI Evolution Engine — BehaviorOS v4.0

Continuous behavioral improvement through genetic-inspired operators:
  - Fitness function: composite of cost, success, latency, alignment
  - Selection: identify highest-fitness behavioral genomes
  - Crossover: combine traits from successful behavioral patterns
  - Mutation: explore nearby behavioral configurations
  - Generation tracking and comparison
  - Concrete improvement recommendations

This engine answers: "How should the agent EVOLVE to be better?"
"""

import math
import random
from typing import List, Dict, Any, Optional, Tuple

from veri.genome import BehaviorGenome, compute_distance, TRAIT_NAMES


# ── Data Structures ────────────────────────────────────────────────


class SessionOutcome:
    """Outcome metrics for a single session."""

    def __init__(
        self,
        session_id: str,
        success: bool,
        total_cost: float,
        total_latency: float,
        error_count: int,
        goal_completion_rate: float,
    ):
        self.session_id = session_id
        self.success = success
        self.total_cost = total_cost
        self.total_latency = total_latency
        self.error_count = error_count
        self.goal_completion_rate = max(0.0, min(1.0, goal_completion_rate))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "success": self.success,
            "total_cost": round(self.total_cost, 4),
            "total_latency": round(self.total_latency, 2),
            "error_count": self.error_count,
            "goal_completion_rate": round(self.goal_completion_rate, 3),
        }


class ImprovementRecommendation:
    """A concrete, actionable configuration change derived from evolutionary analysis."""

    def __init__(
        self,
        trait: str,
        current_value: float,
        target_value: float,
        expected_fitness_gain: float,
        action: str,
        confidence: float,
    ):
        self.trait = trait
        self.current_value = current_value
        self.target_value = target_value
        self.expected_fitness_gain = expected_fitness_gain
        self.action = action
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trait": self.trait,
            "current_value": round(self.current_value, 4),
            "target_value": round(self.target_value, 4),
            "delta": round(self.target_value - self.current_value, 4),
            "expected_fitness_gain": round(self.expected_fitness_gain, 4),
            "action": self.action,
            "confidence": round(self.confidence, 3),
        }


class GenerationReport:
    """Snapshot of a behavioral population at a generation."""

    def __init__(
        self,
        generation_id: str,
        population_size: int,
        avg_fitness: float,
        max_fitness: float,
        min_fitness: float,
        fitness_std: float,
        avg_genome: BehaviorGenome,
        trait_variances: Dict[str, float],
    ):
        self.generation_id = generation_id
        self.population_size = population_size
        self.avg_fitness = avg_fitness
        self.max_fitness = max_fitness
        self.min_fitness = min_fitness
        self.fitness_std = fitness_std
        self.avg_genome = avg_genome
        self.trait_variances = trait_variances

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "population_size": self.population_size,
            "avg_fitness": round(self.avg_fitness, 4),
            "max_fitness": round(self.max_fitness, 4),
            "min_fitness": round(self.min_fitness, 4),
            "fitness_std": round(self.fitness_std, 4),
            "avg_genome": self.avg_genome.to_dict(),
            "trait_variances": {k: round(v, 4) for k, v in self.trait_variances.items()},
        }


# ── Fitness Function ─────────────────────────────────────────────

# Trait importance weights for fitness computation
_FITNESS_WEIGHTS = {
    "decisiveness": 0.08,
    "exploration_rate": 0.05,
    "tool_diversity": 0.05,
    "reasoning_depth": 0.07,
    "risk_tolerance": -0.05,  # Lower risk = better (negative weight inverts)
    "recovery_speed": 0.10,
    "delegation_tendency": 0.03,
    "confidence_calibration": 0.12,
    "cost_efficiency": 0.15,
    "focus_persistence": 0.08,
    "learning_rate": 0.10,
    "error_handling_style": 0.05,
    "autonomy_level": 0.07,
}

# Outcome-based weight multipliers
_OUTCOME_WEIGHTS = {
    "success": 0.30,
    "cost_efficiency": 0.25,
    "speed": 0.20,
    "error_free": 0.15,
    "completion": 0.10,
}


# ── Evolution Engine ─────────────────────────────────────────────


class EvolutionEngine:
    """
    Drives continuous behavioral improvement through
    genetic-inspired operators on behavior genomes.
    """

    def compute_fitness(
        self,
        genome: BehaviorGenome,
        outcome: Optional[SessionOutcome] = None,
    ) -> float:
        """
        Computes behavioral fitness as a weighted combination of
        genome traits and session outcome metrics.

        Fitness ∈ [0, 1] where 1 is optimal behavior.
        """
        # 1. Genome-based fitness (intrinsic behavioral quality)
        genome_fitness = 0.0
        for trait, weight in _FITNESS_WEIGHTS.items():
            value = genome.traits.get(trait, 0.5)
            if weight < 0:
                # Negative weight: lower value is better
                genome_fitness += abs(weight) * (1.0 - value)
            else:
                genome_fitness += weight * value

        # 2. Outcome-based fitness (extrinsic performance)
        if outcome:
            outcome_fitness = 0.0
            outcome_fitness += _OUTCOME_WEIGHTS["success"] * (1.0 if outcome.success else 0.0)
            outcome_fitness += _OUTCOME_WEIGHTS["cost_efficiency"] * max(0.0, 1.0 - min(1.0, outcome.total_cost / 1.0))
            outcome_fitness += _OUTCOME_WEIGHTS["speed"] * max(0.0, 1.0 - min(1.0, outcome.total_latency / 60000.0))
            outcome_fitness += _OUTCOME_WEIGHTS["error_free"] * max(0.0, 1.0 - min(1.0, outcome.error_count / 5.0))
            outcome_fitness += _OUTCOME_WEIGHTS["completion"] * outcome.goal_completion_rate

            # Blend genome and outcome fitness
            fitness = 0.4 * genome_fitness + 0.6 * outcome_fitness
        else:
            fitness = genome_fitness

        return max(0.0, min(1.0, fitness))

    def select_elite(
        self,
        genomes: List[BehaviorGenome],
        outcomes: List[Optional[SessionOutcome]],
        top_k: int = 5,
    ) -> List[Tuple[BehaviorGenome, float]]:
        """
        Tournament selection: evaluate fitness for all genomes,
        return top-k with their fitness scores.
        """
        scored = []
        for i, genome in enumerate(genomes):
            outcome = outcomes[i] if i < len(outcomes) else None
            fitness = self.compute_fitness(genome, outcome)
            scored.append((genome, fitness))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def crossover(
        self,
        parent_a: BehaviorGenome,
        parent_b: BehaviorGenome,
        crossover_rate: float = 0.5,
    ) -> BehaviorGenome:
        """
        Uniform crossover: each trait independently selected from either parent.

        crossover_rate: probability of selecting from parent_a (vs parent_b).
        """
        child_traits: Dict[str, float] = {}

        for trait in TRAIT_NAMES:
            if random.random() < crossover_rate:
                child_traits[trait] = parent_a.traits[trait]
            else:
                child_traits[trait] = parent_b.traits[trait]

        return BehaviorGenome(child_traits, session_id="crossover")

    def mutate(
        self,
        genome: BehaviorGenome,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.15,
    ) -> BehaviorGenome:
        """
        Gaussian mutation: each trait has mutation_rate probability of being perturbed.

        mutation_strength: standard deviation of the Gaussian perturbation.
        """
        mutated_traits: Dict[str, float] = {}

        for trait in TRAIT_NAMES:
            value = genome.traits[trait]
            if random.random() < mutation_rate:
                # Gaussian perturbation clamped to [0, 1]
                perturbation = random.gauss(0, mutation_strength)
                value = max(0.0, min(1.0, value + perturbation))
            mutated_traits[trait] = value

        return BehaviorGenome(mutated_traits, session_id="mutated")

    def recommend_improvements(
        self,
        current: BehaviorGenome,
        elite: List[Tuple[BehaviorGenome, float]],
    ) -> List[ImprovementRecommendation]:
        """
        Generates concrete improvement recommendations by comparing
        current genome to elite performers.

        For each trait where current significantly differs from elite average,
        recommend a specific action.
        """
        if not elite:
            return []

        recommendations: List[ImprovementRecommendation] = []

        # Compute elite average genome
        elite_avg: Dict[str, float] = {}
        elite_fitnesses = [f for _, f in elite]
        avg_elite_fitness = sum(elite_fitnesses) / len(elite_fitnesses)

        for trait in TRAIT_NAMES:
            values = [g.traits[trait] for g, _ in elite]
            elite_avg[trait] = sum(values) / len(values)

        current_fitness = self.compute_fitness(current)

        # Trait-specific action recommendations
        _TRAIT_ACTIONS = {
            "decisiveness": ("Reduce reasoning iterations before committing to an action.", "Increase deliberation time and add more evaluation criteria."),
            "exploration_rate": ("Add more retrieval/search steps before acting.", "Reduce information gathering and proceed with available context."),
            "tool_diversity": ("Expand the set of tools considered for each sub-goal.", "Specialize on fewer, well-tested tools."),
            "reasoning_depth": ("Add chain-of-thought reasoning steps.", "Reduce reasoning verbosity and act more directly."),
            "risk_tolerance": ("Add pre-execution safety checks.", "Allow actions under higher uncertainty thresholds."),
            "recovery_speed": ("Implement faster error handling with retry logic.", "Current recovery speed is adequate."),
            "delegation_tendency": ("Consider delegating complex subtasks to specialized sub-agents.", "Reduce delegation and handle more tasks directly."),
            "confidence_calibration": ("Add self-evaluation steps after each major action.", "Reduce over-confidence by adding verification checkpoints."),
            "cost_efficiency": ("Switch to smaller/cheaper models for simple sub-tasks.", "Invest more in quality for critical decision points."),
            "focus_persistence": ("Maintain focus on primary goal; reduce context switches.", "Allow more flexibility in goal pursuit."),
            "learning_rate": ("Add explicit reflection steps after errors.", "Current learning rate is sufficient."),
            "error_handling_style": ("Escalate errors instead of retrying blindly.", "Try recovery before escalating."),
            "autonomy_level": ("Act more independently; reduce confirmation requests.", "Add more human-in-the-loop checkpoints."),
        }

        for trait in TRAIT_NAMES:
            current_val = current.traits[trait]
            elite_val = elite_avg[trait]
            delta = elite_val - current_val

            if abs(delta) < 0.08:  # Insignificant difference
                continue

            # Choose action based on direction of improvement needed
            actions = _TRAIT_ACTIONS.get(trait, ("Increase this trait.", "Decrease this trait."))
            action = actions[0] if delta > 0 else actions[1]

            # Expected fitness gain: proportional to weight * delta
            weight = abs(_FITNESS_WEIGHTS.get(trait, 0.05))
            expected_gain = weight * abs(delta) * 2.0

            recommendations.append(ImprovementRecommendation(
                trait=trait,
                current_value=current_val,
                target_value=elite_val,
                expected_fitness_gain=expected_gain,
                action=action,
                confidence=min(0.95, 0.5 + len(elite) * 0.1),
            ))

        # Sort by expected fitness gain
        recommendations.sort(key=lambda r: r.expected_fitness_gain, reverse=True)
        return recommendations

    def track_generation(
        self,
        genomes: List[BehaviorGenome],
        outcomes: List[Optional[SessionOutcome]],
        generation_id: str,
    ) -> GenerationReport:
        """
        Snapshot a behavioral population at a given generation.
        Tracks fitness statistics and trait variances.
        """
        fitnesses = []
        for i, genome in enumerate(genomes):
            outcome = outcomes[i] if i < len(outcomes) else None
            fitnesses.append(self.compute_fitness(genome, outcome))

        avg_fitness = sum(fitnesses) / max(1, len(fitnesses))
        max_fitness = max(fitnesses) if fitnesses else 0.0
        min_fitness = min(fitnesses) if fitnesses else 0.0
        fitness_std = math.sqrt(
            sum((f - avg_fitness) ** 2 for f in fitnesses) / max(1, len(fitnesses) - 1)
        ) if len(fitnesses) > 1 else 0.0

        # Average genome
        avg_traits: Dict[str, float] = {}
        for trait in TRAIT_NAMES:
            values = [g.traits[trait] for g in genomes]
            avg_traits[trait] = sum(values) / max(1, len(values))
        avg_genome = BehaviorGenome(avg_traits, session_id=f"gen_{generation_id}_avg")

        # Trait variances
        trait_variances: Dict[str, float] = {}
        for trait in TRAIT_NAMES:
            values = [g.traits[trait] for g in genomes]
            mean = sum(values) / max(1, len(values))
            variance = sum((v - mean) ** 2 for v in values) / max(1, len(values))
            trait_variances[trait] = variance

        return GenerationReport(
            generation_id=generation_id,
            population_size=len(genomes),
            avg_fitness=avg_fitness,
            max_fitness=max_fitness,
            min_fitness=min_fitness,
            fitness_std=fitness_std,
            avg_genome=avg_genome,
            trait_variances=trait_variances,
        )

    def evolve_population(
        self,
        genomes: List[BehaviorGenome],
        outcomes: List[Optional[SessionOutcome]],
        elite_size: int = 3,
        offspring_count: int = 5,
        mutation_rate: float = 0.15,
    ) -> List[BehaviorGenome]:
        """
        Run one generation of evolution:
        1. Select elite
        2. Generate offspring via crossover
        3. Mutate offspring
        4. Return new population

        Returns the next generation of genomes.
        """
        # 1. Selection
        elite = self.select_elite(genomes, outcomes, top_k=elite_size)
        elite_genomes = [g for g, _ in elite]

        # 2. Keep elite unchanged (elitism)
        next_gen = list(elite_genomes)

        # 3. Generate offspring via crossover
        for _ in range(offspring_count):
            if len(elite_genomes) >= 2:
                parent_a = random.choice(elite_genomes)
                parent_b = random.choice(elite_genomes)
                child = self.crossover(parent_a, parent_b)
            else:
                child = elite_genomes[0] if elite_genomes else BehaviorGenome({})

            # 4. Mutate
            child = self.mutate(child, mutation_rate=mutation_rate)
            next_gen.append(child)

        return next_gen
