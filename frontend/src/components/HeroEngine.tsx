/**
 * Hero signal chain.
 *
 * The product's whole claim is that a verdict comes out of a fixed sequence of
 * stages rather than out of asking a model what it thinks. This shows that
 * sequence running: a ticker enters, data is fetched, arithmetic is computed,
 * gates are checked, a verdict falls out. It replays a real recorded run from
 * the ledger, and says so, so nobody reads it as a live feed.
 *
 * With no ledger row available it renders the same chain with field names and
 * blank values rather than inventing numbers.
 */
import React, { useEffect, useRef, useState } from 'react';
import type { LedgerRow } from '../types';
import {
  asGateMap,
  asNum,
  asObj,
  asStr,
  gateInk,
  inr,
  num,
  titleCase,
  verdictInk,
} from '../format';
import { ConfidenceMeter } from './motion';
import { manifestFor } from '../pipeline';

const STATION_COUNT = 5;

/** Milliseconds each station holds before handing off. The verdict holds longest. */
const DWELL = [1500, 1900, 2100, 2400, 3600];

type Field = { k: string; v: string; ink?: string };

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true;

export const HeroEngine: React.FC<{ row: LedgerRow | null; loading?: boolean }> = ({
  row,
  loading = false,
}) => {
  const [reduced] = useState(prefersReducedMotion);
  const [step, setStep] = useState(reduced ? STATION_COUNT - 1 : 0);
  const [paused, setPaused] = useState(false);
  const timer = useRef<number | null>(null);

  // Advance the chain, then start over. Held while a reader is hovering or has
  // focus inside it, so a station can actually be read.
  useEffect(() => {
    if (reduced || paused || loading) return;

    timer.current = window.setTimeout(
      () => setStep((s) => (s + 1) % STATION_COUNT),
      DWELL[step] ?? 2000,
    );

    return () => {
      if (timer.current != null) window.clearTimeout(timer.current);
    };
  }, [step, paused, reduced, loading]);

  const silver = row?.silver_state;
  const gold = row?.gold_verdict;
  const setup = gold ? asObj(gold.trade_setup) : null;
  const timeframe = String(row?.timeframe || 'swing');
  const manifest = manifestFor(timeframe);
  const gates = Object.entries(asGateMap(gold?.gate_results)).slice(0, 4);
  const verdict = asStr(gold?.verdict);
  const score = asNum(gold?.confidence_score);

  const blank = 'not run';

  const stations: { n: string; name: string; caption: string; fields: Field[] }[] = [
    {
      n: '00',
      name: 'Input',
      caption: 'You type a ticker. Nothing is linked to a broker.',
      fields: [
        { k: 'Symbol', v: row ? row.ticker : blank, ink: 'text-fg' },
        { k: 'Horizon', v: row ? timeframe.replace('_', ' ') : blank },
        { k: 'Capital', v: 'your profile' },
      ],
    },
    {
      n: '01',
      name: 'Bronze',
      caption: 'Fetches only what this horizon actually needs.',
      fields: [
        { k: 'Series', v: row ? manifest.period + ' / ' + manifest.interval : blank },
        ...manifest.needs.slice(0, 2).map((need) => ({ k: need, v: row ? 'fetched' : blank })),
      ],
    },
    {
      n: '02',
      name: 'Silver',
      caption: 'Fixed arithmetic over the series. No opinions.',
      fields: [
        { k: 'RSI 14', v: silver ? num(asNum(silver.rsi_14)) : blank },
        { k: 'ATR 14', v: silver ? inr(asNum(silver.atr_14)) : blank },
        { k: 'SMA 50', v: silver ? inr(asNum(silver.sma_50)) : blank },
      ],
    },
    {
      n: '03',
      name: 'Gold',
      caption: 'Each gate is one figure against one threshold.',
      fields:
        gates.length > 0
          ? gates.map(([name, status]) => ({
              k: titleCase(name),
              v: status,
              ink: gateInk(status),
            }))
          : [
              { k: 'Trend', v: blank },
              { k: 'Momentum', v: blank },
              { k: 'Volume', v: blank },
            ],
    },
    {
      n: '04',
      name: 'Verdict',
      caption: 'One of five, with the levels to act on it.',
      fields: [
        { k: 'Call', v: verdict ?? blank, ink: verdict ? verdictInk(verdict) : undefined },
        { k: 'Entry', v: setup ? inr(asNum(setup.entry_zone_low)) : row ? 'no setup' : blank },
        {
          k: 'Stop',
          v: setup ? inr(asNum(setup.stop_loss)) : row ? 'no setup' : blank,
          ink: setup ? 'text-down' : undefined,
        },
      ],
    },
  ];

  return (
    <figure
      className="m-0"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={() => setPaused(false)}
    >
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <figcaption className="label-accent">
          {row ? 'Replay of a recorded run' : 'The sequence, with no run loaded'}
        </figcaption>
        <p className="label">
          {row?.ticker ? row.ticker + ' / ' + (row.date ?? 'ledger') : 'awaiting first analysis'}
        </p>
      </div>

      <div className="flex flex-col lg:flex-row lg:items-stretch">
        {stations.map((s, i) => {
          const active = reduced || step >= i;
          const current = !reduced && step === i;

          return (
            <React.Fragment key={s.n}>
              <div
                className={
                  'min-w-0 flex-1 border p-4 transition-colors duration-500 ' +
                  (current
                    ? 'border-accent bg-term-900'
                    : active
                      ? 'border-rule bg-term-900'
                      : 'border-rule bg-term-950')
                }
              >
                <div className="mb-2.5 flex items-baseline gap-2.5">
                  <span
                    className={
                      'num text-xs transition-colors duration-500 ' +
                      (current ? 'text-accent' : 'text-fg-3')
                    }
                  >
                    {s.n}
                  </span>
                  <span
                    className={
                      'text-lg font-bold tracking-tight transition-colors duration-500 ' +
                      (active ? 'text-fg' : 'text-fg-3')
                    }
                  >
                    {s.name}
                  </span>
                </div>

                <p className="mb-3.5 min-h-[2.6rem] text-xs leading-snug text-fg-3">
                  {s.caption}
                </p>

                <dl className="flex flex-col gap-2">
                  {s.fields.map((f, fi) => (
                    <div
                      key={f.k}
                      className={
                        'flex items-baseline justify-between gap-3 border-b border-rule/60 pb-2 last:border-0 ' +
                        (active ? 'chain-in' : 'opacity-0')
                      }
                      style={active && !reduced ? { animationDelay: fi * 110 + 'ms' } : undefined}
                    >
                      <dt className="truncate text-xs text-fg-3">{f.k}</dt>
                      <dd className={'num shrink-0 text-xs ' + (f.ink ?? 'text-fg-2')}>{f.v}</dd>
                    </div>
                  ))}
                </dl>

                {i === STATION_COUNT - 1 && (
                  <div className={'mt-3.5 ' + (active ? 'chain-in' : 'opacity-0')}>
                    <ConfidenceMeter score={score} active={active} />
                  </div>
                )}
              </div>

              {i < stations.length - 1 && (
                <div
                  className="flex shrink-0 items-center justify-center lg:w-6"
                  aria-hidden="true"
                >
                  {/* Stacked layout: the handoff runs downward. */}
                  <span
                    className={
                      'block h-4 w-px lg:hidden ' + (step > i ? 'bg-accent' : 'bg-rule-strong')
                    }
                  />
                  {/* Row layout: the handoff runs left to right, and draws that way. */}
                  <span
                    className={
                      'hidden h-px w-full lg:block ' +
                      (step > i ? 'link-draw bg-accent' : 'bg-rule-strong')
                    }
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      <p className="mt-4 max-w-3xl text-xs leading-relaxed text-fg-3">
        {row
          ? 'Every figure above is read from the algorithmic ledger. The stages replay in the order the engine ran them. Hover to hold a stage.'
          : 'No analysis has been recorded yet, so the values are blank rather than invented. Sign in and run a ticker to fill them.'}
      </p>
    </figure>
  );
};
