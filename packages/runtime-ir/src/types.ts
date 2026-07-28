import { Confidence } from './confidence';
import { Capability } from './capabilities';

export interface RuntimeNode {
  id: string;
  kind: string;                        // open string for display: "reasoning", "tool_call", etc.
  capabilities: Capability[];          // what engines can DO with this node — this is what's matched on
  label: string;
  content: Record<string, unknown>;
  confidence?: Confidence;
  cost: number;
  latency: number;
  timestamp: string;
  agentId: string;
  sessionId: string;
  projectId: string;
}

export interface RuntimeEdge {
  id: string;
  sourceId: string;
  targetId: string;
  kind: 'depends_on' | 'causes' | 'conflicts_with' | 'updates' | 'constrains' | string;
  weight?: number;
  metadata?: Record<string, unknown>;
  sessionId?: string;
  edgeConfidenceSource?: 'measured' | 'inferred';
}
