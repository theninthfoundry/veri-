/**
 * IRRef<T> transparent wrapper for tracking dataflow provenance in JavaScript/TypeScript.
 * Wraps values returned from tracked functions to automatically attach origin node_id.
 */

export interface IRRefMetadata {
  sourceNodeId: string;
  sourceField: string;
}

export const IR_REF_SYMBOL = Symbol('IRRefMetadata');

export function createIRRef<T extends object | string | number | boolean>(
  value: T,
  sourceNodeId: string,
  sourceField: string = 'content'
): T {
  const metadata: IRRefMetadata = { sourceNodeId, sourceField };

  if (typeof value === 'object' && value !== null) {
    return new Proxy(value as object, {
      get(target, prop, receiver) {
        if (prop === IR_REF_SYMBOL) {
          return metadata;
        }
        return Reflect.get(target, prop, receiver);
      },
    }) as T;
  }

  // Primitive wrapper object fallback
  const wrapper = new String(value) as any;
  wrapper[IR_REF_SYMBOL] = metadata;
  wrapper.valueOf = () => value;
  return wrapper as T;
}

export function extractIRRefMetadata(val: any): IRRefMetadata | null {
  if (val && typeof val === 'object' && IR_REF_SYMBOL in val) {
    return val[IR_REF_SYMBOL] as IRRefMetadata;
  }
  return null;
}
