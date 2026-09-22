import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/auth';
import { supabase } from '../supabase';
import { apiUrl } from '../api';
import { Wordmark } from '../components/SiteChrome';
import { MarketClock } from '../components/MarketClock';
import { TutorPanel } from '../components/TutorPanel';
import { SkeletonBlock, SkeletonLine, SkeletonMetric, SkeletonRow } from '../components/Skeleton';
import {
  IconClose,
  IconMarked,
  IconPanel,
  IconPlus,
  IconSearch,
} from '../components/Icons';
import {
  Disclaimer,
  GateList,
  MetricTable,
  Narrative,
  PriceLadder,
  TradeSetup,
  VerdictHead,
} from '../components/analysis';
import { asNum, asObj, asStr, asStrArray, verdictInk } from '../format';
import { errorMessage, type LedgerRow } from '../types';
import type { LogEntry } from '../components/TutorPanel';
import { prefersReducedMotion, useDocumentTitle } from '../hooks';

/**
 * A failed read, said as a failure. A failed history or watchlist read used to
 * fall through to the empty state, which told the user they had no runs.
 */
const LoadError: React.FC<{ what: string; message: string; onRetry: () => void }> = ({
  what,
  message,
  onRetry,
}) => (
  <div role="alert" className="flex flex-col gap-1 p-3">
    <p className="text-sm leading-relaxed text-down">Could not load {what}.</p>
    <p className="text-sm leading-relaxed text-fg-3">{message}</p>
    <button type="button" onClick={onRetry} className="text-action self-start">
      Try again
    </button>
  </div>
);

// Ticker shape: alphanumerics with an optional .NS suffix, used to decide
// whether a bare input should be treated as an analysis request.
const TICKER_PATTERN = /^[A-Za-z0-9&-]{2,12}(\.NS)?$/;

const getTime = () => new Date().toLocaleTimeString('en-GB', { hour12: false });

export default function Workspace() {
  const { session, profile, logout } = useAuth();

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sidebarTab, setSidebarTab] = useState<'recent' | 'watchlist'>('recent');

  // Persisted per account in the `watchlists` table (migration 004). It used to
  // be session state, so the star button looked broken: it forgot everything on
  // reload (audit NEW-FE-15). Still starts empty rather than pre-seeded with
  // tickers the user never chose.
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  const [ledgerItems, setLedgerItems] = useState<LedgerRow[]>([]);
  const [ledgerLoading, setLedgerLoading] = useState(true);
  const [ledgerError, setLedgerError] = useState<string | null>(null);
  const [watchlistLoading, setWatchlistLoading] = useState(true);
  const [watchlistError, setWatchlistError] = useState<string | null>(null);
  const [activeItem, setActiveItem] = useState<LedgerRow | null>(null);
  useDocumentTitle(activeItem ? `${activeItem.ticker.split('.')[0]} analysis` : 'Workspace');

  const [command, setCommand] = useState('');
  const [log, setLog] = useState<LogEntry[]>([
    { role: 'sys', text: 'Engine connected. Enter a ticker to run the pipeline, or ask a question.', time: getTime() },
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  // One chat session per account, persisted. It used to be a fresh
  // crypto.randomUUID() on every mount, so a page reload started a new session
  // and the tutor's working memory was always empty however well the backend
  // stored it (audit finding ISO-03). Keyed by user id so switching accounts
  // never inherits the previous account's conversation.
  const userId = session?.user?.id ?? null;
  const [sessionId, setSessionId] = useState('');

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!userId) return;
    const key = `invr.session.${userId}`;
    let existing = localStorage.getItem(key);
    if (!existing) {
      existing = crypto.randomUUID();
      localStorage.setItem(key, existing);
    }
    setSessionId(existing);
  }, [userId]);
  /* eslint-enable react-hooks/set-state-in-effect */
  const logEndRef = useRef<HTMLDivElement>(null);

  const silver = activeItem?.silver_state;
  const gold = activeItem?.gold_verdict;
  const setup = gold ? asObj(gold.trade_setup) : null;
  const narrative = gold ? asObj(gold.llm_analysis) : null;
  const isWatched = activeItem ? watchlist.includes(activeItem.ticker) : false;

  const appendLog = (entry: Omit<LogEntry, 'time'>) =>
    setLog((prev) => [...prev, { ...entry, time: getTime() }]);

  // Scrolls the transcript pane only. scrollIntoView moved the whole page on
  // mobile, dragging the reader away from a result they had just asked for.
  const scrollLog = () =>
    setTimeout(() => {
      const pane = logEndRef.current?.parentElement;
      pane?.scrollTo({
        top: pane.scrollHeight,
        behavior: prefersReducedMotion() ? 'auto' : 'smooth',
      });
    }, 120);

  /*
    This user's most recent run per ticker, five tickers deep.

    Read through `prediction_interactions`, not `algorithmic_ledger` directly.
    The ledger is shared by design: it is deduplicated on
    (ticker, timeframe, date, pipeline_version) so one deterministic verdict is
    stored once and graded once by the Engine Room, which means it carries no
    user_id to filter on. Selecting from it directly showed every account the
    same globally-newest rows - two people signed in and saw each other's
    stocks (audit finding ISO-01). The interaction table is the ownership
    record, and RLS in migrations/003 enforces the same scope server-side so
    the filter below is defence in depth rather than the only guard.
  */
  const fetchWatchlist = async () => {
    if (!userId) return;
    try {
      const { data, error } = await supabase
        .from('watchlists')
        .select('ticker')
        .eq('user_id', userId)
        .order('created_at', { ascending: false });
      if (error) throw error;
      setWatchlist((data ?? []).map((row) => (row as { ticker: string }).ticker));
      setWatchlistError(null);
    } catch (err) {
      // A failed watchlist read must not take the workspace down with it, but
      // it must not pass for an empty watchlist either.
      console.error('Could not read your watchlist:', err);
      setWatchlistError(errorMessage(err, 'The request failed.'));
    } finally {
      setWatchlistLoading(false);
    }
  };

  const fetchLedger = async () => {
    if (!userId) return;
    try {
      const { data, error } = await supabase
        .from('prediction_interactions')
        .select('created_at, algorithmic_ledger(*)')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(100);

      if (error) throw error;

      // PostgREST types a foreign-table embed as an array even when the
      // relationship is many-to-one, and returns an object at runtime, so
      // accept either shape rather than asserting one.
      const rows = (data ?? [])
        .flatMap((row) => {
          const joined = (row as unknown as { algorithmic_ledger: unknown }).algorithmic_ledger;
          return Array.isArray(joined) ? joined : joined ? [joined] : [];
        })
        .filter((row): row is LedgerRow => row != null) as LedgerRow[];

      // A user can view the same prediction many times, so dedupe on ticker
      // after ordering rather than trusting the interaction rows to be unique.
      const seen = new Set<string>();
      const deduped = rows
        .filter((item) => {
          if (seen.has(item.ticker)) return false;
          seen.add(item.ticker);
          return true;
        })
        .slice(0, 5);

      setLedgerItems(deduped);
      setActiveItem((current) => current ?? deduped[0] ?? null);
      setLedgerError(null);
    } catch (err) {
      console.error('Could not read your analysis history:', err);
      setLedgerError(errorMessage(err, 'The request failed.'));
    } finally {
      setLedgerLoading(false);
    }
  };

  // Reads the ledger when a session appears. This is the sanctioned "subscribe
  // to an external system" case: the database is the external system, and the
  // resulting setState lands in a later microtask, not during render.
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    // Clear first, so switching accounts never shows the previous account's
    // rows while the new read is in flight.
    setLedgerItems([]);
    setActiveItem(null);
    setLedgerLoading(true);
    setLedgerError(null);
    setWatchlistLoading(true);
    setWatchlistError(null);
    void fetchLedger();
    void fetchWatchlist();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);
  /* eslint-enable react-hooks/set-state-in-effect */

  /*
    Hides a run from this session's list. It deliberately does NOT delete the
    ledger row: that table is the shared record the Engine Room grades against,
    it carries no user_id to scope a delete by, and removing rows would destroy
    the accuracy history for everyone. Writes are revoked at the database in
    migrations/001_ledger_rls.sql.
  */
  const dismissLedgerItem = (logId: string) => {
    setLedgerItems((prev) => prev.filter((item) => item.log_id !== logId));
    if (activeItem?.log_id === logId) setActiveItem(null);
  };

  const retryLedger = () => {
    setLedgerLoading(true);
    setLedgerError(null);
    void fetchLedger();
  };

  const retryWatchlist = () => {
    setWatchlistLoading(true);
    setWatchlistError(null);
    void fetchWatchlist();
  };

  /*
    Optimistic toggle: the star flips immediately and the row is written behind
    it, because waiting on a round trip to acknowledge a bookmark feels broken.
    A failed write rolls the local state back rather than leaving the UI showing
    something the database does not agree with.
  */
  const toggleWatch = async (ticker: string) => {
    if (!userId) return;
    const wasWatched = watchlist.includes(ticker);
    setWatchlist((prev) => (wasWatched ? prev.filter((t) => t !== ticker) : [...prev, ticker]));

    try {
      if (wasWatched) {
        const { error } = await supabase
          .from('watchlists')
          .delete()
          .eq('user_id', userId)
          .eq('ticker', ticker);
        if (error) throw error;
      } else {
        // upsert, not insert: the unique (user_id, ticker) constraint makes a
        // double-click idempotent instead of an error.
        const { error } = await supabase
          .from('watchlists')
          .upsert({ user_id: userId, ticker }, { onConflict: 'user_id,ticker' });
        if (error) throw error;
      }
    } catch (err) {
      setWatchlist((prev) => (wasWatched ? [...prev, ticker] : prev.filter((t) => t !== ticker)));
      appendLog({ role: 'sys', text: `Could not update the watchlist: ${errorMessage(err, 'write failed')}` });
    }
  };

  const runAnalysis = async (rawTicker: string) => {
    if (!session) {
      appendLog({ role: 'sys', text: 'No active session. Sign in again to run the pipeline.' });
      return;
    }
    if (!profile) {
      appendLog({ role: 'sys', text: 'Profile not loaded yet. Reload the page and try again.' });
      return;
    }
    if (isProcessing) return;

    const rawClean = rawTicker.trim().toUpperCase().replace(/\.NS$/i, '');
    const ticker = `${rawClean}.NS`;

    setIsProcessing(true);
    appendLog({ role: 'sys', text: `Running the ${profile.timeframe || 'swing'} pipeline for ${ticker}.` });

    try {
      const payload = {
        ticker,
        timeframe: profile.timeframe || 'swing',
        user_profile: {
          risk_tolerance: profile.risk,
          experience_level: profile.experience,
          goal: profile.goal,
          available_capital: profile.capital,
        },
        session_id: sessionId,
      };

      const response = await fetch(apiUrl('/api/v1/analytics/process'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = (await response.json().catch(() => ({}))) as { detail?: string };
        throw new Error(errData.detail || 'The pipeline request failed.');
      }

      const resData = await response.json();
      const apiTicker = (resData.ticker as string)?.toUpperCase() || ticker;

      if (!resData.success) {
        const pipelineError = resData.errors?.[0] || 'The pipeline returned no data.';
        appendLog({ role: 'sys', text: `Pipeline error: ${pipelineError}` });

        // Fall back to the last stored run so the panels are not left blank.
        // Scoped by timeframe: the ledger dedup key is
        // (ticker, timeframe, date, version), so an unscoped lookup could
        // surface a row produced for someone else's horizon (ISO-06).
        const { data: staleData } = await supabase
          .from('algorithmic_ledger')
          .select('*')
          .or(`ticker.eq.${apiTicker},ticker.eq.${rawClean}`)
          .eq('timeframe', payload.timeframe)
          .order('created_at', { ascending: false })
          .limit(1);

        if (staleData && staleData.length > 0) {
          setActiveItem(staleData[0] as LedgerRow);
          appendLog({ role: 'sys', text: 'Showing the previous stored run for this ticker.' });
          void fetchLedger();
        }
        return;
      }

      // The backend writes the ledger row before it responds and returns its
      // log_id (audit MU-04), so the exact row can be read with no wait. This
      // replaced a fixed 3s sleep that raced a background write. The ticker
      // lookup remains only for a response with no log_id, meaning the write
      // failed and the latest stored run is the best available.
      const logId = typeof resData.log_id === 'string' ? resData.log_id : null;
      const ledger = supabase.from('algorithmic_ledger').select('*');
      const { data, error } = await (logId
        ? ledger.eq('log_id', logId).limit(1)
        : ledger
            .or(`ticker.eq.${apiTicker},ticker.eq.${rawClean}`)
            .eq('timeframe', payload.timeframe)
            .order('created_at', { ascending: false })
            .limit(1));

      if (error) throw error;

      if (data && data.length > 0) {
        const row = data[0] as LedgerRow;
        setActiveItem(row);
        void fetchLedger();

        const rowScore = asNum(row.gold_verdict?.confidence_score);
        const score = rowScore != null ? ` Confidence ${(rowScore / 10).toFixed(1)} of 10.` : '';
        appendLog({
          role: 'ai',
          text: `${row.ticker}: ${asStr(row.gold_verdict?.verdict) ?? 'no verdict'}.${score} ${
            asStr(row.gold_verdict?.primary_reason) ?? ''
          }`.trim(),
        });
      } else {
        appendLog({
          role: 'sys',
          text: `Pipeline finished with verdict ${resData.verdict}, but the result could not be saved to your history.`,
        });
        void fetchLedger();
      }
    } catch (err: unknown) {
      appendLog({ role: 'sys', text: `Error: ${errorMessage(err, 'the request failed.')}` });
    } finally {
      setIsProcessing(false);
      scrollLog();
    }
  };

  const handleCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim() || isProcessing) return;

    const cmd = command.trim();
    setCommand('');
    appendLog({ role: 'user', text: cmd });

    const isAnalyzeCmd = cmd.toUpperCase().startsWith('/ANALYZE ');
    const isBareTicker = TICKER_PATTERN.test(cmd);

    if (isAnalyzeCmd || isBareTicker) {
      const tk = isAnalyzeCmd ? cmd.substring(9).trim() : cmd;
      if (tk) {
        await runAnalysis(tk);
        return;
      }
    }

    setIsProcessing(true);
    setIsStreaming(true);

    try {
      const response = await fetch(apiUrl('/api/v1/tutor/chat/stream'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify({
          message: cmd,
          session_id: sessionId,
          // Flat shape, because that is what extract_relevant_state reads on
          // the backend. Sending {silver, gold} left it with no ticker at all,
          // which is how the tutor ended up talking about another company.
          analysis_context: activeItem
            ? {
                ticker: activeItem.ticker,
                timeframe: activeItem.timeframe,
                verdict: asStr(gold?.verdict),
                confidence_score: asNum(gold?.confidence_score),
                primary_reason: asStr(gold?.primary_reason),
                gate_results: asObj(gold?.gate_results) ?? {},
                trade_setup: setup,
                what_to_watch: asStrArray(narrative?.what_to_watch),
                risk_warning: asStr(narrative?.risk_warning),
                tutor_triggers: asStrArray(narrative?.tutor_triggers),
                metrics: silver ?? {},
              }
            : {},
          user_profile: {
            risk_tolerance: profile?.risk || 'moderate',
            experience_level: profile?.experience || 'intermediate',
            goal: profile?.goal || 'wealth_growth',
            available_capital: profile?.capital || 100000.0,
          },
        }),
      });

      if (!response.ok) throw new Error('The tutor stream could not be opened.');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('The response stream is unreadable.');

      const decoder = new TextDecoder();
      let aiText = '';

      appendLog({ role: 'ai', text: '' });

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue;

          const dataStr = line.slice(6).trim();
          if (dataStr === '[DONE]') break;

          try {
            const data = JSON.parse(dataStr);
            if (data.token) {
              aiText += data.token;
              setLog((prev) => {
                const next = [...prev];
                if (next.length > 0) {
                  next[next.length - 1] = { ...next[next.length - 1], text: aiText };
                }
                return next;
              });
            } else if (data.error) {
              throw new Error(data.error);
            }
          } catch {
            // Partial frame across chunk boundaries. The next read completes it.
          }
        }
      }
    } catch (err: unknown) {
      appendLog({ role: 'sys', text: `Tutor error: ${errorMessage(err, 'the stream stopped.')}` });
    } finally {
      setIsStreaming(false);
      setIsProcessing(false);
      scrollLog();
    }
  };

  const showAnalysisSkeleton = isProcessing && !activeItem;

  return (
    // Below lg the workspace scrolls as one document: a fixed-height shell left
    // the analysis a sliver above the tutor on a phone, and a two-pane split on
    // a tablet left the analysis about 350px wide.
    <div className="flex min-h-screen flex-col bg-term-950 text-fg lg:h-screen">
      {/* ------------------------------------------------------------ top bar */}
      <header className="shrink-0 border-b border-rule bg-term-950">
        <div className="flex flex-wrap items-center gap-3 px-4 py-3">
          <button
            type="button"
            onClick={() => setIsSidebarOpen((v) => !v)}
            aria-label={isSidebarOpen ? 'Hide the history panel' : 'Show the history panel'}
            aria-pressed={isSidebarOpen}
            className={`hidden h-11 w-11 items-center justify-center rounded-[2px] border transition-colors lg:inline-flex ${
              isSidebarOpen
                ? 'border-accent text-fg'
                : 'border-rule-strong text-fg-3 hover:border-accent hover:text-fg'
            }`}
          >
            <IconPanel className="h-4 w-4" />
          </button>

          {/* Below sm the wordmark takes the whole first row, which leaves the
              field, Analyse and Sign out on one line under it. */}
          <Link to="/" className="flex basis-full items-baseline gap-2 sm:basis-auto">
            <Wordmark />
          </Link>

          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const q = searchQuery.trim();
              if (q && !isProcessing) {
                setSearchQuery('');
                await runAnalysis(q);
              }
            }}
            className="flex min-w-0 flex-1 items-center gap-2 sm:max-w-xl"
          >
            <label htmlFor="ticker-input" className="sr-only">
              NSE ticker to analyse
            </label>
            {/* The padding sits on the input, not the box, so the whole
                control is a 44px tap target rather than a 27px line of text. */}
            <div className="control flex min-w-0 flex-1 items-center gap-2.5 px-3.5">
              <IconSearch className="h-4 w-4 shrink-0 text-fg-3" />
              <input
                id="ticker-input"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ticker, for example TCS or RELIANCE"
                disabled={isProcessing}
                autoComplete="off"
                spellCheck={false}
                className="w-full min-w-0 bg-transparent py-3 text-base outline-none placeholder:text-fg-3 disabled:opacity-60"
              />
              <span className="kbd hidden shrink-0 sm:inline">Enter</span>
            </div>
            {/* Narrower padding on a phone: three controls share the row. */}
            <button
              type="submit"
              disabled={isProcessing}
              className="btn-primary shrink-0 px-3.5 sm:px-5"
            >
              {isProcessing ? 'Running' : 'Analyse'}
            </button>
          </form>

          <div className="ml-auto flex shrink-0 items-center gap-4">
            <div className="hidden lg:block">
              <MarketClock compact />
            </div>
            {profile?.timeframe && (
              <p className="label hidden md:block">
                {String(profile.timeframe).replace('_', ' ')} horizon
              </p>
            )}
            <button onClick={logout} className="btn-quiet px-3.5 sm:px-5">
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 flex-col lg:min-h-0 lg:flex-row">
        {/* ---------------------------------------------------------- sidebar */}
        {isSidebarOpen && (
          <aside className="hidden w-[260px] shrink-0 flex-col border-r border-rule bg-term-900 lg:flex">
            <div className="flex shrink-0 border-b border-rule">
              {(['recent', 'watchlist'] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  aria-pressed={sidebarTab === tab}
                  onClick={() => setSidebarTab(tab)}
                  className={`-mb-px min-h-[44px] flex-1 px-3 text-2xs font-semibold uppercase tracking-label transition-colors ${
                    sidebarTab === tab
                      ? 'border-b-2 border-accent text-fg'
                      : 'border-b-2 border-transparent text-fg-3 hover:text-fg'
                  }`}
                >
                  {tab === 'recent' ? 'Recent runs' : 'Watchlist'}
                </button>
              ))}
            </div>

            <div className="no-scrollbar flex flex-1 flex-col gap-2 overflow-y-auto p-3">
              {sidebarTab === 'recent' ? (
                ledgerLoading ? (
                  <>
                    <SkeletonRow />
                    <SkeletonRow />
                    <SkeletonRow />
                  </>
                ) : ledgerError && ledgerItems.length === 0 ? (
                  <LoadError what="your recent runs" message={ledgerError} onRetry={retryLedger} />
                ) : ledgerItems.length === 0 ? (
                  <p className="p-3 text-sm leading-relaxed text-fg-3">
                    No runs recorded yet. Analyse a ticker to start the ledger.
                  </p>
                ) : (
                  ledgerItems.map((item) => {
                    const selected = activeItem?.log_id === item.log_id;
                    const watched = watchlist.includes(item.ticker);
                    const score = asNum(item.gold_verdict?.confidence_score);
                    const rowVerdict = asStr(item.gold_verdict?.verdict);
                    // The row's select control and its actions are siblings. They
                    // used to be buttons nested inside a role="button" div, which
                    // is invalid and ambiguous to a screen reader.
                    return (
                      <div
                        key={item.log_id}
                        className={`flex items-stretch border transition-colors ${
                          selected
                            ? 'border-accent bg-term-850'
                            : 'border-rule hover:border-rule-strong'
                        }`}
                      >
                        <button
                          type="button"
                          onClick={() => setActiveItem(item)}
                          aria-pressed={selected}
                          className="min-w-0 flex-1 p-3 text-left"
                        >
                          <span className="block truncate text-lg font-bold tracking-tight text-fg">
                            {item.ticker.split('.')[0]}
                          </span>
                          <span
                            className={`mt-0.5 block truncate text-2xs font-semibold uppercase tracking-label ${verdictInk(
                              rowVerdict,
                            )}`}
                          >
                            {rowVerdict ?? 'no verdict'}
                          </span>
                          <span className="num mt-2 block text-2xs text-fg-3">
                            {score != null ? `${(score / 10).toFixed(1)} / 10` : 'unscored'}
                            {item.date ? ` · ${item.date}` : ''}
                          </span>
                        </button>
                        {/* Always shown. Hover-only actions cannot be found on touch. */}
                        <div className="flex shrink-0 flex-col">
                          <button
                            type="button"
                            onClick={() => void toggleWatch(item.ticker)}
                            aria-label={
                              watched
                                ? `Remove ${item.ticker} from the watchlist`
                                : `Add ${item.ticker} to the watchlist`
                            }
                            className="icon-btn"
                          >
                            {watched ? (
                              <IconMarked className="h-3.5 w-3.5 text-fg" />
                            ) : (
                              <IconPlus className="h-3.5 w-3.5" />
                            )}
                          </button>
                          <button
                            type="button"
                            onClick={() => dismissLedgerItem(item.log_id!)}
                            aria-label={`Hide the ${item.ticker} run from this list`}
                            title="Hide from this list. The record itself is kept for grading."
                            className="icon-btn"
                          >
                            <IconClose className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })
                )
              ) : watchlistLoading ? (
                <>
                  <SkeletonRow />
                  <SkeletonRow />
                </>
              ) : watchlistError ? (
                <LoadError what="your watchlist" message={watchlistError} onRetry={retryWatchlist} />
              ) : watchlist.length === 0 ? (
                <p className="p-3 text-sm leading-relaxed text-fg-3">
                  Nothing on the watchlist. Use Watch on an analysis, or the plus mark on a
                  recent run, to add a ticker.
                </p>
              ) : (
                watchlist.map((ticker) => (
                  <div
                    key={ticker}
                    className="flex items-center justify-between border border-rule pl-3"
                  >
                    <span className="text-base font-medium text-fg">{ticker.split('.')[0]}</span>
                    <div className="flex">
                      <button
                        type="button"
                        onClick={() => void runAnalysis(ticker)}
                        disabled={isProcessing}
                        aria-label={`Analyse ${ticker}`}
                        className="icon-btn"
                      >
                        <IconSearch className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => void toggleWatch(ticker)}
                        aria-label={`Remove ${ticker} from the watchlist`}
                        className="icon-btn hover:text-down"
                      >
                        <IconClose className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </aside>
        )}

        {/* -------------------------------------------------------- main sheet */}
        <main className="no-scrollbar flex-1 lg:min-h-0 lg:overflow-y-auto">
          <div className="mx-auto max-w-3xl px-5 py-6">
            {/*
              Recent runs below lg, where the sidebar is hidden. Without this a
              phone had no way back to an earlier analysis.
            */}
            {ledgerItems.length > 0 && (
              <nav aria-label="Recent runs" className="mb-5 border-b border-rule pb-3 lg:hidden">
                <p className="label mb-2">Recent runs</p>
                {/*
                  One scrolling row, not a wrapping block: five runs wrapped to
                  three rows and pushed the analysis itself below the fold.
                */}
                <div className="no-scrollbar -mx-5 flex gap-2 overflow-x-auto px-5">
                  {ledgerItems.map((item) => {
                    const selected = activeItem?.log_id === item.log_id;
                    const rowVerdict = asStr(item.gold_verdict?.verdict);
                    return (
                      <button
                        key={item.log_id}
                        type="button"
                        onClick={() => setActiveItem(item)}
                        aria-pressed={selected}
                        className={`inline-flex min-h-[44px] shrink-0 items-baseline gap-2 whitespace-nowrap rounded-[2px] border px-3 py-2 transition-colors ${
                          selected ? 'border-accent bg-term-850' : 'border-rule-strong hover:border-accent'
                        }`}
                      >
                        <span className="text-sm font-bold tracking-tight text-fg">
                          {item.ticker.split('.')[0]}
                        </span>
                        <span
                          className={`text-2xs font-semibold uppercase tracking-label ${verdictInk(rowVerdict)}`}
                        >
                          {rowVerdict ?? 'no verdict'}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </nav>
            )}

            {ledgerLoading && !activeItem ? (
              <div className="flex flex-col gap-6">
                <SkeletonLine className="h-2.5 w-32" />
                <SkeletonLine className="h-9 w-64" />
                <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-1 2xl:grid-cols-2">
                  <SkeletonBlock lines={7} />
                  <SkeletonBlock lines={7} />
                </div>
              </div>
            ) : showAnalysisSkeleton ? (
              <div className="flex flex-col gap-6" role="status" aria-label="Running the pipeline">
                <p className="label">Running the pipeline</p>
                <SkeletonLine className="h-9 w-64" />
                <div className="grid gap-3 sm:grid-cols-2">
                  <SkeletonMetric />
                  <SkeletonMetric />
                  <SkeletonMetric />
                  <SkeletonMetric />
                </div>
              </div>
            ) : !activeItem || !silver || !gold ? (
              <div className="border border-rule bg-term-900 p-8">
                <p className="label mb-2">No analysis loaded</p>
                <h2 className="h-section">
                  Enter a ticker to run the pipeline
                </h2>
                <p className="mt-4 max-w-xl text-lg leading-relaxed text-fg-2">
                  Type an NSE symbol in the field above, or ask the tutor a question in the
                  panel beside this one. Results are written to the ledger and listed under
                  recent runs.
                </p>
                {/* The sidebar is hidden below lg, so the failure is stated here too. */}
                {ledgerError && (
                  <div className="-mx-3 mt-4 border-t border-rule pt-2">
                    <LoadError what="your recent runs" message={ledgerError} onRetry={retryLedger} />
                  </div>
                )}
              </div>
            ) : (
              <article className="flex flex-col gap-8">
                {/* Masthead for the active ticker */}
                <div className="flex flex-wrap items-start justify-between gap-4 border-b border-rule pb-5">
                  <div>
                    <h1 className="text-5xl font-extrabold leading-none tracking-tight text-fg">
                      {activeItem.ticker.split('.')[0]}
                    </h1>
                    <p className="mt-2.5 text-sm text-fg-3">
                      {activeItem.ticker} · {String(activeItem.timeframe).replace('_', ' ')}
                      {activeItem.date ? ` · recorded ${activeItem.date}` : ''}
                    </p>
                  </div>
                  <button
                    onClick={() => toggleWatch(activeItem.ticker)}
                    className="btn-quiet flex items-center gap-2"
                  >
                    {isWatched ? (
                      <>
                        <IconMarked className="h-3.5 w-3.5" />
                        On watchlist
                      </>
                    ) : (
                      <>
                        <IconPlus className="h-3.5 w-3.5" />
                        Watch
                      </>
                    )}
                  </button>
                </div>

                <section>
                  <VerdictHead gold={gold} ticker={activeItem.ticker} />
                  {asStr(gold.primary_reason) && (
                    <div className="mt-6 border-t border-rule pt-4">
                      <p className="label mb-1.5">Primary reason</p>
                      <p className="text-lg leading-relaxed text-fg-2">
                        {asStr(gold.primary_reason)}
                      </p>
                    </div>
                  )}
                </section>

                {/*
                  Two columns only where the sheet is actually wide: between md
                  and lg it has the whole window, and from 2xl it has enough left
                  over after the sidebar and the tutor. From lg to 2xl the sheet
                  is 360 to 640px, where two columns broke the metric notes one
                  word per line and cut the price ladder off.
                */}
                <div className="grid gap-x-10 gap-y-8 md:grid-cols-2 lg:grid-cols-1 2xl:grid-cols-2">
                  <section>
                    <h2 className="label mb-3 border-b border-rule pb-2">Silver metrics</h2>
                    <MetricTable silver={silver} />
                  </section>

                  <section>
                    <h2 className="label mb-3 border-b border-rule pb-2">Price structure</h2>
                    <PriceLadder silver={silver} setup={setup} />
                  </section>

                  <section>
                    <h2 className="label mb-3 border-b border-rule pb-2">Gate results</h2>
                    <GateList gates={asObj(gold.gate_results) ?? {}} />
                  </section>

                  <section className="flex flex-col gap-4">
                    <h2 className="label border-b border-rule pb-2">Position</h2>
                    {setup ? (
                      <TradeSetup setup={setup} />
                    ) : (
                      <p className="text-base leading-relaxed text-fg-3">
                        No trade setup on this record. The engine only generates entry, stop
                        and target levels for a strong buy on the intraday, swing and
                        positional horizons.
                      </p>
                    )}
                  </section>
                </div>

                {narrative && (
                  <section className="border-t border-rule pt-6">
                    <h2 className="label mb-4">Written explanation</h2>
                    <Narrative llm={narrative} />

                    {asStrArray(narrative.tutor_triggers).length > 0 && (
                        <div className="mt-6">
                          <p className="label mb-2">Ask about</p>
                          <div className="flex flex-wrap gap-2">
                            {asStrArray(narrative.tutor_triggers).map((trigger, i) => (
                              <button
                                key={i}
                                onClick={() =>
                                  setCommand(
                                    `Explain ${trigger} and how it applies to ${activeItem.ticker.split('.')[0]}.`,
                                  )
                                }
                                type="button"
                                className="chip"
                              >
                                {trigger}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                  </section>
                )}

                <div className="border-t border-rule pt-5">
                  <Disclaimer />
                </div>
              </article>
            )}
          </div>
        </main>

        <TutorPanel
          log={log}
          command={command}
          setCommand={setCommand}
          onSubmit={handleCommand}
          isProcessing={isProcessing}
          isStreaming={isStreaming}
          activeItem={activeItem}
          logEndRef={logEndRef}
        />
      </div>
    </div>
  );
}
