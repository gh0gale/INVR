/**
 * Decisions around a stock run that must not depend on render timing.
 */
export type RunOutcome = 'success' | 'failed' | 'fallback';

/**
 * Open the tutor after a run only when that run succeeded with a ledger row,
 * is still the latest run (a superseded or abandoned run does not), the
 * workspace is still mounted, and the user has not switched auto-open off.
 * Called once from the run's completion, never from an effect, so a re-render
 * cannot open it again.
 */
export function shouldAutoOpenTutor(p: {
  outcome: RunOutcome;
  runId: number;
  latestRunId: number;
  mounted: boolean;
  enabled: boolean;
}): boolean {
  return p.outcome === 'success' && p.runId === p.latestRunId && p.mounted && p.enabled;
}

/** First login: the profile is loaded and the tour has never been finished or skipped. */
export const shouldStartTour = (profile: { tour_completed_at?: string | null } | null): boolean =>
  profile != null && !profile.tour_completed_at;
