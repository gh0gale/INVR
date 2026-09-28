/**
 * Horizons are the engine's own four timeframes, the keys of PIPELINE_CONFIG
 * (backend/app/pipeline/router.py) and of MANIFEST in src/pipeline.ts. Each
 * stock remembers the one the user last ran it on; a stock with none uses the
 * profile's onboarding timeframe.
 */
export type Timeframe = 'intraday' | 'swing' | 'positional' | 'long_term';

export const HORIZONS: { value: Timeframe; label: string }[] = [
  { value: 'intraday', label: 'Intraday' },
  { value: 'swing', label: 'Swing' },
  { value: 'positional', label: 'Positional' },
  { value: 'long_term', label: 'Long-term' },
];

export const isTimeframe = (v: unknown): v is Timeframe =>
  HORIZONS.some((h) => h.value === v);

export const horizonLabel = (t: string): string =>
  HORIZONS.find((h) => h.value === t)?.label ?? t.replace('_', ' ');

/** The stock's saved horizon, else the profile's, else swing. */
export function resolveHorizon(saved: unknown, profileDefault: unknown): Timeframe {
  if (isTimeframe(saved)) return saved;
  if (isTimeframe(profileDefault)) return profileDefault;
  return 'swing';
}
