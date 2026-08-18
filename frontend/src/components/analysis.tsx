/**
 * Rendering primitives for one analysis.
 *
 * Shared between the workspace and the public overview on purpose: the sample
 * shown to a visitor is the same component tree, fed a real row out of the
 * algorithmic ledger. There is no marketing mock of the product anywhere.
 *
 * Motion here is all reporting: figures count in when their panel is reached,
 * gates stamp in the order the engine evaluated them, and magnitude bars draw
 * to the distance they represent.
 */
import React from 'react';
import { IconCaution, IconDown, IconUp } from './Icons';
import { RichText } from './RichText';
import { AnimatedNumber, ConfidenceMeter, DeltaBar } from './motion';
import { useInView } from '../hooks';
import type { JsonObject } from '../types';
import {
  asGateMap,
  asNum,
  asStr,
  asStrArray,
  count,
  gateInk,
  inr,
  num,
  titleCase,
  verdictInk,
} from '../format';

// --------------------------------------------------------------- price ladder

type Level = {
  label: string;
  value: number;
  ink: string;
  isPrice?: boolean;
};

/**
 * Every level the engine actually computed, ordered by price.
 *
 * This stands in for a price chart because the backend sends no price series
 * to the client. The previous chart drew a hardcoded shape scaled to the last
 * close, which was decoration standing in for data. These figures are real,
 * and their vertical order is the information: where the last traded price
 * sits against its moving averages and the ATR-derived setup.
 */
export const PriceLadder: React.FC<{
  silver: JsonObject;
  setup?: JsonObject | null;
}> = ({ silver, setup }) => {
  const [ref, inView] = useInView<HTMLTableSectionElement>();
  const price = asNum(silver.current_price);

  if (price == null) {
    return <p className="label py-6 text-center">No price level data on this record</p>;
  }

  const levels: Level[] = [];
  const push = (label: string, raw: unknown, ink: string) => {
    const value = asNum(raw as never);
    if (value != null) levels.push({ label, value, ink });
  };

  if (setup) {
    push('Target 2', setup.target_2, 'text-up');
    push('Target 1', setup.target_1, 'text-up');
  }
  push('SMA 200', silver.sma_200, 'text-fg-2');
  push('SMA 50', silver.sma_50, 'text-fg-2');
  push('SMA 20', silver.sma_20, 'text-fg-2');
  if (setup) {
    push('Entry high', setup.entry_zone_high, 'text-fg-2');
    push('Entry low', setup.entry_zone_low, 'text-fg-2');
    push('Stop loss', setup.stop_loss, 'text-down');
  }

  levels.push({ label: 'Last price', value: price, ink: 'text-fg', isPrice: true });
  levels.sort((a, b) => b.value - a.value);

  const deltas = levels.map((l) => ((l.value - price) / price) * 100);
  const scale = Math.max(...deltas.map(Math.abs), 0.01);

  return (
    <table className="w-full border-collapse text-base">
      <thead>
        <tr className="border-b border-rule text-left">
          <th className="label py-1.5 font-medium">Level</th>
          <th className="label py-1.5 text-right font-medium">Price</th>
          <th className="label w-24 py-1.5 font-medium">Distance</th>
          <th className="label py-1.5 text-right font-medium">%</th>
        </tr>
      </thead>
      <tbody ref={ref}>
        {levels.map((l, i) => {
          const delta = deltas[i];
          return (
            <tr
              key={l.label}
              className={`border-b border-rule/70 last:border-0 ${
                l.isPrice ? 'bg-term-850' : ''
              } ${inView ? 'stamp-in' : 'opacity-0'}`}
              style={inView ? { animationDelay: `${i * 45}ms` } : undefined}
            >
              <td className={`py-1.5 ${l.ink} ${l.isPrice ? 'font-medium' : ''}`}>{l.label}</td>
              <td className={`num py-1.5 pr-3 text-right ${l.ink} ${l.isPrice ? 'font-medium' : ''}`}>
                {inr(l.value)}
              </td>
              <td className="py-1.5 pr-3">
                {!l.isPrice && <DeltaBar pct={delta} scale={scale} active={inView} />}
              </td>
              <td className="num py-1.5 text-right">
                {l.isPrice ? (
                  <span className="text-fg-3">last</span>
                ) : (
                  <span
                    className={`inline-flex items-center justify-end gap-1 ${
                      delta >= 0 ? 'text-up' : 'text-down'
                    }`}
                  >
                    {delta >= 0 ? <IconUp className="h-2 w-2" /> : <IconDown className="h-2 w-2" />}
                    {Math.abs(delta).toFixed(1)}%
                  </span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

// --------------------------------------------------------------- metric table

type MetricRow = {
  label: string;
  note: string;
  value: number | null;
  format: (v: number) => string;
  text?: string;
};

export const MetricTable: React.FC<{ silver: JsonObject }> = ({ silver }) => {
  const [ref, inView] = useInView<HTMLTableSectionElement>();

  const rows: MetricRow[] = [
    {
      label: 'Last price',
      note: 'Latest close in the fetched series',
      value: asNum(silver.current_price),
      format: (v) => inr(v),
    },
    {
      label: 'Volume',
      note: 'Shares traded in the latest bar',
      value: asNum(silver.current_volume),
      format: (v) => count(v),
    },
    {
      label: 'RSI 14',
      note: 'Above 70 overbought, below 30 oversold',
      value: asNum(silver.rsi_14),
      format: (v) => num(v),
    },
    {
      label: 'ATR 14',
      note: 'Average true range, sizes the stop',
      value: asNum(silver.atr_14),
      format: (v) => inr(v),
    },
    {
      label: 'SMA 20',
      note: 'Short trend reference',
      value: asNum(silver.sma_20),
      format: (v) => inr(v),
    },
    {
      label: 'SMA 50',
      note: 'Medium trend reference',
      value: asNum(silver.sma_50),
      format: (v) => inr(v),
    },
  ];

  const sma200 = asNum(silver.sma_200);
  if (sma200 != null) {
    rows.push({
      label: 'SMA 200',
      note: 'Secular trend reference',
      value: sma200,
      format: (v) => inr(v),
    });
  }

  const regime = asStr(silver.market_regime);
  if (regime) {
    rows.push({
      label: 'Market regime',
      note: 'Index position against its own averages',
      value: null,
      format: () => regime,
      text: regime,
    });
  }

  const sectorRs = asNum(silver.stock_vs_sector_rs);
  if (sectorRs != null) {
    rows.push({
      label: 'Sector RS',
      note: 'Return minus sector index return',
      value: sectorRs,
      format: (v) => num(v, 3),
    });
  }

  return (
    <table className="w-full border-collapse text-base">
      <tbody ref={ref}>
        {rows.map((r) => (
          <tr key={r.label} className="border-b border-rule/70 align-baseline last:border-0">
            <td className="py-2 pr-3">
              <span className="block text-fg">{r.label}</span>
              <span className="block text-sm text-fg-3">{r.note}</span>
            </td>
            <td className="num whitespace-nowrap py-2 text-right font-medium text-fg">
              {r.text ? (
                <span className={inView ? 'value-in' : 'opacity-0'}>{r.text}</span>
              ) : (
                <AnimatedNumber value={r.value} format={r.format} active={inView} />
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

// ----------------------------------------------------------------- gate list

export const GateList: React.FC<{ gates: JsonObject | undefined }> = ({ gates }) => {
  const [ref, inView] = useInView<HTMLDListElement>();
  const entries = Object.entries(asGateMap(gates));

  if (entries.length === 0) return <p className="label">No gates recorded</p>;

  return (
    <dl ref={ref} className="grid grid-cols-[1fr_auto] gap-x-4">
      {entries.map(([name, status], i) => (
        <React.Fragment key={name}>
          <dt
            className={`border-b border-rule/70 py-1.5 text-sm text-fg-2 ${
              inView ? 'stamp-in' : 'opacity-0'
            }`}
            style={inView ? { animationDelay: `${i * 60}ms` } : undefined}
          >
            {titleCase(name)}
          </dt>
          <dd
            className={`border-b border-rule/70 py-1.5 text-right text-2xs font-semibold uppercase tracking-label ${gateInk(
              status,
            )} ${inView ? 'stamp-in' : 'opacity-0'}`}
            style={inView ? { animationDelay: `${i * 60 + 30}ms` } : undefined}
          >
            {status}
          </dd>
        </React.Fragment>
      ))}
    </dl>
  );
};

// ---------------------------------------------------------------- trade setup

export const TradeSetup: React.FC<{ setup: JsonObject }> = ({ setup }) => {
  const [ref, inView] = useInView<HTMLDivElement>();
  const size = asNum(setup.suggested_position_size);
  const risk = asNum(setup.risk_per_trade_inr);

  return (
    <div ref={ref} className="panel-sunk p-4">
      <p className="label-accent mb-3">Trade setup</p>
      <div className="grid grid-cols-2 gap-x-6 gap-y-4 text-base">
        <div>
          <span className="label block">Entry zone</span>
          <span className="num text-fg">
            <AnimatedNumber value={asNum(setup.entry_zone_low)} format={(v) => inr(v)} active={inView} />
            {' to '}
            <AnimatedNumber value={asNum(setup.entry_zone_high)} format={(v) => inr(v)} active={inView} />
          </span>
        </div>
        <div>
          <span className="label block">Stop loss</span>
          <span className="num text-down">
            <AnimatedNumber value={asNum(setup.stop_loss)} format={(v) => inr(v)} active={inView} />
          </span>
        </div>
        <div>
          <span className="label block">Targets</span>
          <span className="num text-up">
            <AnimatedNumber value={asNum(setup.target_1)} format={(v) => inr(v)} active={inView} />
            {' / '}
            <AnimatedNumber value={asNum(setup.target_2)} format={(v) => inr(v)} active={inView} />
          </span>
        </div>
        <div>
          <span className="label block">Reward to risk</span>
          <span className="num text-fg">
            <AnimatedNumber
              value={asNum(setup.risk_reward_ratio)}
              format={(v) => `${num(v)}x`}
              active={inView}
            />
          </span>
        </div>
        {size != null && (
          <div>
            <span className="label block">Position size</span>
            <span className="num text-fg">
              <AnimatedNumber value={size} format={(v) => `${count(v)} shares`} active={inView} />
            </span>
          </div>
        )}
        {risk != null && (
          <div>
            <span className="label block">Capital at risk</span>
            <span className="num text-fg">
              <AnimatedNumber value={risk} format={(v) => inr(v, 0)} active={inView} />
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

// -------------------------------------------------------------- verdict block

export const VerdictHead: React.FC<{ gold: JsonObject; ticker: string }> = ({ gold, ticker }) => {
  const [ref, inView] = useInView<HTMLDivElement>();
  const rawScore = asNum(gold.confidence_score);
  const verdict = asStr(gold.verdict) ?? 'No verdict';
  const timeframe = asStr(gold.timeframe) ?? '';

  return (
    <div ref={ref} className="flex flex-wrap items-end justify-between gap-x-8 gap-y-4">
      <div>
        <p className="label-accent mb-2">Gold layer verdict</p>
        <h3
          className={`text-4xl font-extrabold tracking-tight md:text-5xl ${verdictInk(verdict)} ${
            inView ? 'value-in' : 'opacity-0'
          }`}
        >
          {verdict}
        </h3>
        <p className="num mt-2 text-xs text-fg-3">
          {ticker}
          {timeframe ? ` · ${timeframe.replace('_', ' ')}` : ''}
        </p>
      </div>

      <div className="flex flex-col items-start gap-2 sm:items-end">
        <p className="label">Confidence</p>
        <p className="num text-3xl font-medium text-fg">
          <AnimatedNumber
            value={rawScore != null ? rawScore / 10 : null}
            format={(v) => (Number.isNaN(v) ? 'n/a' : v.toFixed(1))}
            active={inView}
          />
          <span className="text-base text-fg-3"> / 10</span>
        </p>
        <ConfidenceMeter score={rawScore} active={inView} />
      </div>
    </div>
  );
};

/** Narrative written by the synthesiser, kept visually subordinate to the arithmetic. */
export const Narrative: React.FC<{ llm: JsonObject }> = ({ llm }) => {
  const reasoning = asStrArray(llm.personalized_reasoning).filter(
    (l) => !/^[A-Z0-9 &]+$/.test(l.trim()),
  );
  const watch = asStrArray(llm.what_to_watch);
  const risk = asStr(llm.risk_warning);

  return (
    <div className="flex flex-col gap-5">
      {reasoning.length > 0 && (
        <div>
          <p className="label mb-2">Thesis and profile fit</p>
          <div className="text-base leading-relaxed text-fg-2">
            <RichText text={reasoning.map((l) => l.replace(/^-\s*/, '')).join('\n')} />
          </div>
        </div>
      )}

      {watch.length > 0 && (
        <div>
          <p className="label mb-2">Conditions to watch</p>
          <ul className="flex flex-col gap-2.5 text-base leading-relaxed text-fg-2">
            {watch.map((line, i) => (
              <li key={i} className="border-l-2 border-rule-strong pl-3.5">
                <RichText text={line.replace(/^-\s*/, '')} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {risk && (
        <div className="panel-sunk flex gap-3 p-3">
          <IconCaution className="mt-0.5 h-4 w-4 shrink-0 text-down" />
          <div>
            <p className="label mb-1 text-down">Risk</p>
            <div className="text-base leading-relaxed text-fg-2"><RichText text={risk} /></div>
          </div>
        </div>
      )}
    </div>
  );
};

export const Disclaimer: React.FC = () => (
  <p className="text-sm leading-relaxed text-fg-3">
    Educational output only. This is not investment advice and INVR is not a SEBI-registered
    investment adviser. Verify every figure independently before committing capital.
  </p>
);
