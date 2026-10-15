/**
 * Single source for the backend origin. Previously this literal was repeated
 * in four call sites, which made the documented VITE_API_BASE_URL dead config.
 */
import { parseSuggestions, type Suggestion } from './lib/symbols';

export const API_BASE: string =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiUrl = (path: string): string =>
  `${API_BASE.replace(/\/$/, '')}${path}`;

/** Authenticated JSON call. Throws an Error carrying the server's `detail`. */
export async function apiJson<T>(
  path: string,
  token: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: unknown };
    const detail = typeof body.detail === 'string' ? body.detail : null;
    throw new Error(detail ?? `The request failed (error ${response.status}).`);
  }
  return (response.status === 204 ? null : await response.json()) as T;
}

/** NSE listings matching a query, validated at the boundary (src/lib/symbols.ts). */
export const searchSymbols = async (
  q: string,
  token: string,
  signal?: AbortSignal,
): Promise<Suggestion[]> =>
  parseSuggestions(
    await apiJson<unknown>(`/api/v1/symbols/search?q=${encodeURIComponent(q)}`, token, { signal }),
  );
