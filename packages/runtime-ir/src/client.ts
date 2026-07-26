import { RuntimeNode, RuntimeEdge } from './types';

export interface VeriClientConfig {
  endpoint: string;
  apiKey: string;
  batchSize?: number;
  flushIntervalMs?: number;
  disabled?: boolean;
}

export class VeriClient {
  private endpoint: string;
  private apiKey: string;
  private batchSize: number;
  private flushIntervalMs: number;
  private disabled: boolean;

  private nodeQueue: RuntimeNode[] = [];
  private edgeQueue: RuntimeEdge[] = [];
  private timer: any = null;

  constructor(config: VeriClientConfig) {
    this.endpoint = config.endpoint || 'http://localhost:8080/api/v1/ingest';
    this.apiKey = config.apiKey;
    this.batchSize = config.batchSize || 50;
    this.flushIntervalMs = config.flushIntervalMs || 2000;
    this.disabled = !!config.disabled;

    if (!this.disabled) {
      this.timer = setInterval(() => this.flush(), this.flushIntervalMs);
    }
  }

  public enqueueNode(node: RuntimeNode): void {
    if (this.disabled) return;
    this.nodeQueue.push(node);
    if (this.nodeQueue.length >= this.batchSize) {
      this.flush();
    }
  }

  public enqueueEdge(edge: RuntimeEdge): void {
    if (this.disabled) return;
    this.edgeQueue.push(edge);
    if (this.edgeQueue.length >= this.batchSize) {
      this.flush();
    }
  }

  public async flush(): Promise<void> {
    if (this.disabled || (this.nodeQueue.length === 0 && this.edgeQueue.length === 0)) {
      return;
    }

    const nodesToSend = [...this.nodeQueue];
    const edgesToSend = [...this.edgeQueue];
    this.nodeQueue = [];
    this.edgeQueue = [];

    const payload = {
      nodes: nodesToSend,
      edges: edgesToSend,
      timestamp: new Date().toISOString(),
    };

    try {
      const res = await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        console.warn(`[VERI TS Client] Failed to stream events: ${res.statusText}`);
      }
    } catch (err) {
      console.warn(`[VERI TS Client] Ingest stream network error:`, err);
    }
  }

  public shutdown(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    this.flush();
  }
}
