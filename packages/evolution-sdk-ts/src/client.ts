/**
 * VERI Runtime Client & AsyncLocalStorage Context Tracker — TypeScript
 */

import { AsyncLocalStorage } from "async_hooks";
import { RuntimeNode, RuntimeEdge, NodeKind, EdgeKind } from "./ir.js";
import { BehaviorContract, ContractViolation } from "./contracts.js";

export interface SessionContext {
  sessionId: string;
  agentId: string;
  projectId: string;
  costLimit: number;
  callLimit: number;
  accumulatedCost: number;
  accumulatedCalls: number;
  nodes: RuntimeNode[];
  edges: RuntimeEdge[];
}

export const sessionLocalStorage = new AsyncLocalStorage<SessionContext>();

export interface VeriClientConfig {
  apiKey: string;
  endpoint?: string;
  costLimit?: number;
  callLimit?: number;
  disabled?: boolean;
}

export class VeriClient {
  apiKey: string;
  endpoint: string;
  costLimit: number;
  callLimit: number;
  disabled: boolean;

  constructor(config: VeriClientConfig) {
    this.apiKey = config.apiKey;
    this.endpoint = config.endpoint || "http://localhost:8080/api/v1/ingest";
    this.costLimit = config.costLimit || 5.0;
    this.callLimit = config.callLimit || 100;
    this.disabled = config.disabled || false;
  }

  async emitNode(node: RuntimeNode): Promise<void> {
    if (this.disabled) return;
    const ctx = sessionLocalStorage.getStore();
    if (ctx) {
      ctx.nodes.push(node);
      ctx.accumulatedCost += node.cost || 0;
      if (node.kind === NodeKind.LLM_CALL) {
        ctx.accumulatedCalls += 1;
      }
    }
  }

  async emitEdge(edge: RuntimeEdge): Promise<void> {
    if (this.disabled) return;
    const ctx = sessionLocalStorage.getStore();
    if (ctx) {
      ctx.edges.push(edge);
    }
  }
}
