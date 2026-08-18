import type { JsonObject, JsonValue } from './types';

// ------------------------------------------------------------------ narrowing

export const asNum = (v: JsonValue | undefined): number | null =>
  typeof v === 'number' && Number.isFinite(v) ? v : null;

export const asStr = (v: JsonValue | undefined): string | null =>
  typeof v === 'string' && v.length > 0 ? v : null;

export const asObj = (v: JsonValue | undefined): JsonObject | null =>
  v !== null && typeof v === 'object' && !Array.isArray(v) ? (v as JsonObject) : null;

export const asStrArray = (v: JsonValue | undefined): string[] =>
  Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string') : [];

/** Gate maps are string to status string. */
export const asGateMap = (v: JsonValue | undefined): Record<string, string> => {
  const obj = asObj(v);
  if (!obj) return {};
  const out: Record<string, string> = {};
  for (const [k, val] of Object.entries(obj)) {
    if (typeof val === 'string') out[k] = val;
  }
  return out;
};

// ----------------------------------------------------------------- formatting

export const inr = (v: number | null | undefined, digits = 2): string =>
  v == null || Number.isNaN(v)
    ? 'n/a'
    : `₹${v.toLocaleString('en-IN', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      })}`;

export const num = (v: number | null | undefined, digits = 2): string =>
  v == null || Number.isNaN(v) ? 'n/a' : v.toFixed(digits);

export const count = (v: number | null | undefined): string =>
  v == null || Number.isNaN(v) ? 'n/a' : Math.round(v).toLocaleString('en-IN');

export const titleCase = (s: string): string =>
  s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

/**
 * Verdicts are a closed vocabulary from the Gold layer. Each maps to exactly
 * one ink so colour carries meaning rather than variety.
 */
export function verdictInk(verdict: string | null): string {
  switch ((verdict || '').toUpperCase()) {
    case 'STRONG BUY':
    case 'BUY ON DIP':
      return 'text-up';
    case 'CAUTION':
    case 'AVOID':
      return 'text-down';
    case 'MONITOR':
      return 'text-note';
    default:
      return 'text-fg';
  }
}

export function gateInk(status: string): string {
  switch (status) {
    case 'PASS':
      return 'text-up';
    case 'WARN':
      return 'text-accent';
    case 'FAIL':
    case 'BLOCK':
      return 'text-down';
    default:
      return 'text-fg-3';
  }
}
