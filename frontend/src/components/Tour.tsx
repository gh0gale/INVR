/**
 * First-login walkthrough of the workspace.
 *
 * Each step points at an element marked `data-tour="..."`: everything except
 * that element is blurred, the element gets an amber keyline, and a small panel
 * beside it says what it does. No library. Steps whose element is absent or
 * hidden at this screen size are skipped, so the same list works on a phone
 * and a laptop.
 *
 * The blur is the one sanctioned `backdrop-*` in the product (design rule 8),
 * at the user's request on 2026-09-28: it exists only while the tour runs and
 * reports which element is being explained. It is a blur with no tint, so no
 * translucent colour layer is added.
 */
import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { prefersReducedMotion } from '../hooks';
import type { TourStep } from '../lib/tourSteps';

const GAP = 10;
const PANEL_W = 352; // 22rem
const EDGE = 16;

// The first rendered match: some targets exist twice (the recent-runs sidebar
// from lg, the recent-runs row below it) with one hidden by CSS.
const findTarget = (step: TourStep): HTMLElement | null =>
  Array.from(document.querySelectorAll<HTMLElement>(`[data-tour="${step.target}"]`)).find(
    (el) => el.getClientRects().length > 0,
  ) ?? null;

export const Tour: React.FC<{ steps: TourStep[]; onDone: (how: 'finished' | 'skipped') => void }> = ({
  steps,
  onDone,
}) => {
  // The steps visible in this layout, resolved once after the first commit so
  // targets rendered in the same pass as the tour are found.
  const [resolved, setResolved] = useState<TourStep[] | null>(null);
  const visible = resolved ?? [];
  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [panelH, setPanelH] = useState(0);
  const panelRef = useRef<HTMLDivElement>(null);
  const nextRef = useRef<HTMLButtonElement>(null);
  const step = visible[index];
  const last = index === visible.length - 1;

  const measure = useCallback(() => {
    const el = step ? findTarget(step) : null;
    setRect(el ? el.getBoundingClientRect() : null);
  }, [step]);

  /* eslint-disable react-hooks/set-state-in-effect */
  useLayoutEffect(() => {
    setResolved(steps.filter((s) => findTarget(s)));
  }, [steps]);
  /* eslint-enable react-hooks/set-state-in-effect */

  // Nothing to show on this layout: close as finished rather than hang.
  useEffect(() => {
    if (resolved && resolved.length === 0) onDone('finished');
  }, [resolved, onDone]);

  // Reads layout from the DOM, the external system here, so the state it sets
  // is a measurement rather than derived React state.
  /* eslint-disable react-hooks/set-state-in-effect */
  useLayoutEffect(() => {
    const el = step ? findTarget(step) : null;
    el?.scrollIntoView({ block: 'nearest', behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
    measure();
    nextRef.current?.focus();
  }, [step, measure]);

  useLayoutEffect(() => {
    setPanelH(panelRef.current?.offsetHeight ?? 0);
  }, [index, rect]);
  /* eslint-enable react-hooks/set-state-in-effect */

  // Focus goes back where it was when the tour closes.
  useEffect(() => {
    const before = document.activeElement as HTMLElement | null;
    return () => before?.focus?.();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onDone('skipped');
      else if (e.key === 'ArrowRight') setIndex((i) => Math.min(i + 1, visible.length - 1));
      else if (e.key === 'ArrowLeft') setIndex((i) => Math.max(i - 1, 0));
    };
    window.addEventListener('resize', measure);
    window.addEventListener('scroll', measure, true);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('resize', measure);
      window.removeEventListener('scroll', measure, true);
      window.removeEventListener('keydown', onKey);
    };
  }, [measure, onDone, visible.length]);

  if (!step || !rect) return null;

  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const width = Math.min(PANEL_W, vw - EDGE * 2);
  const below = rect.bottom + GAP + panelH <= vh - EDGE || rect.top - GAP - panelH < EDGE;
  const top = below
    ? Math.min(rect.bottom + GAP, vh - EDGE - panelH)
    : rect.top - GAP - panelH;
  const left = Math.max(EDGE, Math.min(rect.left, vw - EDGE - width));
  // The sharp window, clamped to the viewport, with the keyline's 4px margin.
  const hole = {
    top: Math.max(0, rect.top - 4),
    left: Math.max(0, rect.left - 4),
    bottom: Math.min(vh, rect.bottom + 4),
    right: Math.min(vw, rect.right + 4),
  };

  return (
    <>
      {/*
        Four blurred panels around the element, leaving it sharp. They also
        catch clicks, so the page cannot be changed under the tour.
      */}
      {[
        { top: 0, left: 0, width: vw, height: hole.top },
        { top: hole.bottom, left: 0, width: vw, height: Math.max(0, vh - hole.bottom) },
        { top: hole.top, left: 0, width: hole.left, height: hole.bottom - hole.top },
        { top: hole.top, left: hole.right, width: Math.max(0, vw - hole.right), height: hole.bottom - hole.top },
      ].map((box, i) => (
        <div key={i} aria-hidden="true" className="fixed z-[59] backdrop-blur-[3px]" style={box} />
      ))}
      {/* The keyline around the element being explained. */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed z-[60] rounded-[2px] border-2 border-accent"
        style={{ top: rect.top - 4, left: rect.left - 4, width: rect.width + 8, height: rect.height + 8 }}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="false"
        aria-labelledby="tour-title"
        aria-describedby="tour-body"
        className="fixed z-[61] flex flex-col gap-3 border border-rule-strong bg-term-900 p-5"
        style={{ top: Math.max(EDGE, top), left, width }}
      >
        <div className="flex items-center justify-between gap-3">
          <p className="label num">
            Step {index + 1} of {visible.length}
          </p>
          <button type="button" onClick={() => onDone('skipped')} className="text-action -my-2">
            Skip tour
          </button>
        </div>
        {/* Where this step sits in the walkthrough. Static, so it is not motion. */}
        <div aria-hidden="true" className="flex gap-1">
          {visible.map((_, i) => (
            <span key={i} className={`h-0.5 flex-1 ${i <= index ? 'bg-accent' : 'bg-rule'}`} />
          ))}
        </div>
        <h2 id="tour-title" className="h-panel mt-1">
          {step.title}
        </h2>
        <p id="tour-body" className="text-base leading-relaxed text-fg-2">
          {step.body}
        </p>
        <div className="mt-1 flex items-center justify-end gap-2 border-t border-rule pt-4">
          <p className="mr-auto hidden text-2xs text-fg-3 sm:block" aria-hidden="true">
            <span className="kbd">Esc</span> skips
          </p>
          {index > 0 && (
            <button type="button" onClick={() => setIndex((i) => i - 1)} className="btn-quiet px-4">
              Back
            </button>
          )}
          <button
            ref={nextRef}
            type="button"
            onClick={() => (last ? onDone('finished') : setIndex((i) => i + 1))}
            className="btn-primary px-5"
          >
            {last ? 'Finish' : 'Next'}
          </button>
        </div>
      </div>
    </>
  );
};
