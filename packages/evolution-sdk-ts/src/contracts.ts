/**
 * VERI BehaviorContract Engine — TypeScript Definition
 */

export interface ContractViolation {
  nodeId: string;
  nodeName: string;
  rule: string;
  message: string;
  details?: Record<string, any>;
}

export class BehaviorContract {
  maxCost?: number;
  forbiddenTools: string[];
  requiredExplanations: boolean;

  constructor(options?: {
    maxCost?: number;
    forbiddenTools?: string[];
    requiredExplanations?: boolean;
  }) {
    this.maxCost = options?.maxCost;
    this.forbiddenTools = options?.forbiddenTools || [];
    this.requiredExplanations = options?.requiredExplanations || false;
  }

  verifyTrace(nodes: Array<Record<string, any>>): ContractViolation[] {
    const violations: ContractViolation[] = [];
    let accumulatedCost = 0;

    for (const node of nodes) {
      const nodeName = node.name || node.label || node.id;
      const nodeCost = node.metrics?.cost_usd || node.cost || 0;
      accumulatedCost += nodeCost;

      // Rule 1: Max Cost
      if (this.maxCost !== undefined && accumulatedCost > this.maxCost) {
        violations.push({
          nodeId: node.id,
          nodeName: nodeName,
          rule: "max_cost",
          message: `Accumulated spend $${accumulatedCost.toFixed(4)} exceeds limit of $${this.maxCost.toFixed(2)}`,
          details: { accumulated_cost: accumulatedCost, limit: this.maxCost },
        });
      }

      // Rule 2: Forbidden Tools
      if (this.forbiddenTools.includes(nodeName)) {
        violations.push({
          nodeId: node.id,
          nodeName: nodeName,
          rule: "forbidden_tools",
          message: `Invocation of tool '${nodeName}' is prohibited by contract policy`,
          details: { tool: nodeName, forbidden_list: this.forbiddenTools },
        });
      }
    }

    return violations;
  }
}
