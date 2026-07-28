"""
VERI Behavioral Database & Query Engine (BQL) — BehaviorOS v5.0

Implements Behavior Query Language (BQL) — "SQL for Behaviors".
Allows developers and operators to query agent execution traces, cognitive states,
and behavioral patterns using SQL-like syntax.

Supported BQL Commands:
  - FIND workflows WHERE planning_depth > 7 AND uncertainty > 0.6 AND status = 'success'
  - SHOW executions SIMILAR TO 'session_48291' THRESHOLD 0.85
  - SELECT ANOMALIES WHERE impact > 0.5 GROUP BY agent_id
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple

from veri.ir import RuntimeNode, NodeKind
from veri.search import BehaviorSignature, compute_signature, compute_similarity


# ── BQL Query Result ──────────────────────────────────────────────


class BQLQueryResult:
    """The result of executing a BQL query against the Behavioral Database."""

    def __init__(
        self,
        query: str,
        matched_count: int,
        results: List[Dict[str, Any]],
        execution_time_ms: float,
    ):
        self.query = query
        self.matched_count = matched_count
        self.results = results
        self.execution_time_ms = execution_time_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "matched_count": self.matched_count,
            "results": self.results,
            "execution_time_ms": round(self.execution_time_ms, 3),
        }


# ── Behavioral Database ───────────────────────────────────────────


class SessionRecord:
    """Stored session record in the Behavioral Database."""

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        project_id: str,
        nodes: List[RuntimeNode],
        signature: BehaviorSignature,
        status: str = "success",
        total_cost: float = 0.0,
        planning_depth: int = 0,
        uncertainty: float = 0.0,
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.project_id = project_id
        self.nodes = nodes
        self.signature = signature
        self.status = status
        self.total_cost = total_cost
        self.planning_depth = planning_depth
        self.uncertainty = uncertainty

    def get_field(self, field_name: str) -> Any:
        """Dynamic field lookup for BQL WHERE clauses."""
        field_map = {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "project_id": self.project_id,
            "status": self.status,
            "total_cost": self.total_cost,
            "planning_depth": self.planning_depth,
            "uncertainty": self.uncertainty,
            "node_count": len(self.nodes),
            "error_rate": self.signature.error_rate,
            "reasoning_ratio": self.signature.reasoning_ratio,
        }
        return field_map.get(field_name.lower())


class BehavioralDatabase:
    """
    In-memory and indexed database of session execution graphs.
    Parses and executes Behavior Query Language (BQL) queries.
    """

    def __init__(self):
        self.records: Dict[str, SessionRecord] = {}

    def insert_session(
        self,
        session_id: str,
        agent_id: str,
        project_id: str,
        nodes: List[RuntimeNode],
        status: str = "success",
        total_cost: float = 0.0,
    ) -> None:
        """Inserts or updates a session execution graph in the database."""
        sig = compute_signature(nodes, [], session_id)
        reasoning_nodes = [n for n in nodes if n.kind == NodeKind.REASONING]
        planning_depth = len(reasoning_nodes)

        confs = [n.confidence for n in nodes if n.confidence is not None]
        avg_conf = sum(confs) / len(confs) if confs else 0.5
        uncertainty = 1.0 - avg_conf

        record = SessionRecord(
            session_id=session_id,
            agent_id=agent_id,
            project_id=project_id,
            nodes=nodes,
            signature=sig,
            status=status,
            total_cost=total_cost,
            planning_depth=planning_depth,
            uncertainty=uncertainty,
        )
        self.records[session_id] = record

    def execute_bql(self, query: str) -> BQLQueryResult:
        """
        Parses and executes a BQL string query against stored records.

        Supported Syntax Examples:
          - FIND workflows WHERE planning_depth > 7 AND uncertainty > 0.6 AND status = 'success'
          - SHOW executions SIMILAR TO 'session_123' THRESHOLD 0.80
          - SELECT ANOMALIES WHERE error_rate > 0.1
        """
        start_time = time.time()
        q_upper = query.strip().upper()

        if q_upper.startswith("FIND"):
            results = self._execute_find(query)
        elif q_upper.startswith("SHOW"):
            results = self._execute_show_similar(query)
        elif q_upper.startswith("SELECT"):
            results = self._execute_select(query)
        else:
            results = [r.signature.to_dict() for r in self.records.values()]

        exec_time = (time.time() - start_time) * 1000.0
        return BQLQueryResult(
            query=query,
            matched_count=len(results),
            results=results,
            execution_time_ms=exec_time,
        )

    # ── Internal BQL Query Parsers ─────────────────────────────────

    def _execute_find(self, query: str) -> List[Dict[str, Any]]:
        """Parses: FIND workflows WHERE <conditions>"""
        match = re.search(r"WHERE\s+(.+)$", query, re.IGNORECASE)
        if not match:
            return [r.signature.to_dict() for r in self.records.values()]

        where_clause = match.group(1)
        conditions = [c.strip() for c in where_clause.split("AND")]

        matched_results = []
        for record in self.records.values():
            if self._eval_conditions(record, conditions):
                matched_results.append({
                    "session_id": record.session_id,
                    "agent_id": record.agent_id,
                    "status": record.status,
                    "planning_depth": record.planning_depth,
                    "uncertainty": round(record.uncertainty, 3),
                    "total_cost": round(record.total_cost, 4),
                    "signature": record.signature.to_dict(),
                })
        return matched_results

    def _execute_show_similar(self, query: str) -> List[Dict[str, Any]]:
        """Parses: SHOW executions SIMILAR TO 'session_id' THRESHOLD 0.80"""
        target_match = re.search(r"SIMILAR TO ['\"]([^'\"]+)['\"]", query, re.IGNORECASE)
        threshold_match = re.search(r"THRESHOLD\s+([0-9\.]+)", query, re.IGNORECASE)

        if not target_match:
            return []

        target_id = target_match.group(1)
        threshold = float(threshold_match.group(1)) if threshold_match else 0.70

        target_rec = self.records.get(target_id)
        if not target_rec:
            return []

        results = []
        for rec in self.records.values():
            if rec.session_id == target_id:
                continue
            sim = compute_similarity(target_rec.signature, rec.signature)
            if sim >= threshold:
                results.append({
                    "session_id": rec.session_id,
                    "similarity": round(sim, 4),
                    "agent_id": rec.agent_id,
                    "status": rec.status,
                    "signature": rec.signature.to_dict(),
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results

    def _execute_select(self, query: str) -> List[Dict[str, Any]]:
        """Parses: SELECT ANOMALIES WHERE error_rate > 0.10"""
        match = re.search(r"WHERE\s+(.+)$", query, re.IGNORECASE)
        conditions = [c.strip() for c in match.group(1).split("AND")] if match else []

        results = []
        for rec in self.records.values():
            if not conditions or self._eval_conditions(rec, conditions):
                if rec.signature.error_rate > 0.0 or rec.status != "success":
                    results.append({
                        "session_id": rec.session_id,
                        "agent_id": rec.agent_id,
                        "status": rec.status,
                        "error_rate": round(rec.signature.error_rate, 3),
                        "uncertainty": round(rec.uncertainty, 3),
                    })
        return results

    def _eval_conditions(self, record: SessionRecord, conditions: List[str]) -> bool:
        """Evaluates a list of string conditions against a SessionRecord."""
        for cond in conditions:
            # Match operator: >, <, >=, <=, =, !=
            m = re.match(r"(\w+)\s*(=|!=|>|<|>=|<=)\s*['\"]?([^'\"]+)['\"]?", cond)
            if not m:
                continue
            field, op, val_str = m.groups()
            actual_val = record.get_field(field)

            if actual_val is None:
                return False

            # Type conversion
            try:
                if "." in val_str:
                    target_val = float(val_str)
                else:
                    target_val = int(val_str)
            except ValueError:
                target_val = val_str.lower()
                actual_val = str(actual_val).lower()

            if op == "=" and actual_val != target_val:
                return False
            elif op == "!=" and actual_val == target_val:
                return False
            elif op == ">" and not (actual_val > target_val):
                return False
            elif op == "<" and not (actual_val < target_val):
                return False
            elif op == ">=" and not (actual_val >= target_val):
                return False
            elif op == "<=" and not (actual_val <= target_val):
                return False
        return True
