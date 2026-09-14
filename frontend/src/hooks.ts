/**
 * Scroll-position hooks.
 *
 * Both exist to answer "is this data on screen yet", which is what lets a
 * figure count in at the moment it is read rather than while it is off screen.
 * Neither is a general-purpose animate-on-scroll helper.
 */
import { useEffect, useRef, useState } from 'react';

const DEFAULT_TITLE = 'INVR: quantitative analysis of NSE equities';

/**
 * Names the page in the browser tab and for screen readers (WCAG 2.4.2). Every
 * route used to share the one static "INVR" title.
 */
export function useDocumentTitle(title?: string | null) {
  useEffect(() => {
    document.title = title ? `${title} · INVR` : DEFAULT_TITLE;
  }, [title]);
}

export const prefersReducedMotion = (): boolean =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true;

/** True once the element has been seen. Never flips back, so figures settle. */
export function useInView<T extends HTMLElement = HTMLDivElement>(
  rootMargin = '-12% 0px -12% 0px',
): [React.RefObject<T | null>, boolean] {
  const ref = useRef<T | null>(null);
  // Without IntersectionObserver, treat everything as visible immediately.
  const [seen, setSeen] = useState(() => typeof IntersectionObserver === 'undefined');

  useEffect(() => {
    const node = ref.current;
    if (!node || seen) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setSeen(true);
            observer.disconnect();
          }
        }
      },
      { rootMargin, threshold: 0.01 },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [rootMargin, seen]);

  return [ref, seen];
}

/** Reports which of several sections currently holds the viewport centre. */
export function useActiveSection(
  count: number,
): [(index: number) => (node: HTMLElement | null) => void, number] {
  const nodes = useRef<(HTMLElement | null)[]>([]);
  const [active, setActive] = useState(0);

  const register = (index: number) => (node: HTMLElement | null) => {
    nodes.current[index] = node;
  };

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const index = nodes.current.findIndex((n) => n === entry.target);
          if (index >= 0) setActive(index);
        }
      },
      // A narrow band across the middle of the viewport, so exactly one
      // section is active at any scroll position.
      { rootMargin: '-45% 0px -45% 0px', threshold: 0 },
    );

    for (const node of nodes.current) {
      if (node) observer.observe(node);
    }
    return () => observer.disconnect();
  }, [count]);

  return [register, active];
}
