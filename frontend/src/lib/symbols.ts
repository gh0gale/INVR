/**
 * The mapping layer between the ticker autocomplete and the run API.
 *
 * POST /api/v1/analytics/process takes `ticker` as a plain string. Bronze
 * appends `.NS` to anything without it, so the only safe form is an upper-case
 * NSE symbol with exactly one `.NS`. A BSE `.BO` symbol would reach Yahoo as
 * `X.BO.NS`. Only a value that came back from /api/v1/symbols/search (NSE
 * equities only) may be sent; free text never is.
 */
export type Suggestion = { symbol: string; name: string; exchange: 'NSE' };

const NSE_SYMBOL = /^[A-Z0-9&-]{1,20}\.NS$/;

/** Symbol without the market suffix, for display and for matching typed input. */
export const bareSymbol = (symbol: string): string => symbol.toUpperCase().replace(/\.NS$/, '');

/** Exactly the string the run API expects, or null if the value is not a runnable NSE symbol. */
export function toRunTicker(s: Pick<Suggestion, 'symbol' | 'exchange'>): string | null {
  const symbol = s.symbol.trim().toUpperCase();
  return s.exchange === 'NSE' && NSE_SYMBOL.test(symbol) ? symbol : null;
}

/** Validates the search response at the trust boundary; anything malformed is dropped. */
export function parseSuggestions(json: unknown): Suggestion[] {
  if (!Array.isArray(json)) return [];
  return json.flatMap((item) => {
    const o = item as Record<string, unknown> | null;
    if (typeof o?.symbol !== 'string' || typeof o?.name !== 'string' || o?.exchange !== 'NSE') return [];
    const s: Suggestion = { symbol: o.symbol.toUpperCase(), name: o.name, exchange: 'NSE' };
    return toRunTicker(s) ? [s] : [];
  });
}

/**
 * A typed value that is exactly one suggestion's symbol (with or without
 * `.NS`, any case). Used when the user presses Enter without picking from the
 * list. A company name is not matched: two listings can share one.
 */
export function matchSuggestion(input: string, list: Suggestion[]): Suggestion | null {
  const typed = bareSymbol(input.trim());
  if (!typed) return null;
  return list.find((s) => bareSymbol(s.symbol) === typed) ?? null;
}
