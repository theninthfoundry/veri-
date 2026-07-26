/**
 * Behavioral Contracts Engine for JavaScript/TypeScript Agent Systems.
 */

export interface ContractPolicy {
  maxPrice?: number;
  allowedCountry?: string;
  forbiddenKeywords?: string[];
  allowedTools?: string[];
  maxLatencyMs?: number;
}

export class ContractViolationError extends Error {
  constructor(message: string, public readonly rule: string, public readonly value: any) {
    super(`[VERI Contract Violation] ${message}`);
    this.name = 'ContractViolationError';
  }
}

export function enforceContract(policy: ContractPolicy, args: Record<string, any>): void {
  if (policy.maxPrice !== undefined && args.price !== undefined) {
    if (args.price > policy.maxPrice) {
      throw new ContractViolationError(
        `Price $${args.price} exceeds maximum allowed boundary of $${policy.maxPrice}`,
        'maxPrice',
        args.price
      );
    }
  }

  if (policy.allowedCountry !== undefined && args.country !== undefined) {
    if (args.country !== policy.allowedCountry) {
      throw new ContractViolationError(
        `Country '${args.country}' is not permitted (must be '${policy.allowedCountry}')`,
        'allowedCountry',
        args.country
      );
    }
  }

  if (policy.forbiddenKeywords && policy.forbiddenKeywords.length > 0) {
    const textArg = JSON.stringify(args);
    for (const kw of policy.forbiddenKeywords) {
      if (textArg.toLowerCase().includes(kw.toLowerCase())) {
        throw new ContractViolationError(
          `Payload contains forbidden keyword '${kw}'`,
          'forbiddenKeywords',
          kw
        );
      }
    }
  }
}

export function withContract<T extends (...args: any[]) => any>(
  policy: ContractPolicy,
  fn: T,
  paramNames: string[] = ['price', 'country', 'query']
): T {
  return (async (...args: any[]) => {
    const namedArgs: Record<string, any> = {};
    args.forEach((arg, idx) => {
      const key = paramNames[idx] || `arg${idx}`;
      namedArgs[key] = arg;
    });

    enforceContract(policy, namedArgs);

    const start = Date.now();
    const result = await fn(...args);
    const duration = Date.now() - start;

    if (policy.maxLatencyMs !== undefined && duration > policy.maxLatencyMs) {
      throw new ContractViolationError(
        `Execution latency ${duration}ms exceeded limit of ${policy.maxLatencyMs}ms`,
        'maxLatencyMs',
        duration
      );
    }

    return result;
  }) as unknown as T;
}
