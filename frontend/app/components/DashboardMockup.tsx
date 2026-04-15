"use client";

export default function DashboardMockup() {
  return (
    <div className="relative w-full max-w-[520px] mx-auto pb-10">
      {/* Main Dashboard Container */}
      <div className="rounded-xl border border-line bg-bg-surface overflow-hidden shadow-2xl shadow-black/50">
        {/* Dashboard Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-line">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-gain" />
            <span className="text-xs font-medium text-fg-faint tracking-wide uppercase font-mono">
              Live Analysis
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-fg-faint font-mono">15 Apr 2026</span>
            <div className="w-1.5 h-1.5 rounded-full bg-gain animate-pulse" />
          </div>
        </div>

        {/* Stock Scorecard */}
        <div className="px-5 py-4 border-b border-line">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2.5 mb-1">
                <span className="text-lg font-semibold text-fg tracking-tight">RELIANCE</span>
                <span className="text-xs px-2 py-0.5 rounded bg-gain/10 text-gain font-mono font-medium">
                  +2.34%
                </span>
              </div>
              <p className="text-xs text-fg-faint font-mono">Reliance Industries Ltd · NSE</p>
            </div>
            {/* Score Ring */}
            <div className="relative flex items-center justify-center">
              <svg width="56" height="56" viewBox="0 0 56 56" className="-rotate-90">
                <circle cx="28" cy="28" r="24" fill="none" stroke="#1a1a1a" strokeWidth="3" />
                <circle
                  cx="28" cy="28" r="24" fill="none"
                  stroke="#22C55E" strokeWidth="3" strokeLinecap="round"
                  strokeDasharray={`${(7.8 / 10) * 150.8} 150.8`}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-base font-semibold text-fg leading-none">7.8</span>
                <span className="text-[9px] text-fg-faint leading-none mt-0.5">/10</span>
              </div>
            </div>
          </div>

          {/* Score Breakdown */}
          <div className="grid grid-cols-4 gap-3 mt-4">
            {[
              { label: "Fundamental", value: 8.2, color: "#22C55E" },
              { label: "Technical", value: 7.1, color: "#22C55E" },
              { label: "Macro", value: 6.9, color: "#F59E0B" },
              { label: "Risk", value: 8.8, color: "#22C55E" },
            ].map((metric) => (
              <div key={metric.label} className="text-center">
                <div className="text-sm font-semibold font-mono" style={{ color: metric.color }}>
                  {metric.value}
                </div>
                <div className="text-[10px] text-fg-faint mt-0.5 leading-tight">{metric.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Mini Chart */}
        <div className="px-5 py-4 border-b border-line">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-fg-faint font-mono">Price Action · 6M</span>
            <span className="text-xs text-fg-muted font-mono">₹2,847.50</span>
          </div>
          <svg viewBox="0 0 400 80" className="w-full h-[72px]" preserveAspectRatio="none">
            {[0, 20, 40, 60, 80].map((y) => (
              <line key={y} x1="0" y1={y} x2="400" y2={y} stroke="#1a1a1a" strokeWidth="1" />
            ))}
            <defs>
              <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22C55E" stopOpacity="0.12" />
                <stop offset="100%" stopColor="#22C55E" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path
              d="M0,65 L30,60 L60,58 L90,55 L120,48 L150,52 L180,45 L210,38 L240,42 L270,35 L300,28 L330,22 L360,25 L400,18"
              fill="none" stroke="#22C55E" strokeWidth="1.5"
            />
            <path
              d="M0,65 L30,60 L60,58 L90,55 L120,48 L150,52 L180,45 L210,38 L240,42 L270,35 L300,28 L330,22 L360,25 L400,18 L400,80 L0,80 Z"
              fill="url(#chartGrad)"
            />
            <circle cx="400" cy="18" r="3" fill="#22C55E" />
            <circle cx="400" cy="18" r="6" fill="#22C55E" opacity="0.2" />
          </svg>

          {/* Level Indicators */}
          <div className="flex items-center justify-between mt-3 px-1">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-gain" />
              <span className="text-[10px] text-fg-faint font-mono">Entry ₹2,780</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-amber" />
              <span className="text-[10px] text-fg-faint font-mono">Target ₹3,120</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-loss" />
              <span className="text-[10px] text-fg-faint font-mono">Stop ₹2,650</span>
            </div>
          </div>
        </div>
      </div>

      {/* Floating AI Analysis — overlapping bottom-right like reference */}
      <div className="absolute -bottom-4 right-[-8px] z-20 w-[360px] rounded-xl bg-[#0e0e0e] border border-neutral-700/40 shadow-2xl shadow-black/80 px-4 py-3.5">
        <div className="flex items-start gap-3">
          {/* Circular icon with pulse/heartbeat */}
          <div className="w-9 h-9 rounded-full bg-[#2a2a2c] border border-neutral-600/40 flex items-center justify-center shrink-0">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a0a0a0" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12h4l3-9 4 18 3-9h4" />
            </svg>
          </div>
          <div className="flex-1 min-w-0 pt-0.5">
            <p className="text-[13px] text-neutral-400 font-medium mb-1">AI Analysis</p>
            <p className="text-[13px] text-neutral-300 leading-[1.55]">
              Strong P/E ratio indicates undervaluation
              relative to sector average...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
