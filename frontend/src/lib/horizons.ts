/**
 * Horizons are the engine's own four timeframes, the keys of PIPELINE_CONFIG
 * (backend/app/pipeline/router.py) and of MANIFEST in src/pipeline.ts. The
 * workspace selector holds the one in use for the session; nothing is stored.
 */
export type Timeframe = 'intraday' | 'swing' | 'positional' | 'long_term';

export const HORIZONS: { value: Timeframe; label: string }[] = [
  { value: 'intraday', label: 'Intraday' },
  { value: 'swing', label: 'Swing' },
  { value: 'positional', label: 'Positional' },
  { value: 'long_term', label: 'Long-term' },
];

/** What the selector shows until the user picks one. */
export const DEFAULT_HORIZON: Timeframe = 'swing';

export const horizonLabel = (t: string): string =>
  HORIZONS.find((h) => h.value === t)?.label ?? t.replace('_', ' ');
