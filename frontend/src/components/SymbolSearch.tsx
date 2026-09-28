/**
 * Ticker field with NSE autosuggest (ARIA combobox).
 *
 * Only a listing that came back from /api/v1/symbols/search can be run: a
 * pick from the list, or typed text that is exactly one suggestion's symbol.
 * Anything else stops here with an inline error, so free text never reaches
 * the run API. Requests are debounced, and each new one aborts the last and
 * carries a sequence number, so a slow early response cannot overwrite a
 * newer one.
 */
import React, { useEffect, useId, useRef, useState } from 'react';
import { searchSymbols } from '../api';
import { bareSymbol, matchSuggestion, toRunTicker, type Suggestion } from '../lib/symbols';
import { errorMessage } from '../types';
import { IconSearch } from './Icons';
import { SkeletonLine } from './Skeleton';

const DEBOUNCE_MS = 250;

/** The part of `text` that matches what was typed, set in the brighter ink. */
const Highlight: React.FC<{ text: string; query: string }> = ({ text, query }) => {
  const at = query ? text.toLowerCase().indexOf(query.toLowerCase()) : -1;
  if (at < 0) return <>{text}</>;
  return (
    <>
      {text.slice(0, at)}
      <span className="font-semibold text-fg">{text.slice(at, at + query.length)}</span>
      {text.slice(at + query.length)}
    </>
  );
};

type Status = 'idle' | 'loading' | 'ready' | 'error';

export const SymbolSearch: React.FC<{
  token: string | null;
  busy: boolean;
  /** Called with a validated run ticker (`SYMBOL.NS`). */
  onRun: (ticker: string) => void;
  /** Called when a listing is chosen, before any run, so the horizon can follow it. */
  onPick: (ticker: string) => void;
}> = ({ token, busy, onRun, onPick }) => {
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<Suggestion[]>([]);
  const [status, setStatus] = useState<Status>('idle');
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [picked, setPicked] = useState<Suggestion | null>(null);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const seq = useRef(0);
  const listId = useId();

  const q = query.trim();
  const searchable = q.length > 0 && !(picked && bareSymbol(picked.symbol) === q.toUpperCase());

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!searchable || !token) {
      setStatus('idle');
      return;
    }
    const mine = ++seq.current;
    const controller = new AbortController();
    setStatus('loading');
    const timer = setTimeout(async () => {
      try {
        const found = await searchSymbols(q, token, controller.signal);
        if (mine !== seq.current) return;
        setItems(found);
        setActive(found.length ? 0 : -1);
        setFetchError(null);
        setStatus('ready');
      } catch (err) {
        if (controller.signal.aborted || mine !== seq.current) return;
        setItems([]);
        setFetchError(errorMessage(err, 'Search failed.'));
        setStatus('error');
      }
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [q, searchable, token, retry]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const choose = (s: Suggestion) => {
    setPicked(s);
    setQuery(bareSymbol(s.symbol));
    setOpen(false);
    setInlineError(null);
    onPick(s.symbol);
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (busy || !q) return;
    const chosen = picked && bareSymbol(picked.symbol) === q.toUpperCase() ? picked : matchSuggestion(q, items);
    const ticker = chosen ? toRunTicker(chosen) : null;
    if (!ticker) {
      setInlineError(
        status === 'loading'
          ? 'Still searching. Pick a listing when the matches appear.'
          : status === 'error'
            ? 'Search is unavailable, so the ticker cannot be checked. Try again shortly.'
            : `No NSE listing matches "${q}". Pick one from the list.`,
      );
      setOpen(true);
      return;
    }
    if (chosen && chosen !== picked) onPick(ticker);
    setQuery('');
    setPicked(null);
    setItems([]);
    setOpen(false);
    setInlineError(null);
    onRun(ticker);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!items.length) return;
      setOpen(true);
      const step = e.key === 'ArrowDown' ? 1 : -1;
      setActive((i) => (i + step + items.length) % items.length);
    } else if (e.key === 'Enter' && open && active >= 0 && items[active] && status === 'ready') {
      // Enter on a highlighted row picks it; a second Enter runs it.
      e.preventDefault();
      choose(items[active]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  const showList = open && searchable && status !== 'idle';
  const errorId = `${listId}-error`;

  return (
    <form
      onSubmit={submit}
      data-tour="ticker-search"
      className="relative flex min-w-0 flex-1 flex-col sm:max-w-xl"
    >
      <label htmlFor="ticker-input" className="sr-only">
        Company or NSE symbol to analyse
      </label>
      <div className="control flex min-w-0 flex-1 items-center gap-2.5 pl-3.5">
        <IconSearch className="h-4 w-4 shrink-0 text-fg-3" />
        <input
          id="ticker-input"
          type="text"
          role="combobox"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={showList && active >= 0 ? `${listId}-${active}` : undefined}
          aria-invalid={inlineError ? true : undefined}
          aria-describedby={inlineError ? errorId : undefined}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setPicked(null);
            setInlineError(null);
            setOpen(true);
          }}
          onKeyDown={onKeyDown}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          placeholder="Search NSE stocks, e.g. Tata or TCS"
          disabled={busy}
          autoComplete="off"
          spellCheck={false}
          className="w-full min-w-0 bg-transparent py-3 text-base outline-none placeholder:text-fg-3 disabled:opacity-60"
        />
        {/* What the short symbol in the box stands for, once one is picked. */}
        {picked && bareSymbol(picked.symbol) === q.toUpperCase() ? (
          <span className="hidden min-w-0 max-w-[14rem] shrink truncate text-sm text-fg-3 md:inline">
            {picked.name}
          </span>
        ) : (
          <span className="kbd hidden shrink-0 sm:inline">Enter</span>
        )}
        <button
          type="submit"
          disabled={busy}
          data-tour="analyse"
          className="btn-primary m-1 shrink-0 px-3.5 sm:px-5"
        >
          {busy ? 'Running' : 'Analyse'}
        </button>
      </div>

      {inlineError && (
        <p id={errorId} role="alert" className="mt-1.5 text-sm text-down">
          {inlineError}
        </p>
      )}

      {showList && (
        // mousedown is prevented so the input keeps focus and blur does not
        // close the list before the click lands.
        <div
          onMouseDown={(e) => e.preventDefault()}
          className="absolute left-0 right-0 top-full z-40 mt-1 border border-rule-strong bg-term-900"
        >
          {status === 'loading' && (
            <div role="status" aria-label="Searching" className="flex flex-col gap-3 p-3.5">
              <SkeletonLine className="h-3.5 w-3/4" />
              <SkeletonLine className="h-3.5 w-1/2" />
            </div>
          )}
          {status === 'error' && (
            <div role="alert" className="flex flex-col gap-1 p-3.5">
              <p className="text-sm text-down">Could not search listings.</p>
              <p className="text-sm text-fg-3">{fetchError}</p>
              <button type="button" onClick={() => setRetry((n) => n + 1)} className="text-action self-start">
                Try again
              </button>
            </div>
          )}
          {status === 'ready' && items.length === 0 && (
            <p className="p-3.5 text-sm text-fg-3">No NSE listing matches "{q}".</p>
          )}
          <ul id={listId} role="listbox" aria-label="Matching NSE listings" className="max-h-80 overflow-y-auto">
            {status === 'ready' &&
              items.map((s, i) => (
                <li
                  key={s.symbol}
                  id={`${listId}-${i}`}
                  role="option"
                  aria-selected={i === active}
                  onClick={() => choose(s)}
                  onMouseMove={() => setActive(i)}
                  className={`flex min-h-[44px] cursor-pointer items-baseline gap-3 border-t border-rule px-3.5 py-2.5 first:border-t-0 ${
                    i === active ? 'bg-term-800 text-fg' : 'text-fg-2'
                  }`}
                >
                  <span className="w-28 shrink-0 truncate font-bold tracking-tight text-fg">
                    {bareSymbol(s.symbol)}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-sm">
                    <Highlight text={s.name} query={q} />
                  </span>
                  <span className="label shrink-0">{s.exchange}</span>
                </li>
              ))}
          </ul>
          {status === 'ready' && items.length > 0 && (
            <p className="hidden border-t border-rule px-3.5 py-2 text-2xs text-fg-3 sm:block">
              <span className="kbd">Up</span> <span className="kbd">Down</span> to move,{' '}
              <span className="kbd">Enter</span> to pick, <span className="kbd">Esc</span> to close
            </p>
          )}
        </div>
      )}
    </form>
  );
};
