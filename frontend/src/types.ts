/**
 * Shapes for data that arrives untyped.
 *
 * `silver_state` and `gold_verdict` are jsonb columns whose contents vary by
 * timeframe, so they are modelled as JSON rather than pretending to a fixed
 * interface. Read them through the accessors in `format.ts`, which narrow a
 * JsonValue to the type a component actually needs.
 */
export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export type JsonObject = { [key: string]: JsonValue };

export type LedgerRow = {
  log_id?: string;
  ticker: string;
  timeframe: string;
  date?: string;
  created_at?: string;
  actual_outcome?: string;
  silver_state: JsonObject;
  gold_verdict: JsonObject;
};

/** Pulls a displayable message off an unknown throw without asserting `any`. */
export function errorMessage(err: unknown, fallback: string): string {
  if (err instanceof Error && err.message) return err.message;
  if (typeof err === 'string' && err) return err;
  return fallback;
}
