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

// Ticker shape: alphanumerics with an optional .NS suffix, used to decide
// whether a bare input should be treated as an analysis request.
const TICKER_PATTERN = /^[A-Za-z0-9&-]{2,12}(\.NS)?$/;

const getTime = () => new Date().toLocaleTimeString('en-GB', { hour12: false });

export default function Workspace() {
  const { session, profile, logout } = useAuth();

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sidebarTab, setSidebarTab] = useState<'recent' | 'watchlist'>('recent');

  // Watchlist is local to the session. It starts empty rather than pre-seeded
  // with tickers the user never chose.
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  const [ledgerItems, setLedgerItems] = useState<LedgerRow[]>([]);
  const [ledgerLoading, setLedgerLoading] = useState(true);
  const [activeItem, setActiveItem] = useState<LedgerRow | null>(null);

  const [command, setCommand] = useState('');
  const [log, setLog] = useState<LogEntry[]>([
    { role: 'sys', text: 'Engine connected. Enter a ticker to run the pipeline, or ask a question.', time: getTime() },
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const logEndRef = useRef<HTMLDivElement>(null);

  const silver = activeItem?.silver_state;
  const gold = activeItem?.gold_verdict;
  const setup = gold ? asObj(gold.trade_setup) : null;
  const narrative = gold ? asObj(gold.llm_analysis) : null;
  const isWatched = activeItem ? watchlist.includes(activeItem.ticker) : false;

  const appendLog = (entry: Omit<LogEntry, 'time'>) =>
    setLog((prev) => [...prev, { ...entry, time: getTime() }]);

  const scrollLog = () =>
    setTimeout(() => logEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 120);

  // Most recent run per ticker, five tickers deep.
  const fetchLedger = async () => {
    if (!session) return;
    try {
      const { data, error } = await supabase
        .from('algorithmic_ledger')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(50);

      if (error) throw error;

      if (data && data.length > 0) {
        const seen = new Set<string>();
        const deduped = (data as LedgerRow[])
          .filter((item) => {
            if (seen.has(item.ticker)) return false;
            seen.add(item.ticker);
            return true;
          })
          .slice(0, 5);

        setLedgerItems(deduped);
        setActiveItem((current) => current ?? deduped[0] ?? null);
      }
    } catch (err) {
      console.error('Could not read the algorithmic ledger:', err);
    } finally {
      setLedgerLoading(false);
    }
  };

  // Reads the ledger when a session appears. This is the sanctioned "subscribe
  // to an external system" case: the database is the external system, and the
  // resulting setState lands in a later microtask, not during render.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchLedger();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session]);

  /*
    Hides a run from this session's list. It deliberately does NOT delete the
    ledger row: that table is the shared record the Engine Room grades against,
    it carries no user_id to scope a delete by, and removing rows would destroy
    the accuracy history for everyone. Writes are revoked at the database in
    migrations/001_ledger_rls.sql.
  */
  const dismissLedgerItem = (e: React.MouseEvent, logId: string) => {
    e.stopPropagation();
    setLedgerItems((prev) => prev.filter((item) => item.log_id !== logId));
    if (activeItem?.log_id === logId) setActiveItem(null);
  };

  const toggleWatch = (ticker: string) =>
    setWatchlist((prev) =>
      prev.includes(ticker) ? prev.filter((t) => t !== ticker) : [...prev, ticker],
    );

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
        const { data: staleData } = await supabase
          .from('algorithmic_ledger')
          .select('*')
          .or(`ticker.eq.${apiTicker},ticker.eq.${rawClean}`)
          .order('created_at', { ascending: false })
          .limit(1);

        if (staleData && staleData.length > 0) {
          setActiveItem(staleData[0] as LedgerRow);
          appendLog({ role: 'sys', text: 'Showing the previous stored run for this ticker.' });
          void fetchLedger();
        }
        return;
      }

      // The verdict is written to the ledger in a background task, so the row
      // can trail the response by a moment.
      await new Promise((resolve) => setTimeout(resolve, 3000));

      const { data, error } = await supabase
        .from('algorithmic_ledger')
        .select('*')
        .or(`ticker.eq.${apiTicker},ticker.eq.${rawClean}`)
        .order('created_at', { ascending: false })
        .limit(1);

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
          text: `Pipeline finished with verdict ${resData.verdict}. The ledger row has not appeared yet, retrying.`,
        });
        await new Promise((resolve) => setTimeout(resolve, 2000));
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
    <div className="flex h-screen flex-col bg-term-950 text-fg">
      {/* ------------------------------------------------------------ top bar */}
      <header className="shrink-0 border-b border-rule bg-term-950">
        <div className="flex flex-wrap items-center gap-3 px-4 py-3">
          <button
            type="button"
            onClick={() => setIsSidebarOpen((v) => !v)}
            aria-label={isSidebarOpen ? 'Hide the history panel' : 'Show the history panel'}
            aria-pressed={isSidebarOpen}
            className={`hidden rounded-[2px] border p-2 transition-colors lg:block ${
              isSidebarOpen
                ? 'border-accent text-fg'
                : 'border-rule-strong text-fg-3 hover:border-accent hover:text-fg'
            }`}
          >
            <IconPanel className="h-4 w-4" />
          </button>

          <Link to="/" className="flex items-baseline gap-2">
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
            className="order-last flex w-full min-w-0 flex-1 items-center gap-2 sm:order-none sm:w-auto sm:max-w-xl"
          >
            <label htmlFor="ticker-input" className="sr-only">
              NSE ticker to analyse
            </label>
            <div className="control flex min-w-0 flex-1 items-center gap-2.5 px-3.5 py-2.5">
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
                className="w-full min-w-0 bg-transparent text-base outline-none placeholder:text-fg-3 disabled:opacity-60"
              />
              <span className="kbd hidden shrink-0 sm:inline">Enter</span>
            </div>
            <button type="submit" disabled={isProcessing} className="btn-primary shrink-0">
              {isProcessing ? 'Running' : 'Analyse'}
            </button>
          </form>

          <div className="ml-auto flex items-center gap-4">
            <div className="hidden lg:block">
              <MarketClock compact />
            </div>
            {profile?.timeframe && (
              <p className="label hidden md:block">
                {String(profile.timeframe).replace('_', ' ')} horizon
              </p>
            )}
            <button onClick={logout} className="btn-quiet">
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col md:flex-row">
        {/* ---------------------------------------------------------- sidebar */}
        {isSidebarOpen && (
          <aside className="hidden w-[260px] shrink-0 flex-col border-r border-rule bg-term-900 lg:flex">
            <div className="flex shrink-0 border-b border-rule">
              {(['recent', 'watchlist'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setSidebarTab(tab)}
                  className={`-mb-px flex-1 px-3 py-3 text-2xs font-semibold uppercase tracking-label transition-colors ${
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
                    return (
                      <div
                        key={item.log_id}
                        onClick={() => setActiveItem(item)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') setActiveItem(item);
                        }}
                        className={`group cursor-pointer border p-3 transition-colors ${
                          selected
                            ? 'border-accent bg-term-850'
                            : 'border-rule hover:border-rule-strong'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="truncate text-lg font-bold tracking-tight text-fg">
                              {item.ticker.split('.')[0]}
                            </p>
                            <p
                              className={`mt-0.5 truncate text-2xs font-semibold uppercase tracking-label ${verdictInk(
                                rowVerdict,
                              )}`}
                            >
                              {rowVerdict ?? 'no verdict'}
                            </p>
                          </div>
                          <div className="flex shrink-0 gap-0.5 opacity-0 transition-opacity focus-within:opacity-100 group-hover:opacity-100">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleWatch(item.ticker);
                              }}
                              aria-label={watched ? 'Remove from watchlist' : 'Add to watchlist'}
                              className="p-1 text-fg-3 hover:text-fg"
                            >
                              {watched ? (
                                <IconMarked className="h-3.5 w-3.5 text-fg" />
                              ) : (
                                <IconPlus className="h-3.5 w-3.5" />
                              )}
                            </button>
                            <button
                              onClick={(e) => dismissLedgerItem(e, item.log_id!)}
                              aria-label={`Hide the ${item.ticker} run from this list`}
                              title="Hide from this list. The record itself is kept for grading."
                              className="p-1 text-fg-3 hover:text-fg"
                            >
                              <IconClose className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>
                        <p className="num mt-2 text-2xs text-fg-3">
                          {score != null ? `${(score / 10).toFixed(1)} / 10` : 'unscored'}
                          {item.date ? ` · ${item.date}` : ''}
                        </p>
                      </div>
                    );
                  })
                )
              ) : watchlist.length === 0 ? (
                <p className="p-3 text-sm leading-relaxed text-fg-3">
                  Nothing on the watchlist. Add a ticker from a recent run. The list is kept
                  for this session only.
                </p>
              ) : (
                watchlist.map((ticker) => (
                  <div
                    key={ticker}
                    className="group flex items-center justify-between border border-rule p-3"
                  >
                    <span className="text-base font-medium text-fg">{ticker.split('.')[0]}</span>
                    <div className="flex gap-0.5 opacity-0 transition-opacity focus-within:opacity-100 group-hover:opacity-100">
                      <button
                        onClick={() => runAnalysis(ticker)}
                        disabled={isProcessing}
                        aria-label={`Analyse ${ticker}`}
                        className="p-1 text-fg-3 hover:text-fg disabled:text-rule-strong"
                      >
                        <IconSearch className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => toggleWatch(ticker)}
                        aria-label={`Remove ${ticker} from the watchlist`}
                        className="p-1 text-fg-3 hover:text-down"
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
        <main className="no-scrollbar min-h-0 flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-5 py-6">
            {ledgerLoading && !activeItem ? (
              <div className="flex flex-col gap-6">
                <SkeletonLine className="h-2.5 w-32" />
                <SkeletonLine className="h-9 w-64" />
                <div className="grid gap-8 md:grid-cols-2">
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
                    <p className="mt-5 border-l-2 border-accent pl-5 text-lg leading-relaxed text-fg-2">
                      {asStr(gold.primary_reason)}
                    </p>
                  )}
                </section>

                <div className="grid gap-x-10 gap-y-8 md:grid-cols-2">
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
                                className="rounded-[2px] border border-rule-strong px-2.5 py-1 text-xs text-fg-2 transition-colors hover:border-accent hover:text-fg"
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
