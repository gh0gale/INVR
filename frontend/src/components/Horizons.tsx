/**
 * Horizon control for the workspace header: the engine's four timeframes as
 * one segmented radio group, so every choice is visible and one tap away
 * (four options, where a native select hid three of them behind a menu).
 * Each segment states what that horizon fetches, from MANIFEST.
 *
 * Keyboard: the group is one tab stop; arrow keys move and select, as a radio
 * group does. It follows the stock in focus, and a change is saved for it.
 */
import React, { useRef } from 'react';
import { HORIZONS, type Timeframe } from '../lib/horizons';
import { manifestFor } from '../pipeline';

const BAR = { '5m': '5-minute', '1d': 'daily', '1wk': 'weekly' } as Record<string, string>;
const PERIOD = { '5d': '5 days', '6mo': '6 months', '1y': '1 year', '5y': '5 years' } as Record<string, string>;

const reads = (t: Timeframe): string => {
  const m = manifestFor(t);
  return `${PERIOD[m.period] ?? m.period} of ${BAR[m.interval] ?? m.interval} bars`;
};

export const HorizonSelect: React.FC<{
  value: Timeframe;
  disabled: boolean;
  onChange: (t: Timeframe) => void;
}> = ({ value, disabled, onChange }) => {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const onKeyDown = (e: React.KeyboardEvent, i: number) => {
    const step = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    const next = (i + step + HORIZONS.length) % HORIZONS.length;
    onChange(HORIZONS[next].value);
    refs.current[next]?.focus();
  };

  return (
    <div
      data-tour="horizon-select"
      className="order-last flex min-w-0 basis-full items-center gap-3 xl:order-none xl:basis-auto"
    >
      <span id="horizon-label" className="label sr-only shrink-0 sm:not-sr-only">
        Horizon
      </span>
      <div
        role="radiogroup"
        aria-labelledby="horizon-label"
        aria-disabled={disabled || undefined}
        className="grid min-w-0 flex-1 grid-cols-4 rounded-[2px] border border-rule-strong sm:flex-none sm:grid-cols-[repeat(4,auto)]"
      >
        {HORIZONS.map((h, i) => {
          const on = h.value === value;
          return (
            <button
              key={h.value}
              ref={(el) => {
                refs.current[i] = el;
              }}
              type="button"
              role="radio"
              aria-checked={on}
              tabIndex={on ? 0 : -1}
              disabled={disabled}
              title={`Reads ${reads(h.value)}`}
              onClick={() => onChange(h.value)}
              onKeyDown={(e) => onKeyDown(e, i)}
              className={`min-h-[44px] min-w-0 truncate whitespace-nowrap border-b-2 px-1 text-2xs font-semibold uppercase tracking-normal sm:px-3.5 sm:tracking-label transition-colors first:rounded-l-[1px] last:rounded-r-[1px] disabled:cursor-not-allowed [&:not(:first-child)]:border-l [&:not(:first-child)]:border-l-rule ${
                on
                  ? 'border-b-accent bg-term-800 text-fg'
                  : 'border-b-transparent text-fg-3 hover:text-fg disabled:hover:text-fg-3'
              }`}
            >
              {h.label}
              <span className="sr-only">, reads {reads(h.value)}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
