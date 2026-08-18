/**
 * Mirrors PIPELINE_CONFIG in backend/app/pipeline/router.py.
 *
 * Kept client side so the overview can state what a given horizon actually
 * fetched. If that file changes, change this too.
 */
export type Manifest = {
  period: string;
  interval: string;
  needs: string[];
};

export const MANIFEST: Record<string, Manifest> = {
  intraday: { period: '5d', interval: '5m', needs: ['Circuit state'] },
  swing: {
    period: '6mo',
    interval: '1d',
    needs: ['Sector index', 'Fundamentals', 'Circuit state'],
  },
  positional: {
    period: '1y',
    interval: '1d',
    needs: ['Sector index', 'Fundamentals', 'Circuit state'],
  },
  long_term: { period: '5y', interval: '1wk', needs: ['Sector index', 'Fundamentals'] },
};

export const manifestFor = (timeframe: string): Manifest =>
  MANIFEST[timeframe] ?? MANIFEST.swing;
