/**
 * VERI Intelligence Operating System TypeScript SDK
 */

import { VeriClient, VeriClientConfig, sessionLocalStorage, SessionContext } from "./client.js";
import { RuntimeNode, RuntimeEdge, NodeKind, EdgeKind } from "./ir.js";
import { BehaviorContract, ContractViolation } from "./contracts.js";

export * from "./ir.js";
export * from "./contracts.js";
export * from "./client.js";

let globalClient: VeriClient | null = null;

export function init(config: VeriClientConfig): VeriClient {
  globalClient = new VeriClient(config);
  return globalClient;
}

export function getClient(): VeriClient {
  if (!globalClient) {
    throw new Error("VERI Client accessed before init() was invoked.");
  }
  return globalClient;
}

export function session<T>(
  sessionId: string,
  agentId: string,
  projectId: string,
  fn: () => Promise<T>
): Promise<T> {
  const client = getClient();
  const ctx: SessionContext = {
    sessionId,
    agentId,
    projectId,
    costLimit: client.costLimit,
    callLimit: client.callLimit,
    accumulatedCost: 0,
    accumulatedCalls: 0,
    nodes: [],
    edges: [],
  };

  return sessionLocalStorage.run(ctx, fn);
}
