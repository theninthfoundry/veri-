"""
VERI Behavioral Search Engine — BehaviorOS v4.0

Searches behaviors by execution topology, not text similarity:
  - Structural signatures from graph topology (node kind distribution, depth, branching)
  - Graph edit distance-based similarity measurement
  - Anti-pattern library matching (known bad behavior signatures)
  - Signature indexing for fast behavioral search

This engine answers: "Have we seen this behavior PATTERN before?"
"""

import math
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter, defaultdict

from veri.ir import RuntimeNode, RuntimeEdge, NodeKind


# ── Data Structures ────────────────────────────────────────────────


class BehaviorSignature:
    """
    Compressed topological fingerprint of an execution pattern.

    Encodes structural properties that are invariant to node IDs, timestamps,
    and content — capturing only the shape of behavior.
    """

    def __init__(
        self,
        session_id: str,
        node_count: int,
        edge_count: int,
        kind_distribution: Dict[str, float],
        max_depth: int,
        max_branching: int,
        avg_branching: float,
        cycle_count: int,
        error_rate: float,
        avg_confidence: float,
        reasoning_ratio: float,
        action_ratio: float,
        delegation_ratio: float,
        transition_sequence: List[str],
    ):
        self.session_id = session_id
        self.node_count = node_count
        self.edge_count = edge_count
        self.kind_distribution = kind_distribution
        self.max_depth = max_depth
        self.max_branching = max_branching
        self.avg_branching = avg_branching
        self.cycle_count = cycle_count
        self.error_rate = error_rate
        self.avg_confidence = avg_confidence
        self.reasoning_ratio = reasoning_ratio
        self.action_ratio = action_ratio
        self.delegation_ratio = delegation_ratio
        self.transition_sequence = transition_sequence  # Compressed kind sequence

    @property
    def feature_vector(self) -> List[float]:
        """Numeric feature vector for distance computation."""
        return [
            self.node_count / 100.0,  # Normalized
            self.edge_count / 100.0,
            self.max_depth / 20.0,
            self.max_branching / 10.0,
            self.avg_branching / 5.0,
            self.cycle_count / 5.0,
            self.error_rate,
            self.avg_confidence,
            self.reasoning_ratio,
            self.action_ratio,
            self.delegation_ratio,
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "kind_distribution": {
                k: round(v, 3) for k, v in self.kind_distribution.items()
            },
            "max_depth": self.max_depth,
            "max_branching": self.max_branching,
            "avg_branching": round(self.avg_branching, 2),
            "cycle_count": self.cycle_count,
            "error_rate": round(self.error_rate, 3),
            "avg_confidence": round(self.avg_confidence, 3),
            "reasoning_ratio": round(self.reasoning_ratio, 3),
            "action_ratio": round(self.action_ratio, 3),
            "delegation_ratio": round(self.delegation_ratio, 3),
        }


class SearchResult:
    """Result of a behavioral similarity search."""

    def __init__(
        self,
        session_id: str,
        similarity: float,
        signature: BehaviorSignature,
        explanation: str,
    ):
        self.session_id = session_id
        self.similarity = similarity
        self.signature = signature
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "similarity": round(self.similarity, 4),
            "explanation": self.explanation,
        }


class AntipatternMatch:
    """Detection of a known bad behavioral pattern."""

    def __init__(
        self,
        pattern_name: str,
        severity: str,
        match_score: float,
        description: str,
        evidence: Dict[str, Any],
    ):
        self.pattern_name = pattern_name
        self.severity = severity
        self.match_score = match_score
        self.description = description
        self.evidence = evidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_name": self.pattern_name,
            "severity": self.severity,
            "match_score": round(self.match_score, 3),
            "description": self.description,
            "evidence": self.evidence,
        }


# ── Anti-Pattern Library ──────────────────────────────────────────

# Each anti-pattern is a function (signature → Optional[AntipatternMatch])

def _check_infinite_loop(sig: BehaviorSignature) -> Optional[AntipatternMatch]:
    """Detects infinite reasoning loops."""
    if sig.cycle_count >= 3 or sig.reasoning_ratio > 0.6:
        score = min(1.0, (sig.cycle_count * 0.2) + (max(0, sig.reasoning_ratio - 0.4) * 2.0))
        if score > 0.5:
            return AntipatternMatch(
                pattern_name="infinite_reasoning_loop",
                severity="high",
                match_score=score,
                description=(
                    f"Behavioral signature matches infinite loop pattern: "
                    f"{sig.cycle_count} cycles, {sig.reasoning_ratio*100:.0f}% reasoning nodes."
                ),
                evidence={"cycle_count": sig.cycle_count, "reasoning_ratio": sig.reasoning_ratio},
            )
    return None


def _check_escalation_cascade(sig: BehaviorSignature) -> Optional[AntipatternMatch]:
    """Detects cascading escalation patterns."""
    if sig.delegation_ratio > 0.3 and sig.error_rate > 0.15:
        score = min(1.0, sig.delegation_ratio * 2.0 + sig.error_rate * 2.0)
        if score > 0.5:
            return AntipatternMatch(
                pattern_name="escalation_cascade",
                severity="critical",
                match_score=score,
                description=(
                    f"Agent escalating/delegating excessively ({sig.delegation_ratio*100:.0f}%) "
                    f"while error rate remains high ({sig.error_rate*100:.0f}%)."
                ),
                evidence={"delegation_ratio": sig.delegation_ratio, "error_rate": sig.error_rate},
            )
    return None


def _check_hallucination_spiral(sig: BehaviorSignature) -> Optional[AntipatternMatch]:
    """Detects declining confidence with continued action (hallucination risk)."""
    if sig.avg_confidence < 0.35 and sig.action_ratio > 0.3:
        score = min(1.0, (1.0 - sig.avg_confidence) * sig.action_ratio * 3.0)
        if score > 0.5:
            return AntipatternMatch(
                pattern_name="hallucination_spiral",
                severity="critical",
                match_score=score,
                description=(
                    f"Agent acting ({sig.action_ratio*100:.0f}% action nodes) despite low "
                    f"confidence ({sig.avg_confidence:.2f}). High hallucination risk."
                ),
                evidence={"avg_confidence": sig.avg_confidence, "action_ratio": sig.action_ratio},
            )
    return None


def _check_analysis_paralysis(sig: BehaviorSignature) -> Optional[AntipatternMatch]:
    """Detects excessive reasoning without action."""
    if sig.reasoning_ratio > 0.5 and sig.action_ratio < 0.1:
        score = min(1.0, sig.reasoning_ratio * 1.5 - sig.action_ratio * 5.0)
        if score > 0.5:
            return AntipatternMatch(
                pattern_name="analysis_paralysis",
                severity="medium",
                match_score=score,
                description=(
                    f"Agent spending {sig.reasoning_ratio*100:.0f}% of steps on reasoning "
                    f"but only {sig.action_ratio*100:.0f}% on actions. Decision paralysis detected."
                ),
                evidence={"reasoning_ratio": sig.reasoning_ratio, "action_ratio": sig.action_ratio},
            )
    return None


def _check_cost_explosion(sig: BehaviorSignature) -> Optional[AntipatternMatch]:
    """Detects high branching with error nodes (expensive failed exploration)."""
    if sig.max_branching >= 5 and sig.error_rate > 0.1:
        score = min(1.0, (sig.max_branching / 10.0) + sig.error_rate * 2.0)
        if score > 0.5:
            return AntipatternMatch(
                pattern_name="cost_explosion",
                severity="high",
                match_score=score,
                description=(
                    f"Wide branching factor ({sig.max_branching}) combined with high "
                    f"error rate ({sig.error_rate*100:.0f}%). Expensive failed explorations."
                ),
                evidence={"max_branching": sig.max_branching, "error_rate": sig.error_rate},
            )
    return None


_ANTIPATTERN_CHECKS = [
    _check_infinite_loop,
    _check_escalation_cascade,
    _check_hallucination_spiral,
    _check_analysis_paralysis,
    _check_cost_explosion,
]


# ── Signature Computation ─────────────────────────────────────────


def compute_signature(
    nodes: List[RuntimeNode],
    edges: List[RuntimeEdge],
    session_id: str = "",
) -> BehaviorSignature:
    """Compute a topological fingerprint from an execution trace."""
    if not nodes:
        return BehaviorSignature(
            session_id=session_id, node_count=0, edge_count=0,
            kind_distribution={}, max_depth=0, max_branching=0,
            avg_branching=0.0, cycle_count=0, error_rate=0.0,
            avg_confidence=0.5, reasoning_ratio=0.0, action_ratio=0.0,
            delegation_ratio=0.0, transition_sequence=[],
        )

    node_ids = {n.id for n in nodes}
    kind_counts = Counter(n.kind for n in nodes)
    total = len(nodes)

    # Kind distribution (normalized)
    kind_dist = {k: c / total for k, c in kind_counts.items()}

    # Build adjacency
    children: Dict[str, List[str]] = defaultdict(list)
    parent_count: Dict[str, int] = defaultdict(int)
    for e in edges:
        if e.source in node_ids and e.target in node_ids:
            children[e.source].append(e.target)
            parent_count[e.target] += 1

    # Max depth via BFS from root nodes
    roots = [n.id for n in nodes if parent_count.get(n.id, 0) == 0]
    max_depth = 0
    for root in roots:
        queue: List[Tuple[str, int]] = [(root, 0)]
        visited: Set[str] = {root}
        while queue:
            current, depth = queue.pop(0)
            max_depth = max(max_depth, depth)
            for child in children.get(current, []):
                if child not in visited:
                    visited.add(child)
                    queue.append((child, depth + 1))

    # Branching statistics
    branching_factors = [len(children[nid]) for nid in node_ids if children.get(nid)]
    max_branching = max(branching_factors) if branching_factors else 0
    avg_branching = sum(branching_factors) / max(1, len(branching_factors))

    # Cycle detection (simplified: check for back-edges in DFS)
    cycle_count = 0
    visited_global: Set[str] = set()
    for root in roots:
        stack: List[Tuple[str, Set[str]]] = [(root, set())]
        while stack:
            current, path = stack.pop()
            if current in path:
                cycle_count += 1
                continue
            if current in visited_global:
                continue
            visited_global.add(current)
            new_path = path | {current}
            for child in children.get(current, []):
                stack.append((child, new_path))

    # Ratios
    reasoning_count = sum(
        kind_counts.get(k, 0) for k in [NodeKind.REASONING, NodeKind.BELIEF, NodeKind.REFLECTION]
    )
    action_count = sum(
        kind_counts.get(k, 0) for k in [NodeKind.ACTION, NodeKind.TOOL_INVOCATION, NodeKind.LLM_CALL]
    )
    delegation_count = kind_counts.get(NodeKind.DELEGATION, 0) + kind_counts.get(NodeKind.ESCALATION, 0)
    error_count = kind_counts.get(NodeKind.ERROR, 0)

    # Confidence
    confs = [n.confidence for n in nodes if n.confidence is not None]
    avg_conf = sum(confs) / max(1, len(confs)) if confs else 0.5

    # Transition sequence (compressed: only when kind changes)
    transition_seq = [nodes[0].kind]
    for i in range(1, len(nodes)):
        if nodes[i].kind != nodes[i-1].kind:
            transition_seq.append(nodes[i].kind)

    return BehaviorSignature(
        session_id=session_id,
        node_count=total,
        edge_count=len(edges),
        kind_distribution=kind_dist,
        max_depth=max_depth,
        max_branching=max_branching,
        avg_branching=avg_branching,
        cycle_count=cycle_count,
        error_rate=error_count / max(1, total),
        avg_confidence=avg_conf,
        reasoning_ratio=reasoning_count / max(1, total),
        action_ratio=action_count / max(1, total),
        delegation_ratio=delegation_count / max(1, total),
        transition_sequence=transition_seq[:50],  # Cap at 50 for efficiency
    )


# ── Similarity Computation ────────────────────────────────────────


def compute_similarity(sig_a: BehaviorSignature, sig_b: BehaviorSignature) -> float:
    """
    Structural similarity between two behavioral signatures.
    Uses a weighted combination of:
      1. Feature vector cosine similarity (structural metrics)
      2. Kind distribution Jensen-Shannon divergence
      3. Transition sequence edit distance (behavioral flow)
    """
    # 1. Feature vector cosine similarity (weight: 0.4)
    vec_a = sig_a.feature_vector
    vec_b = sig_b.feature_vector
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    cosine_sim = dot / (mag_a * mag_b) if mag_a > 0 and mag_b > 0 else 0.0

    # 2. Kind distribution similarity (weight: 0.35)
    # Jensen-Shannon divergence (symmetric KL)
    all_kinds = set(sig_a.kind_distribution.keys()) | set(sig_b.kind_distribution.keys())
    js_div = 0.0
    for k in all_kinds:
        p = sig_a.kind_distribution.get(k, 0.0)
        q = sig_b.kind_distribution.get(k, 0.0)
        m = (p + q) / 2.0
        if p > 0 and m > 0:
            js_div += p * math.log(p / m) / 2.0
        if q > 0 and m > 0:
            js_div += q * math.log(q / m) / 2.0
    kind_sim = max(0.0, 1.0 - js_div * 2.0)

    # 3. Transition sequence similarity (weight: 0.25)
    # Normalized Levenshtein distance
    seq_a = sig_a.transition_sequence[:30]
    seq_b = sig_b.transition_sequence[:30]
    edit_dist = _levenshtein_distance(seq_a, seq_b)
    max_len = max(len(seq_a), len(seq_b))
    seq_sim = 1.0 - (edit_dist / max_len) if max_len > 0 else 1.0

    # Weighted combination
    similarity = 0.40 * cosine_sim + 0.35 * kind_sim + 0.25 * seq_sim
    return max(0.0, min(1.0, similarity))


def _levenshtein_distance(seq_a: List[str], seq_b: List[str]) -> int:
    """Levenshtein edit distance between two sequences."""
    m, n = len(seq_a), len(seq_b)
    if m == 0:
        return n
    if n == 0:
        return m

    # Use two rows for space efficiency
    prev = list(range(n + 1))
    curr = [0] * (n + 1)

    for i in range(1, m + 1):
        curr[0] = i
        for j in range(1, n + 1):
            cost = 0 if seq_a[i - 1] == seq_b[j - 1] else 1
            curr[j] = min(
                prev[j] + 1,      # Deletion
                curr[j - 1] + 1,  # Insertion
                prev[j - 1] + cost,  # Substitution
            )
        prev, curr = curr, prev

    return prev[n]


# ── Search Operations ─────────────────────────────────────────────


def search_similar(
    query: BehaviorSignature,
    library: List[BehaviorSignature],
    top_k: int = 10,
) -> List[SearchResult]:
    """Find the most behaviorally similar sessions from a library."""
    results = []
    for sig in library:
        if sig.session_id == query.session_id:
            continue
        sim = compute_similarity(query, sig)
        results.append(SearchResult(
            session_id=sig.session_id,
            similarity=sim,
            signature=sig,
            explanation=(
                f"Structural similarity: {sim:.1%}. "
                f"Nodes: {sig.node_count}, Depth: {sig.max_depth}, "
                f"Errors: {sig.error_rate*100:.0f}%."
            ),
        ))

    results.sort(key=lambda r: r.similarity, reverse=True)
    return results[:top_k]


def match_antipatterns(
    signature: BehaviorSignature,
) -> List[AntipatternMatch]:
    """Check a behavioral signature against all known anti-patterns."""
    matches = []
    for check_fn in _ANTIPATTERN_CHECKS:
        match = check_fn(signature)
        if match:
            matches.append(match)
    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches


class SignatureIndex:
    """Searchable index of behavioral signatures for fast lookup."""

    def __init__(self):
        self.signatures: List[BehaviorSignature] = []

    def add(self, signature: BehaviorSignature) -> None:
        self.signatures.append(signature)

    def search(
        self, query: BehaviorSignature, top_k: int = 10
    ) -> List[SearchResult]:
        return search_similar(query, self.signatures, top_k)

    @property
    def size(self) -> int:
        return len(self.signatures)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "size": self.size,
            "sessions": [s.session_id for s in self.signatures],
        }
