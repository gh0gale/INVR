import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../supabase';
import { SiteHeader, SiteFooter } from '../components/SiteChrome';
import { SkeletonLine, SkeletonBlock } from '../components/Skeleton';
import { TickerTape } from '../components/TickerTape';
import { MarketClock } from '../components/MarketClock';
import { PipelineScroller } from '../components/PipelineScroller';
import { HeroEngine } from '../components/HeroEngine';
import { Disclaimer } from '../components/analysis';
import { AnimatedNumber } from '../components/motion';
import { useDocumentTitle, useInView } from '../hooks';
import { useAuth } from '../context/auth';
import type { LedgerRow } from '../types';

/**
 * What the product is for, stated as consequences rather than features. Laid
 * out as a two-column definition list, not a row of feature cards.
 */
const BENEFITS = [
  {
    k: 'A verdict you can audit',
    v: 'Every call arrives with the gate results that produced it, so you can see which condition failed instead of taking a score on faith.',
  },
  {
    k: 'Position sizes, not vibes',
    v: 'A strong buy comes with an entry band, a stop and two targets derived from that stock volatility, sized so a stop-out costs two percent of the capital you stated.',
  },
  {
    k: 'The same rules every time',
    v: 'Thresholds live in one versioned file. The engine cannot talk itself into a different answer on a Tuesday, and changes to those thresholds are recorded.',
  },
  {
    k: 'Scored against reality',
    v: 'Past calls are graded on real market highs and lows once the horizon matures, so the system accumulates a record rather than a reputation.',
  },
  {
    k: 'Explained at your level',
    v: 'A tutor answers questions about the loaded analysis using the actual figures, pitched at the experience level you set during setup.',
  },
  {
    k: 'Nothing linked to your broker',
    v: 'No credentials, no holdings, no order placement. You give it a ticker and a risk profile, and that is the whole surface.',
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const { user, profile } = useAuth();
  useDocumentTitle();

  // Signed-in visitors get sent straight into the product, never back to a
  // sign-in screen they have already passed.
  const enter = () => navigate(user ? (profile ? '/workspace' : '/onboarding') : '/auth');
  const enterLabel = user ? (profile ? 'Go to the workspace' : 'Finish your profile') : 'Open the workspace';

  // Real rows out of the ledger. Nothing on this page is a mockup: if the
  // table is empty or unreadable anonymously, the sections say so.
  const [rows, setRows] = useState<LedgerRow[]>([]);
  const [state, setState] = useState<'loading' | 'ready' | 'empty' | 'error'>('loading');

  const [statsRef, statsInView] = useInView<HTMLDListElement>();

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const { data, error } = await supabase
          .from('algorithmic_ledger')
          .select('ticker, timeframe, date, created_at, silver_state, gold_verdict')
          .order('created_at', { ascending: false })
          .limit(12);

        if (cancelled) return;
        if (error) return setState('error');
        if (!data || data.length === 0) return setState('empty');

        setRows(data as LedgerRow[]);
        setState('ready');
      } catch {
        if (!cancelled) setState('error');
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const sample = rows[0] ?? null;
  const distinctTickers = new Set(rows.map((r) => r.ticker)).size;

  return (
    <div className="flex min-h-screen flex-col bg-term-950">
      <SiteHeader />

      {/* Live tape of what the engine has actually recorded. */}
      {state === 'ready' && <TickerTape rows={rows} />}
      {state === 'loading' && (
        <div className="border-y border-rule bg-term-900 px-4 py-2.5">
          <SkeletonLine className="h-3 w-64" />
        </div>
      )}

      {/* ---------------------------------------------------------------- hero */}
      <section className="border-b border-rule">
        <div className="mx-auto max-w-6xl px-6 py-16 md:py-20">
          <div className="mb-7 flex flex-wrap items-center gap-x-6 gap-y-2">
            <p className="label-accent">Algorithmic portfolio analyser</p>
            <div className="lg:hidden">
              <MarketClock compact />
            </div>
          </div>

          <h1 className="max-w-4xl text-4xl font-extrabold leading-[1.03] tracking-tight text-fg sm:text-5xl md:text-6xl">
            The verdict is arithmetic.
            <br />
            <span className="text-fg-3">The explanation comes after.</span>
          </h1>

          <p className="mt-7 max-w-2xl text-xl leading-relaxed text-fg-2">
            INVR runs a fixed quantitative pipeline over an NSE ticker and returns one of five
            verdicts with the gate results that produced it. A language model then
            explains that output against your stated risk profile. It never gets a vote on the
            conclusion.
          </p>

          <div className="mt-9 flex flex-wrap items-center gap-4">
            <button onClick={enter} className="btn-primary btn-lg">
              {enterLabel}
            </button>
            <a href="#run" className="btn-quiet btn-lg">
              See a full run
            </a>
          </div>
        </div>

        {/* The mechanism, running. This is the page's main visual. */}
        <div className="mx-auto max-w-6xl px-6 pb-16">
          {state === 'loading' ? (
            <div className="panel p-6" role="status" aria-label="Loading a recorded run">
              <SkeletonLine className="h-3 w-40" />
              <div className="mt-6 grid gap-4 lg:grid-cols-5">
                <SkeletonBlock lines={4} />
                <SkeletonBlock lines={4} />
                <SkeletonBlock lines={4} />
                <SkeletonBlock lines={4} />
                <SkeletonBlock lines={4} />
              </div>
            </div>
          ) : (
            <HeroEngine row={sample} loading={false} />
          )}
        </div>
      </section>

      {/* ------------------------------------------------------------ numbers */}
      <section className="border-b border-rule bg-term-900">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <dl ref={statsRef} className="grid grid-cols-2 gap-x-10 gap-y-8 sm:grid-cols-4">
            <Stat label="Verdicts" value={5} suffix=" fixed" active={statsInView} />
            <Stat label="Horizons" value={4} active={statsInView} />
            <Stat
              label="In the ledger"
              value={state === 'ready' ? distinctTickers : null}
              suffix=" tickers"
              active={statsInView}
            />
            <div>
              <dt className="label mb-2">Model role</dt>
              <dd className="text-3xl font-bold tracking-tight text-fg">Explain</dd>
            </div>
          </dl>
        </div>
      </section>

      {/* ----------------------------------------------------------- benefits */}
      <section className="border-b border-rule">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <p className="label-accent mb-3">What you get</p>
          <h2 className="h-section max-w-3xl">
            Screening you can take apart and check
          </h2>

          <dl className="mt-10 grid gap-x-14 md:grid-cols-2">
            {BENEFITS.map((b) => (
              <div key={b.k} className="border-t border-rule py-6">
                <dt className="text-xl font-bold tracking-tight text-fg">{b.k}</dt>
                <dd className="mt-2.5 text-base leading-relaxed text-fg-2">{b.v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* ------------------------------------------------------ the scroll run */}
      <section id="run" className="border-b border-rule">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="mb-10 max-w-2xl">
            <p className="label-accent mb-3">One run, layer by layer</p>
            <h2 className="h-section">How a verdict is produced</h2>
            <p className="mt-4 text-lg leading-relaxed text-fg-2">
              Scroll to advance the pipeline. The panel holds a real row from the algorithmic
              ledger, rendered by the same components the workspace uses.
            </p>
          </div>

          {state === 'loading' && (
            <div className="panel p-6" role="status" aria-label="Loading the latest run">
              <SkeletonLine className="h-3 w-32" />
              <SkeletonLine className="mt-4 h-9 w-64" />
              <div className="mt-8 grid gap-8 md:grid-cols-2">
                <SkeletonBlock lines={6} />
                <SkeletonBlock lines={6} />
              </div>
            </div>
          )}

          {state === 'ready' && sample && <PipelineScroller row={sample} />}

          {state === 'empty' && (
            <div className="panel p-8">
              <p className="label-accent mb-3">No published run</p>
              <p className="max-w-xl text-base leading-relaxed text-fg-2">
                The ledger has no analysis recorded yet. Rather than animate an invented one,
                this section stays empty until the engine has actually produced something. Sign
                in and analyse a ticker to populate it.
              </p>
            </div>
          )}

          {state === 'error' && (
            <div className="panel p-8">
              <p className="label-accent mb-3">Sample unavailable</p>
              <p className="max-w-xl text-base leading-relaxed text-fg-2">
                The ledger could not be read from this page. That is usually row-level security
                declining an anonymous request, which is the correct default. Sign in to see
                real output in the workspace.
              </p>
            </div>
          )}

          {state === 'ready' && (
            <div className="mt-10 border-t border-rule pt-6">
              <Disclaimer />
            </div>
          )}
        </div>
      </section>

      {/* ------------------------------------------------------------- sign in */}
      <section>
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="flex flex-wrap items-center gap-5">
            <button onClick={enter} className="btn-primary btn-lg">
              {enterLabel}
            </button>
            <p className="text-base text-fg-3">
              By signing in you accept the{' '}
              <Link to="/terms" className="link">
                terms
              </Link>{' '}
              and the{' '}
              <Link to="/privacy" className="link">
                privacy policy
              </Link>
              .
            </p>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

const Stat: React.FC<{
  label: string;
  value: number | null;
  suffix?: string;
  active: boolean;
}> = ({ label, value, suffix = '', active }) => (
  <div>
    <dt className="label mb-2">{label}</dt>
    <dd className="num text-3xl font-medium text-fg">
      {value == null ? (
        <span className="text-fg-3">n/a</span>
      ) : (
        <AnimatedNumber
          value={value}
          format={(v) => `${Math.round(v)}`}
          active={active}
          durationMs={900}
        />
      )}
      {value != null && suffix && <span className="text-base text-fg-3">{suffix}</span>}
    </dd>
  </div>
);
