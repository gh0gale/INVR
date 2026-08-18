/**
 * Tutor panel: transcript plus composer.
 *
 * The composer is a real editor rather than a bare text box. It states what it
 * accepts, shows the submit keys, grows with the message, disables its own
 * send button when there is nothing to send, and says plainly which analysis
 * is in context so an answer is never mistaken for a general one.
 */
import React, { useRef } from 'react';
import { SkeletonLine } from './Skeleton';
import { RichText } from './RichText';
import type { LedgerRow } from '../types';

export type LogEntry = { role: 'sys' | 'user' | 'ai'; text: string; time: string };

export const TutorPanel: React.FC<{
  log: LogEntry[];
  command: string;
  setCommand: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isProcessing: boolean;
  isStreaming: boolean;
  activeItem: LedgerRow | null;
  logEndRef: React.RefObject<HTMLDivElement | null>;
}> = ({
  log,
  command,
  setCommand,
  onSubmit,
  isProcessing,
  isStreaming,
  activeItem,
  logEndRef,
}) => {
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const hasConversation = log.some((m) => m.role === 'user');

  // Real questions the tutor can answer from the loaded context. Shown only
  // until the first message, so they prompt rather than clutter.
  const starters = activeItem
    ? [
        'Explain this verdict in plain terms',
        'Which gate is closest to flipping?',
        'How was the stop loss calculated?',
      ]
    : ['What does ATR measure?', 'How is RSI read?', 'What is a death cross?'];

  const resetHeight = () => {
    if (composerRef.current) composerRef.current.style.height = 'auto';
  };

  const handleSubmit = (e: React.FormEvent) => {
    onSubmit(e);
    resetHeight();
  };

  return (
    <section className="flex min-h-[26rem] shrink-0 flex-col border-t border-rule bg-term-900 md:min-h-0 md:w-[26rem] md:border-l md:border-t-0 xl:w-[30rem]">
      <header className="shrink-0 border-b border-rule px-5 py-4">
        <div className="flex items-baseline justify-between gap-4">
          <h2 className="h-panel">Tutor</h2>
          <span className="label">{isProcessing ? 'Working' : 'Ready'}</span>
        </div>
        <p className="mt-1.5 text-sm text-fg-3">
          {activeItem
            ? 'Answering with the ' + activeItem.ticker + ' analysis in context'
            : 'No analysis loaded, so answers will be general.'}
        </p>
      </header>

      <div className="no-scrollbar flex flex-1 flex-col gap-5 overflow-y-auto px-5 py-5">
        {log.map((msg, i) => {
          const isLast = i === log.length - 1;
          const who = msg.role === 'user' ? 'You' : msg.role === 'sys' ? 'System' : 'Tutor';
          return (
            <article key={i} className="flex flex-col gap-1.5">
              <div className="flex items-baseline gap-2.5">
                <span
                  className={
                    'text-2xs font-semibold uppercase tracking-label ' +
                    (msg.role === 'user'
                      ? 'text-fg-3'
                      : msg.role === 'sys'
                        ? 'text-note'
                        : 'text-accent')
                  }
                >
                  {who}
                </span>
                <span className="num text-2xs text-fg-3">{msg.time}</span>
              </div>
              {msg.role === 'ai' ? (
                <div
                  className={
                    'text-base leading-relaxed text-fg-2' +
                    (isStreaming && isLast ? ' caret' : '')
                  }
                >
                  <RichText text={msg.text} />
                </div>
              ) : (
                <p
                  className={
                    'whitespace-pre-wrap text-base leading-relaxed ' +
                    (msg.role === 'user'
                      ? 'border-l-2 border-rule-strong pl-3.5 text-fg-2'
                      : 'text-fg-3')
                  }
                >
                  {msg.text}
                </p>
              )}
            </article>
          );
        })}

        {isProcessing && !isStreaming && (
          <div role="status" aria-label="Waiting for the tutor" className="flex flex-col gap-2">
            <SkeletonLine className="h-2.5 w-20" />
            <SkeletonLine className="h-3.5 w-full" />
            <SkeletonLine className="h-3.5 w-4/5" />
          </div>
        )}

        <div ref={logEndRef} />
      </div>

      {/* Starters disappear once a real conversation begins. */}
      {!hasConversation && !isProcessing && (
        <div className="shrink-0 border-t border-rule px-5 py-4">
          <p className="label mb-2.5">Try asking</p>
          <div className="flex flex-wrap gap-2">
            {starters.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setCommand(q)}
                className="rounded-[2px] border border-rule-strong px-3 py-1.5 text-sm text-fg-2 transition-colors hover:border-accent hover:text-accent"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="shrink-0 border-t border-rule bg-term-950 px-5 py-4">
        <label htmlFor="tutor-input" className="label mb-2 block">
          Ask a question, or enter a ticker to analyse
        </label>

        <div className="control flex flex-col gap-2 p-2.5">
          <textarea
            id="tutor-input"
            ref={composerRef}
            rows={2}
            value={command}
            onChange={(e) => {
              setCommand(e.target.value);
              const el = e.currentTarget;
              el.style.height = 'auto';
              el.style.height = Math.min(el.scrollHeight, 168) + 'px';
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                e.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder={
              isProcessing
                ? 'Waiting for the engine'
                : activeItem
                  ? 'Why did this gate fail?'
                  : 'What does ATR measure?'
            }
            disabled={isProcessing}
            className="w-full resize-none bg-transparent text-base leading-relaxed outline-none placeholder:text-fg-3 disabled:opacity-60"
          />

          <div className="flex items-center justify-between gap-3 border-t border-rule pt-2.5">
            <p className="text-2xs text-fg-3">
              <span className="kbd">Enter</span> sends, <span className="kbd">Shift</span> +{' '}
              <span className="kbd">Enter</span> adds a line
            </p>
            <button
              type="submit"
              disabled={isProcessing || !command.trim()}
              className="btn-primary shrink-0"
            >
              Send
            </button>
          </div>
        </div>

        <p className="mt-2.5 text-2xs leading-relaxed text-fg-3">
          A bare ticker, or <span className="num text-fg-2">/analyze TICKER</span>, runs the
          pipeline instead of asking the tutor.
        </p>
      </form>
    </section>
  );
};
