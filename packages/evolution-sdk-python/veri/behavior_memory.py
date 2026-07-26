"""
VERI Behavioral Memory System — BehaviorOS v5.0

Behavioral memory stores operational execution patterns, uncertainty states,
tool failure modes, human approval interventions, and recovery trajectories.

Instead of remembering text ("customer asked for refund"), it remembers behavior:
  High uncertainty ──► Finance tool failed ──► Human approval ──► Recovered in 42s

This enables agents to learn from operational behavior across sessions.
"""

import time
import math
from typing import List, Dict, Any, Optional, Tuple

from veri.ir import RuntimeNode, NodeKind
from veri.state_engine import CognitiveStateVector, CognitivePhase


# ── Behavioral Episode Definition ─────────────────────────────────


class BehavioralEpisode:
    """
    A single recorded episode of behavioral execution.
    Stores operational context, state trajectory, failure modes, and recovery time.
    """

    def __init__(
        self,
        episode_id: str,
        agent_id: str,
        initial_phase: CognitivePhase,
        final_phase: CognitivePhase,
        state_vector: CognitiveStateVector,
        tool_invoked: Optional[str] = None,
        failure_mode: Optional[str] = None,
        human_intervention: bool = False,
        recovery_time_seconds: float = 0.0,
        success: bool = True,
        node_ids: Optional[List[str]] = None,
    ):
        self.episode_id = episode_id
        self.agent_id = agent_id
        self.initial_phase = initial_phase
        self.final_phase = final_phase
        self.state_vector = state_vector
        self.tool_invoked = tool_invoked
        self.failure_mode = failure_mode
        self.human_intervention = human_intervention
        self.recovery_time_seconds = recovery_time_seconds
        self.success = success
        self.node_ids = node_ids or []
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "agent_id": self.agent_id,
            "initial_phase": self.initial_phase.value,
            "final_phase": self.final_phase.value,
            "state_vector": self.state_vector.to_dict(),
            "tool_invoked": self.tool_invoked,
            "failure_mode": self.failure_mode,
            "human_intervention": self.human_intervention,
            "recovery_time_seconds": round(self.recovery_time_seconds, 2),
            "success": self.success,
            "node_ids": self.node_ids,
            "created_at": self.created_at,
        }


class EpisodeSearchResult:
    """SearchResult when querying behavioral memory for matching episodes."""

    def __init__(
        self,
        episode: BehavioralEpisode,
        similarity_score: float,
        recommended_recovery: str,
    ):
        self.episode = episode
        self.similarity_score = similarity_score
        self.recommended_recovery = recommended_recovery

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode": self.episode.to_dict(),
            "similarity_score": round(self.similarity_score, 4),
            "recommended_recovery": self.recommended_recovery,
        }


# ── Behavioral Memory Store ───────────────────────────────────────


class BehavioralMemoryStore:
    """
    In-memory and persistent behavioral memory engine.
    Indexes episodes by cognitive state vector distance, tool failure modes,
    and operational phase transitions.
    """

    def __init__(self):
        self.episodes: List[BehavioralEpisode] = []

    def store_episode(self, episode: BehavioralEpisode) -> None:
        """Stores a new behavioral episode in memory."""
        self.episodes.append(episode)

    def retrieve_similar_episodes(
        self,
        current_state: CognitiveStateVector,
        tool_name: Optional[str] = None,
        failure_mode: Optional[str] = None,
        top_k: int = 5,
    ) -> List[EpisodeSearchResult]:
        """
        Retrieves top-k historical behavioral episodes matching the current
        cognitive state vector and operational context.

        Calculates behavioral similarity based on state vector Euclidean distance
        and tool/failure mode matching.
        """
        results: List[EpisodeSearchResult] = []

        for ep in self.episodes:
            # 1. State vector distance similarity: S_state = 1 / (1 + distance)
            dist = current_state.distance_to(ep.state_vector)
            state_sim = 1.0 / (1.0 + dist)

            # 2. Context match bonus
            context_bonus = 0.0
            if tool_name and ep.tool_invoked and tool_name.lower() == ep.tool_invoked.lower():
                context_bonus += 0.2
            if failure_mode and ep.failure_mode and failure_mode.lower() in ep.failure_mode.lower():
                context_bonus += 0.3

            overall_sim = min(1.0, state_sim * 0.7 + context_bonus)

            # Generate recovery recommendation
            if ep.success:
                if ep.human_intervention:
                    rec = f"Escalate to human approval. Previous successful recovery took {ep.recovery_time_seconds:.1f}s via human sign-off."
                else:
                    rec = f"Apply automated recovery for tool '{ep.tool_invoked}'. Previous recovery succeeded in {ep.recovery_time_seconds:.1f}s."
            else:
                rec = f"Avoid path leading to '{ep.failure_mode}'. Unsuccessful episode in history."

            results.append(EpisodeSearchResult(
                episode=ep,
                similarity_score=overall_sim,
                recommended_recovery=rec,
            ))

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]

    def get_memory_stats(self) -> Dict[str, Any]:
        """Summary statistics of stored behavioral memory."""
        total = len(self.episodes)
        successful = sum(1 for e in self.episodes if e.success)
        interventions = sum(1 for e in self.episodes if e.human_intervention)
        avg_recovery = (
            sum(e.recovery_time_seconds for e in self.episodes if e.recovery_time_seconds > 0)
            / max(1, sum(1 for e in self.episodes if e.recovery_time_seconds > 0))
        )

        return {
            "total_episodes": total,
            "successful_episodes": successful,
            "human_interventions": interventions,
            "avg_recovery_time_seconds": round(avg_recovery, 2),
            "success_rate": round(successful / max(1, total), 3),
        }
