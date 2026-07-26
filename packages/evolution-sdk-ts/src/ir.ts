/**
 * VERI Runtime IR Schema — TypeScript Definition
 */

export enum NodeKind {
  INTENT = "intent",
  SUBGOAL = "subgoal",
  PLAN = "plan",
  REASONING = "reasoning",
  KNOWLEDGE = "knowledge",
  OBSERVATION = "observation",
  WORLD_STATE = "world_state",
  DECISION = "decision",
  ACTION = "action",
  TOOL_INVOCATION = "tool_invocation",
  LLM_CALL = "llm_call",
  RESOURCE = "resource",
  DELEGATION = "delegation",
  ESCALATION = "escalation",
  BELIEF = "belief",
  ASSUMPTION = "assumption",
  REFLECTION = "reflection",
  LEARNING = "learning",
  OUTCOME = "outcome",
  ERROR = "error",
  RISK = "risk",
  ANOMALY = "anomaly",
  CONFLICT = "conflict",
  CONSTRAINT = "constraint",
  UNKNOWN = "unknown",
}

export enum EdgeKind {
  CAUSES = "causes",
  SUPPORTS = "supports",
  REFUTES = "refutes",
  DEPENDS_ON = "depends_on",
  ENABLES = "enables",
  INHIBITS = "inhibits",
  DECOMPOSES_INTO = "decomposes_into",
  TRANSITIONS_TO = "transitions_to",
  REFLECTS_ON = "reflects_on",
  LEARNS_FROM = "learns_from",
  OPTIMIZES = "optimizes",
  CONFLICTS_WITH = "conflicts_with",
}

export interface TokenMetrics {
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
}

export interface RuntimeNode {
  id: string;
  kind: NodeKind;
  label: string;
  agentId: string;
  sessionId: string;
  projectId: string;
  timestamp: number;
  content?: Record<string, any>;
  confidence?: number;
  cost?: number;
  latency?: number;
  tokens?: TokenMetrics;
}

export interface RuntimeEdge {
  id: string;
  source: string;
  target: string;
  kind: EdgeKind;
  sessionId: string;
  weight?: number;
  timestamp: number;
}
