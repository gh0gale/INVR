import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MarketClock } from './MarketClock';
import { useAuth } from '../context/auth';

export const Wordmark: React.FC<{ className?: string }> = ({ className = '' }) => (
  <span className={`text-lg font-bold tracking-tight text-fg ${className}`}>
    INVR<span className="text-accent">.</span>
  </span>
);

export const SiteHeader: React.FC = () => {
  const { pathname } = useLocation();
  const { user, profile, loading, logout } = useAuth();
  const nav = [
    { to: '/', label: 'Overview' },
    { to: '/terms', label: 'Terms' },
    { to: '/privacy', label: 'Privacy' },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-term-950">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-6 px-6 py-3">
        <Link to="/" className="flex items-baseline gap-3">
          <Wordmark />
          <span className="label hidden sm:inline">NSE equities</span>
        </Link>

        <div className="hidden lg:block">
          <MarketClock compact />
        </div>

        <nav className="flex items-center gap-5">
          {nav.map((n) => (
            <Link
              key={n.to}
              to={n.to}
              className={`text-2xs font-semibold uppercase tracking-label transition-colors ${
                pathname === n.to ? 'text-accent' : 'text-fg-3 hover:text-fg'
              }`}
            >
              {n.label}
            </Link>
          ))}

          {/* An authenticated visitor is never offered a sign-in link. */}
          {loading ? (
            <span className="skeleton h-9 w-28" aria-hidden="true" />
          ) : user ? (
            <>
              <Link to={profile ? '/workspace' : '/onboarding'} className="btn-primary">
                {profile ? 'Workspace' : 'Finish setup'}
              </Link>
              <button type="button" onClick={logout} className="btn-quiet">
                Sign out
              </button>
            </>
          ) : (
            <Link to="/auth" className="btn-quiet">
              Sign in
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
};

export const SiteFooter: React.FC = () => (
  <footer className="mt-20 border-t border-rule bg-term-900">
    <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 py-8 sm:flex-row sm:items-start sm:justify-between">
      <div className="max-w-md">
        <Wordmark className="text-base" />
        <p className="mt-2 text-xs leading-relaxed text-fg-3">
          Quantitative analysis of NSE-listed equities for educational use. Not investment
          advice, and not a SEBI-registered investment adviser.
        </p>
      </div>
      <nav className="flex gap-5">
        <Link
          to="/terms"
          className="text-2xs font-semibold uppercase tracking-label text-fg-3 hover:text-accent"
        >
          Terms
        </Link>
        <Link
          to="/privacy"
          className="text-2xs font-semibold uppercase tracking-label text-fg-3 hover:text-accent"
        >
          Privacy
        </Link>
      </nav>
    </div>
  </footer>
);

/** Shared shell for the public, text-heavy pages. */
export const DocumentPage: React.FC<
  React.PropsWithChildren<{ title: string; updated: string; summary: string }>
> = ({ title, updated, summary, children }) => (
  <div className="flex min-h-screen flex-col bg-term-950">
    <SiteHeader />
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
      <p className="label mb-3">Last updated {updated}</p>
      <h1 className="text-5xl font-semibold leading-[1.1] text-fg">{title}</h1>
      <p className="mt-5 border-l-2 border-accent pl-5 text-lg leading-relaxed text-fg-2">
        {summary}
      </p>
      <div className="mt-10 flex flex-col gap-8">{children}</div>
    </main>
    <SiteFooter />
  </div>
);

export const Clause: React.FC<React.PropsWithChildren<{ n: string; heading: string }>> = ({
  n,
  heading,
  children,
}) => (
  <section>
    <h2 className="mb-3 flex items-baseline gap-3 border-b border-rule pb-2">
      <span className="num text-sm text-accent">{n}</span>
      <span className="text-2xl font-semibold text-fg">{heading}</span>
    </h2>
    <div className="flex flex-col gap-4 text-base leading-relaxed text-fg-2">{children}</div>
  </section>
);
