import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../supabase';
import { useAuth } from '../context/auth';
import { SiteFooter, Wordmark } from '../components/SiteChrome';
import { errorMessage } from '../types';

type Mode = 'login' | 'register';

export default function Auth() {
  const navigate = useNavigate();
  const { fetchProfile } = useAuth();

  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const routeAfterAuth = async (token: string) => {
    const profile = await fetchProfile(token);
    navigate(profile ? '/workspace' : '/onboarding');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setNotice(null);

    try {
      if (mode === 'register') {
        const { data, error: signUpError } = await supabase.auth.signUp({ email, password });
        if (signUpError) throw signUpError;

        if (data.session) {
          await routeAfterAuth(data.session.access_token);
        } else {
          setNotice('Account created. Check your inbox to confirm the address, then sign in.');
          setMode('login');
        }
      } else {
        const { data, error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signInError) throw signInError;
        if (data.session) await routeAfterAuth(data.session.access_token);
      }
    } catch (err: unknown) {
      setError(errorMessage(err, 'Authentication failed. Check the email and password.'));
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!email) {
      setError('Enter your email address first, then request a reset link.');
      return;
    }
    setResetting(true);
    setError(null);
    setNotice(null);
    try {
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email);
      if (resetError) throw resetError;
      setNotice(`If an account exists for ${email}, a reset link is on its way.`);
    } catch (err: unknown) {
      setError(errorMessage(err, 'Could not send a reset link.'));
    } finally {
      setResetting(false);
    }
  };

  const busy = loading || resetting;

  return (
    <div className="flex min-h-screen flex-col bg-term-950">
      <header className="border-b border-rule">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-baseline gap-2">
            <Wordmark />
            <span className="label hidden sm:inline">Portfolio analyser</span>
          </Link>
          <Link to="/" className="text-xs font-semibold uppercase tracking-label text-fg-3 hover:text-fg">
            Back to overview
          </Link>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-1 items-start justify-center px-6 py-16">
        <div className="grid w-full max-w-3xl gap-12 md:grid-cols-[1fr_1.1fr]">
          {/* Left: what signing in actually gets you. No decorative panel. */}
          <div className="hidden flex-col justify-between md:flex">
            <div>
              <h1 className="text-4xl font-bold leading-tight tracking-tight text-fg">
                {mode === 'login' ? 'Sign in' : 'Create an account'}
              </h1>
              <p className="mt-5 text-base leading-relaxed text-fg-2">
                An account stores your risk profile and analysis history so the engine can
                frame results against your stated horizon and capital.
              </p>
            </div>

            <dl className="mt-10 border-t border-rule">
              {[
                ['Stored', 'Email, risk profile, analysis history'],
                ['Not stored', 'Brokerage credentials, holdings, PAN'],
                ['Analysis', 'Runs server side, on demand'],
              ].map(([k, v]) => (
                <div key={k} className="border-b border-rule py-3">
                  <dt className="label mb-1">{k}</dt>
                  <dd className="text-base text-fg-2">{v}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Right: the form. */}
          <div className="panel p-6 md:p-8">
            <div className="mb-6 flex border-b border-rule">
              {(['login', 'register'] as Mode[]).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => {
                    setMode(tab);
                    setError(null);
                    setNotice(null);
                  }}
                  className={`-mb-px px-4 py-2.5 text-xs font-semibold uppercase tracking-label transition-colors ${
                    mode === tab
                      ? 'border-b-2 border-accent text-fg'
                      : 'border-b-2 border-transparent text-fg-3 hover:text-fg'
                  }`}
                >
                  {tab === 'login' ? 'Sign in' : 'Register'}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="email" className="label">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="field"
                  placeholder="you@example.com"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="password" className="label">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="field"
                  placeholder={mode === 'login' ? 'Your password' : 'At least 6 characters'}
                />
              </div>

              {error && (
                <p role="alert" className="panel-sunk px-3.5 py-3 text-base text-down">
                  {error}
                </p>
              )}
              {notice && (
                <p role="status" className="panel-sunk px-3.5 py-3 text-base text-fg-2">
                  {notice}
                </p>
              )}

              <button type="submit" disabled={busy} className="btn-primary mt-1">
                {loading
                  ? mode === 'login'
                    ? 'Signing in'
                    : 'Creating account'
                  : mode === 'login'
                    ? 'Sign in'
                    : 'Create account'}
              </button>

              {mode === 'login' && (
                <button
                  type="button"
                  onClick={handleReset}
                  disabled={busy}
                  className="self-start text-xs font-semibold uppercase tracking-label text-fg-3 hover:text-fg disabled:text-rule-strong"
                >
                  {resetting ? 'Sending reset link' : 'Forgot password'}
                </button>
              )}

              {mode === 'register' && (
                <p className="text-sm leading-relaxed text-fg-3">
                  Creating an account means you accept the{' '}
                  <Link to="/terms" className="link">
                    terms of service
                  </Link>{' '}
                  and the{' '}
                  <Link to="/privacy" className="link">
                    privacy policy
                  </Link>
                  .
                </p>
              )}
            </form>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
