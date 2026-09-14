/**
 * Top-level error boundary.
 *
 * Audit finding NEW-FE-12: a render-time exception white-screened the whole app
 * with no recovery path. The risk is concrete rather than theoretical, because
 * `RichText` and `analysis.tsx` both parse model output and jsonb columns whose
 * shape is not guaranteed.
 *
 * Hand-written rather than pulling in `react-error-boundary`: this is the only
 * place it is needed and the class component is twenty lines.
 */
import React from 'react';

type Props = { children: React.ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Left as console output on purpose: there is no error-tracking service
    // wired up, and inventing one would be a dependency the operator did not
    // choose. This is the hook to attach Sentry or equivalent later.
    console.error('Unhandled render error:', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="flex min-h-screen items-center justify-center bg-term-950 px-6">
        <div className="panel max-w-lg p-8">
          <p className="label-accent mb-3">Something broke</p>
          <h1 className="text-3xl font-bold tracking-tight text-fg">
            This screen failed to render
          </h1>
          <p className="mt-4 text-base leading-relaxed text-fg-2">
            The error is logged to the browser console. Your account and your saved
            analyses are unaffected: nothing on this screen writes to the database.
          </p>

          <div className="panel-sunk mt-5 px-4 py-3">
            <p className="label mb-1">Error message</p>
            <p className="text-sm leading-relaxed text-fg-2">
              {this.state.error.message || 'No message was attached to the error.'}
            </p>
          </div>

          <div className="mt-7 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => this.setState({ error: null })}
              className="btn-primary"
            >
              Try again
            </button>
            <a href="/" className="btn-quiet">
              Back to the overview
            </a>
          </div>
        </div>
      </div>
    );
  }
}
