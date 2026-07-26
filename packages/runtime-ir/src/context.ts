import { RuntimeNode, RuntimeEdge } from './types';
import { VeriClient } from './client';

export class VERIContext {
  private static instance: VERIContext | null = null;
  private client: VeriClient | null = null;
  private nodeStack: RuntimeNode[] = [];

  public static getInstance(): VERIContext {
    if (!VERIContext.instance) {
      VERIContext.instance = new VERIContext();
    }
    return VERIContext.instance;
  }

  public setClient(client: VeriClient): void {
    this.client = client;
  }

  public getActiveNode(): RuntimeNode | null {
    if (this.nodeStack.length === 0) return null;
    return this.nodeStack[this.nodeStack.length - 1];
  }

  public pushNode(node: RuntimeNode): void {
    this.nodeStack.push(node);
    if (this.client) {
      this.client.enqueueNode(node);
    }
  }

  public popNode(): RuntimeNode | null {
    return this.nodeStack.pop() || null;
  }

  public addEdge(edge: RuntimeEdge): void {
    if (this.client) {
      this.client.enqueueEdge(edge);
    }
  }

  public async runStep<T>(
    node: RuntimeNode,
    fn: (node: RuntimeNode) => Promise<T> | T
  ): Promise<T> {
    const parentNode = this.getActiveNode();
    this.pushNode(node);

    if (parentNode) {
      this.addEdge({
        id: `edge-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        sourceId: parentNode.id,
        targetId: node.id,
        kind: 'causes',
      });
    }

    const start = Date.now();
    try {
      const result = await fn(node);
      node.latency = Date.now() - start;
      return result;
    } catch (err: any) {
      node.latency = Date.now() - start;
      const errorNode: RuntimeNode = {
        id: `node-err-${Date.now()}`,
        kind: 'error',
        label: `Error: ${err.message || 'Execution failed'}`,
        content: { error: String(err) },
        confidence: 1.0,
        uncertainty: 0.0,
        evidence: [],
        assumptions: [],
        cost: 0,
        latency: node.latency,
        tokens: { input: 0, output: 0 },
        timestamp: new Date().toISOString(),
        agentId: node.agentId,
        sessionId: node.sessionId,
        projectId: node.projectId,
      };
      this.pushNode(errorNode);
      this.addEdge({
        id: `edge-${Date.now()}`,
        sourceId: node.id,
        targetId: errorNode.id,
        kind: 'causes',
      });
      throw err;
    } finally {
      this.popNode();
    }
  }
}
