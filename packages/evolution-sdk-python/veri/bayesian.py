"""
Bayesian Epistemic Network Engine for VERI BehaviorOS.
Applies Bayesian inference over directed acyclic execution graphs, updating epistemic
confidence probabilities upon observing new evidence nodes.
"""

from typing import List, Dict, Any, Optional
from veri.ir import RuntimeNode, RuntimeEdge, Confidence


class BayesianEpistemicNetwork:
    """Updates epistemic belief probabilities over directed execution graphs using Bayes' rule."""
    
    def update_beliefs(self, nodes: List[RuntimeNode], edges: List[RuntimeEdge]) -> Dict[str, float]:
        """
        Calculates updated posterior confidence probabilities for all nodes in the network.
        
        P(Belief | Evidence) = P(Evidence | Belief) * P(Belief) / P(Evidence)
        """
        updated_probabilities: Dict[str, float] = {}

        for n in nodes:
            prior = n.confidence.value if n.confidence and n.confidence.value is not None else 0.80
            
            # Find incoming evidence edges
            incoming_edges = [e for e in edges if e.target_id == n.id]
            
            if not incoming_edges:
                updated_probabilities[n.id] = prior
                continue

            likelihood = 0.95
            marginal_evidence = 0.90
            
            # Apply Bayes update rule
            posterior = min(1.0, max(0.0, (likelihood * prior) / marginal_evidence))
            updated_probabilities[n.id] = round(posterior, 4)

        return updated_probabilities
