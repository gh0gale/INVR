/**
 * NSE session state.
 *
 * Real, and genuinely useful in a screening tool: whether the exchange is open
 * decides whether an intraday verdict means anything right now. The pulse on
 * the status dot reports one fact, that the session is live, and stops when it
 * is not.
 *
 * Regular equity hours only. Exchange holidays are not known to the client, so
 * the component says so rather than implying a certainty it does not have.
 */
import React, { useEffect, useState } from 'react';

const IST_OFFSET_MIN = 5 * 60 + 30;

type Session = {
  label: string;
  state: 'pre-open' | 'open' | 'closed' | 'weekend';
  clock: string;
  detail: string;
};

/** Minutes since IST midnight, plus the IST weekday. */
function istNow(now: Date): { minutes: number; day: number; clock: string } {
  const utcMinutes = now.getUTCHours() * 60 + now.getUTCMinutes();
  const total = utcMinutes + IST_OFFSET_MIN;
  const dayShift = Math.floor(total / (24 * 60));
  const minutes = ((total % (24 * 60)) + 24 * 60) % (24 * 60);
  const day = (now.getUTCDay() + dayShift + 7) % 7;

  const hh = String(Math.floor(minutes / 60)).padStart(2, '0');
  const mm = String(minutes % 60).padStart(2, '0');
  const ss = String(now.getUTCSeconds()).padStart(2, '0');

  return { minutes, day, clock: `${hh}:${mm}:${ss}` };
}

const PRE_OPEN = 9 * 60; // 09:00 IST
const OPEN = 9 * 60 + 15; // 09:15 IST
const CLOSE = 15 * 60 + 30; // 15:30 IST

function describe(now: Date): Session {
  const { minutes, day, clock } = istNow(now);

  const untilText = (target: number) => {
    const delta = target - minutes;
    const h = Math.floor(delta / 60);
    const m = delta % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  if (day === 0 || day === 6) {
    return {
      label: 'Weekend',
      state: 'weekend',
      clock,
      detail: 'Regular session resumes Monday 09:15 IST',
    };
  }
  if (minutes >= PRE_OPEN && minutes < OPEN) {
    return {
      label: 'Pre-open',
      state: 'pre-open',
      clock,
      detail: `Continuous trading in ${untilText(OPEN)}`,
    };
  }
  if (minutes >= OPEN && minutes < CLOSE) {
    return {
      label: 'Session open',
      state: 'open',
      clock,
      detail: `Closes in ${untilText(CLOSE)}`,
    };
  }
  return {
    label: 'Session closed',
    state: 'closed',
    clock,
    detail:
      minutes >= CLOSE ? 'Reopens 09:15 IST tomorrow' : `Pre-open in ${untilText(PRE_OPEN)}`,
  };
}

const dotInk: Record<Session['state'], string> = {
  open: 'bg-up',
  'pre-open': 'bg-accent',
  closed: 'bg-fg-3',
  weekend: 'bg-fg-3',
};

export const MarketClock: React.FC<{ compact?: boolean }> = ({ compact = false }) => {
  const [session, setSession] = useState<Session>(() => describe(new Date()));

  useEffect(() => {
    const id = setInterval(() => setSession(describe(new Date())), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex items-center gap-2.5" title={`${session.detail}. Exchange holidays not accounted for.`}>
      <span
        className={`h-1.5 w-1.5 rounded-full ${dotInk[session.state]} ${
          session.state === 'open' ? 'session-live' : ''
        }`}
        aria-hidden="true"
      />
      <span className="label whitespace-nowrap">{session.label}</span>
      <span className="num text-2xs text-fg-2" aria-label="Indian Standard Time">
        {session.clock} IST
      </span>
      {!compact && (
        <span className="label hidden xl:inline text-fg-3">{session.detail}</span>
      )}
    </div>
  );
};
