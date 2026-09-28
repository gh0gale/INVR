// Run with `npm test` (node --test; Node 24 strips the types itself).
import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  bareSymbol,
  matchSuggestion,
  parseSuggestions,
  toRunTicker,
  type Suggestion,
} from '../src/lib/symbols.ts';
import { HORIZONS, horizonLabel, isTimeframe, resolveHorizon } from '../src/lib/horizons.ts';
import { MANIFEST } from '../src/pipeline.ts';
import { shouldAutoOpenTutor, shouldStartTour } from '../src/lib/runFlow.ts';

const TCS: Suggestion = { symbol: 'TCS.NS', name: 'Tata Consultancy Services Limited', exchange: 'NSE' };
const MM: Suggestion = { symbol: 'M&M.NS', name: 'Mahindra & Mahindra Limited', exchange: 'NSE' };

test('toRunTicker emits exactly the run API ticker form', () => {
  assert.equal(toRunTicker(TCS), 'TCS.NS');
  assert.equal(toRunTicker({ symbol: ' tcs.ns ', exchange: 'NSE' }), 'TCS.NS');
  assert.equal(toRunTicker(MM), 'M&M.NS');
  assert.equal(toRunTicker({ symbol: 'BAJAJ-AUTO.NS', exchange: 'NSE' }), 'BAJAJ-AUTO.NS');
});

test('toRunTicker refuses anything the run API would mangle', () => {
  assert.equal(toRunTicker({ symbol: 'TCS', exchange: 'NSE' }), null);
  assert.equal(toRunTicker({ symbol: 'TCS.BO', exchange: 'NSE' }), null);
  assert.equal(toRunTicker({ symbol: 'TCS.NS.NS', exchange: 'NSE' }), null);
  assert.equal(toRunTicker({ symbol: 'Tata Consultancy', exchange: 'NSE' }), null);
  assert.equal(toRunTicker({ symbol: 'TCS.NS', exchange: 'BSE' as 'NSE' }), null);
});

test('parseSuggestions drops malformed or non-NSE rows from the API', () => {
  const parsed = parseSuggestions([
    TCS,
    { symbol: 'TCS.BO', name: 'x', exchange: 'BSE' },
    { symbol: 'INFY.NS', exchange: 'NSE' },
    null,
    'TCS.NS',
    { symbol: 'infy.ns', name: 'Infosys Limited', exchange: 'NSE' },
  ]);
  assert.deepEqual(
    parsed.map((s) => s.symbol),
    ['TCS.NS', 'INFY.NS'],
  );
  assert.deepEqual(parseSuggestions({ detail: 'error' }), []);
});

test('matchSuggestion accepts only a typed symbol that is in the list', () => {
  assert.equal(matchSuggestion('tcs', [TCS, MM]), TCS);
  assert.equal(matchSuggestion('TCS.NS', [TCS]), TCS);
  assert.equal(matchSuggestion('m&m', [TCS, MM]), MM);
  assert.equal(matchSuggestion('Tata Consultancy Services Limited', [TCS]), null);
  assert.equal(matchSuggestion('TCSX', [TCS]), null);
  assert.equal(matchSuggestion('  ', [TCS]), null);
  assert.equal(bareSymbol('tcs.ns'), 'TCS');
});

test('horizons are exactly the engine timeframes in MANIFEST', () => {
  assert.deepEqual(
    HORIZONS.map((h) => h.value).sort(),
    Object.keys(MANIFEST).sort(),
  );
  assert.equal(horizonLabel('long_term'), 'Long-term');
});

test('resolveHorizon: saved for the stock, then the profile, then swing', () => {
  assert.equal(resolveHorizon('intraday', 'long_term'), 'intraday');
  assert.equal(resolveHorizon(null, 'long_term'), 'long_term');
  assert.equal(resolveHorizon('1 month', 'positional'), 'positional'); // stale or invalid value
  assert.equal(resolveHorizon(undefined, undefined), 'swing');
  assert.equal(isTimeframe('LONG_TERM'), false);
});

test('tutor auto-opens only for the latest successful run', () => {
  const ok = { outcome: 'success' as const, runId: 3, latestRunId: 3, mounted: true, enabled: true };
  assert.equal(shouldAutoOpenTutor(ok), true);
  assert.equal(shouldAutoOpenTutor({ ...ok, outcome: 'failed' }), false);
  assert.equal(shouldAutoOpenTutor({ ...ok, outcome: 'fallback' }), false);
  assert.equal(shouldAutoOpenTutor({ ...ok, latestRunId: 4 }), false);
  assert.equal(shouldAutoOpenTutor({ ...ok, mounted: false }), false);
  assert.equal(shouldAutoOpenTutor({ ...ok, enabled: false }), false);
});

test('tour starts only on first login', () => {
  assert.equal(shouldStartTour(null), false);
  assert.equal(shouldStartTour({ tour_completed_at: null }), true);
  assert.equal(shouldStartTour({}), true);
  assert.equal(shouldStartTour({ tour_completed_at: '2026-09-28T10:00:00Z' }), false);
});
