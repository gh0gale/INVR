/**
 * Ticker tape of real ledger rows.
 *
 * The motion is the point: a tape scrolls because there is more on it than
 * fits, which is the same reason a physical one does. It renders only what the
 * engine has actually recorded, so it shows last price and verdict and stops
 * there. It does not show a change percentage, because the ledger stores no
 * previous close and inventing one would be the fake-demo failure in miniature.
 */
import React from 'react';
import type { LedgerRow } from '../types';
import { asNum, asStr, inr, verdictInk } from '../format';

type TapeItem = {
  ticker: string;
  price: number | null;
  verdict: string;
  score: number | null;
};

const TapeRow: React.FC<{ items: TapeItem[]; ariaHidden: boolean }> = ({ items, ariaHidden }) => (
  <ul className="flex shrink-0 items-center" aria-hidden={ariaHidden || undefined}>
    {items.map((item, i) => (
      <li
        key={`${item.ticker}-${i}`}
        className="flex items-center gap-3 whitespace-nowrap border-r border-rule px-5 py-2"
      >
        <span className="num text-sm font-medium text-fg">{item.ticker}</span>
        {item.price != null && (
          <span className="num text-sm text-fg-2">{inr(item.price)}</span>
        )}
        <span
          className={`text-2xs font-semibold uppercase tracking-label ${verdictInk(
            item.verdict,
          )}`}
        >
          {item.verdict}
        </span>
        {item.score != null && (
          <span className="num text-xs text-fg-3">{(item.score / 10).toFixed(1)}</span>
        )}
      </li>
    ))}
  </ul>
);

export const TickerTape: React.FC<{ rows: LedgerRow[] }> = ({ rows }) => {
  const items: TapeItem[] = rows.map((r) => ({
    ticker: r.ticker.split('.')[0],
    price: asNum(r.silver_state?.current_price),
    verdict: asStr(r.gold_verdict?.verdict) ?? 'NO VERDICT',
    score: asNum(r.gold_verdict?.confidence_score),
  }));

  if (items.length === 0) return null;

  // Pace the loop by content length so a long tape does not race.
  const durationMs = Math.max(28, items.length * 7) * 1000;

  return (
    <div
      className="tape overflow-hidden border-y border-rule bg-term-900"
      style={{ ['--tape-duration' as string]: `${durationMs}ms` }}
    >
      <div className="flex items-center justify-between gap-4">
        <span className="label-accent shrink-0 border-r border-rule px-4 py-2">
          Ledger tape
        </span>
        <div className="relative flex-1 overflow-hidden">
          <div className="tape-track flex w-max">
            <TapeRow items={items} ariaHidden={false} />
            {/* Second copy makes the 50% translate loop seamless. */}
            <TapeRow items={items} ariaHidden={true} />
          </div>
        </div>
      </div>
    </div>
  );
};
