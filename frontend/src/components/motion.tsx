/**
 * Motion components.
 *
 * Each reports a fact: a value arrived, a magnitude, a score on a scale. There
 * is deliberately no generic reveal-on-scroll wrapper here, because that is the
 * decoration the design rules prohibit. Scroll-position hooks live in
 * `src/hooks.ts`.
 */
import React, { useEffect, useRef, useState } from 'react';

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true;

const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

/**
 * Counts to a figure rather than snapping to it, so the eye registers that the
 * number is new. The destination is assigned rather than interpolated on the
 * final frame, so a price is never displayed a paisa short.
 */
export const AnimatedNumber: React.FC<{
  value: number | null;
  format: (v: number) => string;
  active?: boolean;
  durationMs?: number;
  className?: string;
}> = ({ value, format, active = true, durationMs = 700, className }) => {
  // Captured once: a reader who has asked for less motion gets the figure flat.
  const [reduced] = useState(prefersReducedMotion);
  const [shown, setShown] = useState<number | null>(null);
  const frame = useRef<number | null>(null);

  useEffect(() => {
    if (value == null || !active || reduced) return;

    const start = performance.now();

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      if (t >= 1) {
        setShown(value);
        frame.current = null;
        return;
      }
      setShown(value * easeOutCubic(t));
      frame.current = requestAnimationFrame(tick);
    };

    frame.current = requestAnimationFrame(tick);
    return () => {
      if (frame.current != null) cancelAnimationFrame(frame.current);
    };
  }, [value, active, reduced, durationMs]);

  if (value == null) return <span className={className}>{format(NaN)}</span>;
  if (reduced) return <span className={className}>{format(value)}</span>;

  // Before the panel is reached, hold the destination but keep it invisible.
  // Reserving the width stops the column jumping, and a partial figure is
  // never shown as though it were the real one.
  if (!active) {
    return (
      <span className={className} style={{ visibility: 'hidden' }} aria-hidden="true">
        {format(value)}
      </span>
    );
  }

  return <span className={className}>{format(shown ?? 0)}</span>;
};

/**
 * Segmented confidence meter. Ten cells filled to the score, lighting in
 * sequence, so the reading is legible without reading the figure.
 */
export const ConfidenceMeter: React.FC<{
  /** Gold-layer confidence, 0 to 100. */
  score: number | null;
  active?: boolean;
}> = ({ score, active = true }) => {
  const filled = score == null ? 0 : Math.round((score / 100) * 10);
  const reduced = prefersReducedMotion();

  return (
    <div
      className="flex items-center gap-1"
      role="img"
      aria-label={
        score == null
          ? 'Confidence unavailable'
          : `Confidence ${(score / 10).toFixed(1)} of 10`
      }
    >
      {Array.from({ length: 10 }).map((_, i) => {
        const on = active && i < filled;
        return (
          <span
            key={i}
            className={`h-3 w-2 border transition-colors duration-300 ${
              on ? 'border-accent bg-accent' : 'border-rule-strong bg-transparent'
            }`}
            style={on && !reduced ? { transitionDelay: `${i * 45}ms` } : undefined}
          />
        );
      })}
    </div>
  );
};

/**
 * Signed magnitude bar drawn from a centre line. Direction is the side, size is
 * the width. Used for distance from the last traded price.
 */
export const DeltaBar: React.FC<{
  /** Signed percentage. */
  pct: number;
  /** Largest absolute percentage in the set, for a shared scale. */
  scale: number;
  active?: boolean;
}> = ({ pct, scale, active = true }) => {
  const magnitude = scale > 0 ? Math.min(100, (Math.abs(pct) / scale) * 100) : 0;
  const width = active ? `${magnitude / 2}%` : '0%';
  const above = pct >= 0;

  return (
    <span className="relative flex h-1.5 w-full items-center" aria-hidden="true">
      <span className="absolute left-1/2 top-0 h-full w-px bg-rule-strong" />
      <span
        className={`measure absolute h-full ${above ? 'left-1/2 bg-up' : 'right-1/2 bg-down'}`}
        style={{ width }}
      />
    </span>
  );
};
