/**
 * Scroll narrative: one real analysis, advanced a layer at a time.
 *
 * The sticky panel holds the data and the scrolling column holds the prose, so
 * scrolling is what moves the run from ingestion to a written verdict. The
 * motion carries the sequence of the pipeline, which is the one thing a static
 * screenshot of this product cannot show.
 *
 * Every figure comes from the ledger row passed in. If there is no row, the
 * caller renders an honest empty state instead of this component.
 */
import React from 'react';
import type { LedgerRow } from '../types';
import { asNum, asObj, asStr, inr } from '../format';
import { useActiveSection } from '../hooks';
import { manifestFor } from '../pipeline';
import { GateList, MetricTable, PriceLadder, TradeSetup, VerdictHead } from './analysis';

const STAGES = [
  {
    n: '01',
    name: 'Bronze',
    role: 'Ingestion',
    body:
      'The horizon decides the request. A swing run pulls six months of daily bars plus the sector index, fundamentals and the circuit state; an intraday run pulls five days of five-minute bars and skips fundamentals entirely. Optional fetches run concurrently and are allowed to fail, so a missing sector index degrades the analysis rather than killing it.',
  },
  {
    n: '02',
    name: 'Silver',
    role: 'Arithmetic',
    body:
      'Vectorised pandas over the series: moving averages, Wilder RSI and ATR, relative strength against the sector index, and the fundamental ratios this horizon calls for. No opinions, no network calls, no thresholds. This is the layer the unit tests cover, because it is the only one where a number can be simply right or wrong.',
  },
  {
    n: '03',
    name: 'Gold',
    role: 'Decision',
    body:
      'Each gate compares one Silver figure against one threshold and returns pass, warn, fail or block. The verdict falls out of those counts, then three overrides run in order: a breakout without institutional volume is demoted, a dip that is not near a moving-average floor is demoted, and a bearish market regime suppresses every bullish verdict. Confidence is a weighted pass ratio, nothing more.',
  },
  {
    n: '04',
    name: 'Setup and ledger',
    role: 'Output',
    body:
      'A strong buy on a tradeable horizon gets entry, stop and target levels derived from ATR, sized so a stop-out costs two percent of stated capital. The whole run is written to the ledger with its trace ID, which is what makes it scoreable against real prices once the horizon matures.',
  },
];

export const PipelineScroller: React.FC<{ row: LedgerRow }> = ({ row }) => {
  const [register, active] = useActiveSection(STAGES.length);

  const silver = row.silver_state;
  const gold = row.gold_verdict;
  const setup = asObj(gold.trade_setup);
  const timeframe = String(row.timeframe || 'swing');
  const manifest = manifestFor(timeframe);
  const stage = STAGES[active];

  return (
    <div className="md:grid md:grid-cols-2 md:gap-12">
      {/* -------------------------------------------------- sticky data panel */}
      <div className="sticky top-0 z-20 -mx-5 px-5 py-4 md:top-16 md:mx-0 md:h-[calc(100vh-8rem)] md:px-0 md:py-0">
        <div className="panel flex h-full max-h-[46vh] flex-col overflow-hidden bg-term-950 md:max-h-none">
          {/* Stage indicator */}
          <div className="flex shrink-0 items-center justify-between border-b border-rule px-4 py-3">
            <div className="flex items-baseline gap-3">
              <span className="num text-accent">{stage.n}</span>
              <span className="text-base font-bold tracking-tight text-fg">{stage.name}</span>
              <span className="label hidden sm:inline">{stage.role}</span>
            </div>
            <div className="flex gap-1" aria-hidden="true">
              {STAGES.map((s, i) => (
                <span
                  key={s.n}
                  className={`h-1 w-6 transition-colors duration-300 ${
                    i <= active ? 'bg-accent' : 'bg-rule-strong'
                  }`}
                />
              ))}
            </div>
          </div>

          <div className="flex shrink-0 items-baseline justify-between border-b border-rule px-4 py-2">
            <span className="num text-sm text-fg">{row.ticker}</span>
            <span className="label">
              {timeframe.replace('_', ' ')}
              {row.date ? ` · ${row.date}` : ''}
            </span>
          </div>

          <div className="no-scrollbar flex-1 overflow-y-auto p-4">
            {active === 0 && (
              <dl className="flex flex-col">
                <div className="flex items-baseline justify-between border-b border-rule/70 py-2">
                  <dt className="text-sm text-fg-2">Price series</dt>
                  <dd className="num text-sm text-fg">
                    {manifest.period} at {manifest.interval}
                  </dd>
                </div>
                {manifest.needs.map((need) => (
                  <div
                    key={need}
                    className="flex items-baseline justify-between border-b border-rule/70 py-2"
                  >
                    <dt className="text-sm text-fg-2">{need}</dt>
                    <dd className="label-accent">requested</dd>
                  </div>
                ))}
                <div className="flex items-baseline justify-between border-b border-rule/70 py-2">
                  <dt className="text-sm text-fg-2">Institutional flow</dt>
                  <dd className="label">not connected</dd>
                </div>
                <p className="mt-4 text-xs leading-relaxed text-fg-3">
                  Bronze output is a raw payload. Nothing has been judged yet.
                </p>
              </dl>
            )}

            {active === 1 && <MetricTable silver={silver} />}

            {active === 2 && (
              <div className="flex flex-col gap-5">
                <VerdictHead gold={gold} ticker={row.ticker} />
                <GateList gates={asObj(gold.gate_results) ?? {}} />
              </div>
            )}

            {active === 3 && (
              <div className="flex flex-col gap-5">
                {setup ? (
                  <TradeSetup setup={setup} />
                ) : (
                  <p className="text-sm leading-relaxed text-fg-2">
                    No trade setup on this run. Levels are only generated for a strong buy on
                    the intraday, swing and positional horizons, so their absence is itself a
                    result.
                  </p>
                )}
                <PriceLadder silver={silver} setup={setup} />
              </div>
            )}
          </div>

          <div className="shrink-0 border-t border-rule px-4 py-2">
            <p className="label">
              {active === 3 ? 'Written to algorithmic_ledger' : 'Live row from the ledger'}
            </p>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------ scrolling prose */}
      <div>
        {STAGES.map((s, i) => (
          <section
            key={s.n}
            ref={register(i)}
            className="flex min-h-[72vh] flex-col justify-center py-12 md:min-h-[80vh]"
          >
            <div className="flex items-baseline gap-4">
              <span
                className={`num text-sm transition-colors duration-300 ${
                  i === active ? 'text-accent' : 'text-fg-3'
                }`}
              >
                {s.n}
              </span>
              <h3
                className={`text-2xl font-bold tracking-tight transition-colors duration-300 md:text-3xl ${
                  i === active ? 'text-fg' : 'text-fg-3'
                }`}
              >
                {s.name}
              </h3>
              <span className="label">{s.role}</span>
            </div>
            <p
              className={`mt-5 max-w-xl border-l pl-5 text-lg leading-relaxed transition-colors duration-300 ${
                i === active ? 'border-accent text-fg-2' : 'border-rule text-fg-3'
              }`}
            >
              {s.body}
            </p>

            {/* One concrete figure per stage, so the prose is anchored. */}
            <div className="mt-6 flex flex-wrap gap-x-10 gap-y-3">
              {i === 0 && (
                <Fact label="Ticker" value={row.ticker} />
              )}
              {i === 1 && (
                <>
                  <Fact label="Last price" value={inr(asNum(silver.current_price))} />
                  <Fact label="RSI 14" value={asNum(silver.rsi_14)?.toFixed(2) ?? 'n/a'} />
                </>
              )}
              {i === 2 && (
                <>
                  <Fact label="Verdict" value={asStr(gold.verdict) ?? 'n/a'} />
                  <Fact
                    label="Gates run"
                    value={String(Object.keys(asObj(gold.gate_results) ?? {}).length)}
                  />
                </>
              )}
              {i === 3 && (
                <>
                  <Fact label="Setup" value={setup ? 'generated' : 'not generated'} />
                  <Fact label="Recorded" value={row.date ?? 'n/a'} />
                </>
              )}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
};

const Fact: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <p className="label mb-1">{label}</p>
    <p className="num text-sm text-fg">{value}</p>
  </div>
);
