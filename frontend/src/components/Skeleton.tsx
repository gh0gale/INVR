/**
 * Loading placeholders. Every async surface in the app uses one of these while
 * a request is open, so a slow pipeline run reads as work in progress rather
 * than as an empty screen.
 */
import React from 'react';

export const SkeletonLine: React.FC<{ className?: string }> = ({
  className = 'h-3 w-full',
}) => <div className={`skeleton ${className}`} aria-hidden="true" />;

export const SkeletonBlock: React.FC<{
  lines?: number;
  className?: string;
  label?: string;
}> = ({ lines = 3, className = '', label = 'Loading' }) => (
  <div className={`flex flex-col gap-2 ${className}`} role="status" aria-label={label}>
    {Array.from({ length: lines }).map((_, i) => (
      <SkeletonLine key={i} className={`h-3 ${i === lines - 1 ? 'w-2/3' : 'w-full'}`} />
    ))}
  </div>
);

/** Matches the shape of one metric cell so the grid does not jump on load. */
export const SkeletonMetric: React.FC = () => (
  <div className="panel-sunk flex flex-col gap-2 p-3">
    <SkeletonLine className="h-2 w-16" />
    <SkeletonLine className="h-4 w-24" />
  </div>
);

/** Matches one ledger row in the sidebar. */
export const SkeletonRow: React.FC = () => (
  <div className="panel-sunk flex flex-col gap-2 p-3">
    <SkeletonLine className="h-3.5 w-20" />
    <SkeletonLine className="h-2 w-28" />
  </div>
);
