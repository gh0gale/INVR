import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { Search, Plus, BookmarkCheck, CornerDownRight } from 'lucide-react';

// ==========================================
// 1. LIQUID GLASS SYSTEM — exact §4 tokens
// ==========================================
const glass = {
    // Tier 1 — outer card surfaces
    base: {
        background: 'linear-gradient(145deg, rgba(255,255,255,0.09) 0%, rgba(255,255,255,0.028) 100%)',
        backdropFilter: 'blur(72px)',
        WebkitBackdropFilter: 'blur(72px)',
        border: '1px solid rgba(255,255,255,0.13)',
        boxShadow: [
            'inset 0 1.5px 0 rgba(255,255,255,0.26)',
            'inset 1.5px 0 0 rgba(255,255,255,0.09)',
            'inset -1px 0 0 rgba(0,0,0,0.08)',
            'inset 0 -1.5px 0 rgba(0,0,0,0.10)',
            '0 40px 100px rgba(0,0,0,0.52)',
            '0 8px 20px rgba(0,0,0,0.28)',
        ].join(', '),
    } as React.CSSProperties,

    // Tier 2 — nested panels, no backdrop-filter
    nested: {
        background: 'linear-gradient(145deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.01) 100%)',
        border: '1px solid rgba(255,255,255,0.085)',
        boxShadow: [
            'inset 0 1px 0 rgba(255,255,255,0.20)',
            'inset 1px 0 0 rgba(255,255,255,0.06)',
            '0 8px 32px rgba(0,0,0,0.22)',
        ].join(', '),
    } as React.CSSProperties,

    // Tier 3 — pills, badges, nav items
    pill: {
        background: 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)',
        border: '1px solid rgba(255,255,255,0.10)',
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.20), 0 4px 12px rgba(0,0,0,0.15)',
    } as React.CSSProperties,
};

// Shared spring physics — §6.1, defined once
const springSoft  = { type: 'spring', stiffness: 220, damping: 28, mass: 0.9 } as const;
const springPress = { type: 'spring', stiffness: 420, damping: 26, mass: 0.6 } as const;

// ==========================================
// 2. THREE.JS STARFIELD — §7 exact recipe
// ==========================================
function DataPoints() {
    const pointsRef = useRef<any>();
    const count = 2500;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
        positions[i * 3]     = (Math.random() - 0.5) * 35;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }
    useFrame((state) => {
        if (pointsRef.current) {
            pointsRef.current.rotation.y = state.clock.elapsedTime * 0.06;
            pointsRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.1) * 0.15;
        }
    });
    return (
        <points ref={pointsRef}>
            <bufferGeometry>
                <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
            </bufferGeometry>
            {/* opacity: 0.8 per §7 exact spec */}
            <pointsMaterial size={0.045} color="#10B981" transparent opacity={0.8} sizeAttenuation />
        </points>
    );
}

// ==========================================
// 3. CHART UTILITY — §7 Catmull-Rom recipe
// ==========================================
const CHART_W = 600;
const CHART_H  = 160;
const CHART_PAD = 10;

function buildPriceChart(prices: number[]) {
    const min   = Math.min(...prices);
    const max   = Math.max(...prices);
    const range = max - min || 1;
    const points = prices.map((p, i) => ({
        x: (i / (prices.length - 1)) * CHART_W,
        y: CHART_PAD + (1 - (p - min) / range) * (CHART_H - CHART_PAD * 2),
    }));
    let line = `M${points[0].x},${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
        const p0 = points[i - 1] || points[i];
        const p1 = points[i];
        const p2 = points[i + 1];
        const p3 = points[i + 2] || p2;
        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;
        line += ` C${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`;
    }
    const area = `${line} L${CHART_W},${CHART_H} L0,${CHART_H} Z`;
    return { line, area, last: points[points.length - 1] };
}

// ==========================================
// 4. DATA
// ==========================================
const MOCK_PRICES = {
    '1W': [2800, 2790, 2810, 2825, 2840, 2835, 2847.50],
    '1M': [2750, 2730, 2760, 2780, 2775, 2810, 2800, 2820, 2835, 2847.50],
    '6M': [2652, 2638, 2694, 2705, 2734, 2696, 2648, 2748, 2709, 2771, 2733, 2789, 2826, 2847.50],
    '1Y': [2400, 2450, 2380, 2500, 2550, 2600, 2580, 2650, 2700, 2680, 2750, 2847.50],
} as const;

const BRONZE_DATA = [
    { label: 'Market Cap', value: '₹19.3T' },
    { label: 'P/E Ratio',  value: '28.4'   },
    { label: 'Div Yield',  value: '0.35%'  },
    { label: '52W High',   value: '₹3,024' },
    { label: '52W Low',    value: '₹2,220' },
    { label: 'Beta',       value: '1.12'   },
];

const VERDICT_DATA = {
    verdict: 'STRONG BUY',
    score: 8.4,
    reason:
        'Cleared all hard-gates. Showing immense Institutional Volume expansion and Sector Relative Strength. Ready for entry within the calculated ATR zone.',
    gates: [
        { name: 'Circuit Limits',       status: 'PASS' },
        { name: 'Institutional Volume', status: 'PASS' },
        { name: 'Trend (20 DMA)',        status: 'PASS' },
        { name: 'Momentum (RSI)',        status: 'PASS' },
    ],
    setup: {
        entry_low: 2835.50, entry_high: 2855.00,
        stop_loss: 2750.00,
        target_1: 2950.00, target_2: 3100.00,
        rr_ratio: 2.8,
    },
};

const getTime = () => new Date().toLocaleTimeString('en-US', { hour12: false });

// ==========================================
// 5. MAIN WORKSPACE
// ==========================================
export default function Workspace() {
    const navigate = useNavigate();
    const [timeframe, setTimeframe] = useState<'1W' | '1M' | '6M' | '1Y'>('6M');
    const [watchlist, setWatchlist] = useState<string[]>(['HDFCBANK.NS', 'TCS.NS', 'INFY.NS']);
    const [searchQuery, setSearchQuery] = useState('');

    const [command, setCommand] = useState('');
    const [log, setLog] = useState<{ role: 'sys' | 'user' | 'ai'; text: string; time: string }[]>([
        { role: 'sys', text: 'INVR QUANTITATIVE ENGINE ONLINE. KERNEL V4.2.0', time: getTime() },
        { role: 'sys', text: 'LOADED: RELIANCE.NS [NSE]', time: getTime() },
        { role: 'ai',  text: 'Valuation and momentum matrices verified. Awaiting deployment parameters.', time: getTime() },
    ]);
    const [isProcessing, setIsProcessing] = useState(false);
    const logEndRef = useRef<HTMLDivElement>(null);

    const chartData = buildPriceChart(MOCK_PRICES[timeframe]);
    const isWatched = watchlist.includes('RELIANCE.NS');

    const handleCommand = (e: React.FormEvent) => {
        e.preventDefault();
        if (!command.trim()) return;
        const cmd = command;
        setCommand('');
        setLog(prev => [...prev, { role: 'user', text: cmd, time: getTime() }]);
        setIsProcessing(true);
        setTimeout(() => {
            setLog(prev => [...prev, { role: 'sys', text: 'FETCHING BRONZE LAYER TELEMETRY... [OK]', time: getTime() }]);
        }, 600);
        setTimeout(() => {
            setLog(prev => [...prev, { role: 'sys', text: 'EVALUATING GOLD LAYER HARD-GATES...', time: getTime() }]);
        }, 1200);
        setTimeout(() => {
            setIsProcessing(false);
            setLog(prev => [
                ...prev,
                {
                    role: 'ai',
                    text: 'Analysis complete. The requested metric (P/E 28.4) is currently 14% below its 5-year historical median, validating the STRONG BUY setup. Risk parameters remain locked.',
                    time: getTime(),
                },
            ]);
            logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 2200);
    };

    return (
        <div className="relative w-full h-screen bg-[#030508] text-white overflow-hidden font-sans tracking-tighter font-bold flex flex-col p-4 md:p-6 gap-4">
            <style>{`
                .no-scrollbar::-webkit-scrollbar { display: none; }
                .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
            `}</style>

            {/* ── FIXED BACKGROUND STACK (§7 — three layers) ── */}
            {/* Layer 1: Static grid */}
            <div className="fixed inset-0 z-0 bg-grid pointer-events-none opacity-50" />
            {/* Layer 2: Three.js starfield, mix-blend-screen */}
            <div className="fixed inset-0 z-0 mix-blend-screen pointer-events-none">
                <Canvas camera={{ position: [0, 0, 5] }}>
                    <DataPoints />
                </Canvas>
            </div>
            {/* Blob A: top-right, emerald, 800×800px */}
            <motion.div
                className="fixed top-[-10%] right-[-5%] w-[800px] h-[800px] bg-emerald-500/10 blur-[150px] pointer-events-none"
                initial={{ borderRadius: '50%' }}
                animate={{
                    x: [0, 40, -25, 0], y: [0, -30, 20, 0], scale: [1, 1.15, 0.94, 1],
                    borderRadius: ['50%', '42% 58% 60% 40% / 50% 45% 55% 50%', '58% 42% 40% 60% / 45% 55% 45% 55%', '50%'],
                }}
                transition={{ duration: 24, repeat: Infinity, ease: 'easeInOut' }}
            />
            {/* Blob B: bottom-left, teal, 600×600px */}
            <motion.div
                className="fixed bottom-[-10%] left-[-5%] w-[600px] h-[600px] bg-teal-500/10 blur-[150px] pointer-events-none"
                initial={{ borderRadius: '50%' }}
                animate={{
                    x: [0, -30, 30, 0], y: [0, 25, -25, 0], scale: [1, 0.9, 1.12, 1],
                    borderRadius: ['50%', '60% 40% 38% 62% / 55% 45% 55% 45%', '40% 60% 62% 38% / 45% 55% 45% 55%', '50%'],
                }}
                transition={{ duration: 28, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
            />

            {/* ── TOP NAVIGATION — §8: logo left, CTA right, scrim z-40, nav z-50 ── */}
            {/* Scrim — fades in on scroll; always visible here since it's an app shell */}
            <div
                className="fixed top-0 inset-x-0 h-20 z-40 pointer-events-none"
                style={{
                    backdropFilter: 'blur(20px)',
                    WebkitBackdropFilter: 'blur(20px)',
                    background: 'linear-gradient(180deg, rgba(3,5,8,0.80) 0%, rgba(3,5,8,0) 100%)',
                }}
            />
            <nav className="relative z-50 w-full px-2 flex items-center justify-between shrink-0 h-14">
                {/* Logo — §8 exact: INVR + emerald dot */}
                <div
                    onClick={() => navigate('/')}
                    className="font-bold text-2xl tracking-tighter text-white flex items-center cursor-pointer select-none"
                >
                    INVR<span className="text-emerald-500">.</span>
                </div>

                {/* Search Explorer — glass.nested per §4 */}
                <div className="flex-1 max-w-2xl mx-8 relative group">
                    <div
                        className="absolute inset-0 rounded-[1rem] transition-colors duration-300 group-focus-within:bg-white/[0.04]"
                        style={glass.nested}
                    />
                    <div className="relative flex items-center px-4 py-3 z-10">
                        <Search className="w-4 h-4 text-white/40 mr-3 group-focus-within:text-emerald-400 transition-colors" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Query ticker, sector, or institutional flow..."
                            className="w-full bg-transparent border-none outline-none text-sm font-bold tracking-tighter text-white placeholder-white/30"
                        />
                        <div className="hidden md:flex px-2 py-1 rounded-[0.5rem] border border-white/10 text-[9px] font-bold tracking-[0.15em] text-white/40 uppercase bg-white/5">
                            CTRL K
                        </div>
                    </div>
                </div>

                {/* Live status badge — §9 status/live badge recipe */}
                <div className="hidden lg:flex items-center gap-2 px-4 py-2 rounded-full" style={glass.pill}>
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                    <span className="text-[11px] font-bold tracking-tighter text-emerald-400 uppercase">Live</span>
                    <span className="text-[10px] font-bold tracking-[0.12em] text-white/40 uppercase">ID: 0x9A8F</span>
                </div>
            </nav>

            {/* ── MAIN WORKSPACE (3 panes) ── */}
            <div className="flex-1 flex gap-4 min-h-0 relative z-10 w-full">

                {/* ═══════════════════════════════════════
                    PANE 1: ACTIVE LEDGER (left sidebar)
                ═══════════════════════════════════════ */}
                <div className="hidden lg:flex w-[260px] flex-col rounded-[2.5rem] overflow-hidden shrink-0" style={glass.base}>

                    {/* §4.2 — Mandatory: this glass.base pane has nested children (the ledger items) ✓ */}
                    <div className="p-6 border-b border-white/10 shrink-0">
                        {/* Eyebrow — no icon, typographic label only per §1 */}
                        <p className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40">Active Ledger</p>
                    </div>

                    <div className="flex-1 overflow-y-auto no-scrollbar p-4 flex flex-col gap-3">

                        {/* Active item — §4.2 uses glass.pill accent, no icon-in-box */}
                        <motion.div
                            className="p-4 rounded-[1.25rem] flex justify-between items-center cursor-pointer relative overflow-hidden"
                            style={{
                                border: '1px solid rgba(16,185,129,0.35)',
                                background: 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(13,148,136,0.04) 100%)',
                                boxShadow: '0 0 20px rgba(16,185,129,0.12), inset 0 1px 0 rgba(255,255,255,0.18)',
                            }}
                            whileHover={{ scale: 1.01 }}
                            transition={springSoft}
                        >
                            <div>
                                <h4 className="text-lg font-bold tracking-tighter text-white">RELIANCE</h4>
                                {/* §9 score/metric badge — glass.nested inside the active item */}
                                <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-1 rounded-[0.875rem]" style={glass.nested}>
                                    <span className="text-[10px] font-bold tracking-[0.15em] text-emerald-400 uppercase tabular-nums">
                                        Score 7.8
                                    </span>
                                </div>
                            </div>
                            {/* Idle ambient: pulsing emerald dot instead of icon per §6.2 */}
                            <motion.div
                                className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"
                                animate={{ scale: [1, 1.4, 1], opacity: [1, 0.6, 1] }}
                                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                            />
                        </motion.div>

                        {/* Inactive ledger items */}
                        {watchlist.filter(t => t !== 'RELIANCE.NS').map(ticker => (
                            <motion.div
                                key={ticker}
                                className="p-4 rounded-[1.25rem] flex justify-between items-center cursor-pointer group"
                                style={glass.nested}
                                whileHover={{ scale: 1.01 }}
                                transition={springSoft}
                            >
                                <div>
                                    <h4 className="text-lg font-bold tracking-tighter text-white/50 group-hover:text-white transition-colors">
                                        {ticker.split('.')[0]}
                                    </h4>
                                    <span className="text-[9px] font-bold tracking-[0.15em] uppercase text-white/25">NSE</span>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* ═══════════════════════════════════════
                    PANE 2: EXPLORER (center, scrollable)
                ═══════════════════════════════════════ */}
                <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col gap-4">

                    {/* TOP: Primary Chart Card — glass.base with three nested tiers inside */}
                    <div className="rounded-[2.5rem] p-8 flex flex-col gap-6 shrink-0 relative overflow-hidden" style={glass.base}>

                        {/* Header — §8 asymmetric layout */}
                        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 relative z-10">
                            <div>
                                <div className="flex items-center gap-4 mb-2">
                                    {/* §6.2 idle float on ticker headline */}
                                    <motion.h1
                                        className="text-5xl md:text-[4rem] font-bold tracking-tighter text-white leading-none"
                                        animate={{ y: [0, -3, 0] }}
                                        transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
                                    >
                                        RELIANCE
                                    </motion.h1>
                                    {/* Watch button — glass.pill secondary button per §9 */}
                                    <motion.button
                                        onClick={() =>
                                            isWatched
                                                ? setWatchlist(watchlist.filter(t => t !== 'RELIANCE.NS'))
                                                : setWatchlist([...watchlist, 'RELIANCE.NS'])
                                        }
                                        whileHover={{ scale: 1.03 }}
                                        whileTap={{ scale: 0.97 }}
                                        transition={springPress}
                                        className="p-2.5 rounded-[1rem]"
                                        style={glass.pill}
                                    >
                                        {isWatched
                                            ? <BookmarkCheck className="w-5 h-5 text-emerald-400" />
                                            : <Plus className="w-5 h-5 text-white/60" />
                                        }
                                    </motion.button>
                                </div>
                                <p className="text-white/50 font-bold tracking-tighter text-lg">
                                    Reliance Industries Ltd • NSE
                                </p>
                            </div>

                            <div className="flex flex-col md:items-end">
                                {/* §9 score/metric badge — glass.nested for price */}
                                <div className="inline-flex flex-col items-end gap-1">
                                    <span className="text-4xl md:text-5xl font-bold tracking-tighter tabular-nums text-white">
                                        ₹2,847.50
                                    </span>
                                    <span className="text-sm font-bold tracking-tighter text-emerald-400">
                                        +₹65.20 (+2.34%)
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Chart panel — glass.nested per §9 data chart panel recipe */}
                        <div className="rounded-[1.5rem] p-6 relative" style={glass.nested}>
                            {/* Header row: label left, value right — §9 chart panel recipe */}
                            <div className="flex justify-between items-center mb-6">
                                <div className="flex gap-1 p-1 rounded-[1.25rem]" style={glass.pill}>
                                    {(['1W', '1M', '6M', '1Y'] as const).map((tf) => (
                                        <button
                                            key={tf}
                                            onClick={() => setTimeframe(tf)}
                                            className={`relative px-5 py-2 text-[11px] font-bold tracking-[0.15em] uppercase transition-colors rounded-[1rem] z-10 ${
                                                timeframe === tf ? 'text-white' : 'text-white/40 hover:text-white/80'
                                            }`}
                                        >
                                            {timeframe === tf && (
                                                <motion.div
                                                    layoutId="tf-pill"
                                                    className="absolute inset-0 rounded-[1rem] bg-white/[0.08]"
                                                    style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.18)' }}
                                                    transition={springSoft}
                                                />
                                            )}
                                            <span className="relative z-10">{tf}</span>
                                        </button>
                                    ))}
                                </div>
                                <span className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40 hidden md:block">
                                    Price Action
                                </span>
                            </div>

                            {/* Chart — built from real data through Catmull-Rom per §7 */}
                            <div className="h-[200px] w-full relative">
                                <AnimatePresence mode="wait">
                                    <motion.svg
                                        key={timeframe}
                                        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
                                        className="w-full h-full overflow-visible"
                                        preserveAspectRatio="none"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.3 }}
                                    >
                                        <defs>
                                            <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                                                <stop offset="0%" stopColor="#0D9488" />
                                                <stop offset="100%" stopColor="#10B981" />
                                            </linearGradient>
                                            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                                                {/* §7: top ~0.20, bottom 0 */}
                                                <stop offset="0%" stopColor="#10B981" stopOpacity="0.20" />
                                                <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
                                            </linearGradient>
                                        </defs>

                                        {/* §7: 2–3 ultra-faint reference lines, not a data grid */}
                                        {[0.25, 0.5, 0.75].map((f) => (
                                            <line
                                                key={f}
                                                x1="0" x2={CHART_W}
                                                y1={CHART_H * f} y2={CHART_H * f}
                                                stroke="rgba(255,255,255,0.05)" strokeWidth="1"
                                            />
                                        ))}

                                        <motion.path
                                            d={chartData.area} fill="url(#areaGrad)"
                                            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                            transition={{ duration: 0.8, delay: 0.3 }}
                                        />
                                        <motion.path
                                            d={chartData.line} fill="none"
                                            stroke="url(#lineGrad)" strokeWidth="2.5" strokeLinecap="round"
                                            initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
                                            transition={{ duration: 1.5, ease: 'easeInOut' }}
                                            className="drop-shadow-[0_4px_12px_rgba(16,185,129,0.3)]"
                                        />
                                    </motion.svg>
                                </AnimatePresence>

                                {/* Live marker — positioned from actual last data coordinate per §7 */}
                                <motion.div
                                    style={{
                                        left: `${(chartData.last.x / CHART_W) * 100}%`,
                                        top:  `${(chartData.last.y / CHART_H) * 100}%`,
                                    }}
                                    className="absolute -translate-y-1/2 -translate-x-1/2"
                                >
                                    <div className="relative flex items-center justify-center">
                                        <motion.div
                                            animate={{ scale: [1, 2.5, 1], opacity: [0.8, 0, 0.8] }}
                                            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                                            className="absolute w-4 h-4 rounded-full bg-emerald-400 blur-[2px]"
                                        />
                                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 relative z-10 shadow-[0_0_10px_rgba(16,185,129,1)]" />
                                    </div>
                                </motion.div>
                            </div>

                            {/* Axis tick labels per §9 chart panel recipe */}
                            <div className="flex justify-between mt-3">
                                {(['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'] as const).map((m) => (
                                    <span key={m} className="text-[9px] font-bold tracking-[0.1em] text-white/25 uppercase">
                                        {m}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* BOTTOM: Data matrices row */}
                    <div className="grid grid-cols-1 xl:grid-cols-5 gap-4 shrink-0 pb-4">

                        {/* GOLD VERDICT CARD (3 cols) — glass.base with two nested children ✓ §4.2 */}
                        <div className="xl:col-span-3 rounded-[2.5rem] p-8 flex flex-col relative overflow-hidden" style={glass.base}>

                            {/* Left accent stripe — purposeful structural element (verdict severity indicator) */}
                            <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-gradient-to-b from-emerald-400 to-teal-500 shadow-[0_0_20px_rgba(16,185,129,0.5)]" />

                            {/* §9 narrative card structure — eyebrow → headline → body, no icon in box */}
                            <div className="ml-5">
                                {/* Eyebrow — typographic, no icon per §1 */}
                                <p className="text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400 mb-1.5">
                                    Gold Layer · System Verdict
                                </p>

                                {/* Headline with score badge (glass.nested) alongside */}
                                <div className="flex items-center gap-4 mb-4">
                                    <h3 className="text-2xl font-bold tracking-tighter text-white">
                                        {VERDICT_DATA.verdict}
                                    </h3>
                                    {/* §9 score/metric badge */}
                                    <div
                                        className="flex flex-col items-center justify-center px-4 py-2 rounded-[1.25rem]"
                                        style={glass.nested}
                                    >
                                        <span className="font-bold tracking-tighter text-xl text-white tabular-nums leading-none">
                                            {VERDICT_DATA.score}
                                        </span>
                                        <span className="text-[9px] font-bold tracking-[0.15em] text-emerald-400 uppercase mt-1">
                                            Score
                                        </span>
                                    </div>
                                </div>

                                {/* Body — §5: text-white/55, font-bold, tracking-tighter */}
                                <p className="text-white/55 font-bold tracking-tighter text-base leading-relaxed mb-6 max-w-xl">
                                    {VERDICT_DATA.reason}
                                </p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {/* Gates list */}
                                    <div className="flex flex-col gap-3">
                                        <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40 mb-1">
                                            Hard Gates Cleared
                                        </h4>
                                        {VERDICT_DATA.gates.map((g, i) => (
                                            <div key={i} className="flex justify-between items-center py-2 border-b border-white/5">
                                                <span className="text-sm font-bold tracking-tighter text-white/70">{g.name}</span>
                                                <span className="text-[10px] font-bold tracking-[0.15em] text-emerald-400 uppercase">{g.status}</span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Trade setup — §9 verdict/insight panel with gradient top divider */}
                                    <div className="rounded-[1.5rem] p-5 relative overflow-hidden" style={glass.nested}>
                                        <div className="absolute top-0 left-6 right-6 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
                                        <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400 mb-3 mt-1">
                                            Trade Architecture
                                        </h4>
                                        {[
                                            { label: 'Entry Zone',  val: `₹${VERDICT_DATA.setup.entry_low} – ${VERDICT_DATA.setup.entry_high}`, cls: 'text-white' },
                                            { label: 'Stop Loss',   val: `₹${VERDICT_DATA.setup.stop_loss}`, cls: 'text-red-400' },
                                            { label: 'Targets',     val: `₹${VERDICT_DATA.setup.target_1} / ${VERDICT_DATA.setup.target_2}`, cls: 'text-emerald-400' },
                                            { label: 'R/R Ratio',   val: `${VERDICT_DATA.setup.rr_ratio}×`, cls: 'text-white/70' },
                                        ].map(({ label, val, cls }) => (
                                            <div key={label} className="flex justify-between items-center py-1.5">
                                                <span className="text-sm font-bold tracking-tighter text-white/55">{label}</span>
                                                <span className={`text-sm font-bold tracking-tighter tabular-nums ${cls}`}>{val}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* BRONZE DATA GRID (2 cols) — glass.base with nested metric items ✓ §4.2 */}
                        <div className="xl:col-span-2 rounded-[2.5rem] p-8 flex flex-col" style={glass.base}>
                            {/* §1: no icon-in-box header — typographic eyebrow only */}
                            <div className="mb-5 border-b border-white/10 pb-4">
                                <p className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40">
                                    Bronze Layer · Raw Ingestion
                                </p>
                            </div>
                            <div className="grid grid-cols-2 gap-3 flex-1 content-start">
                                {BRONZE_DATA.map((data, i) => (
                                    <div key={i} className="flex flex-col p-4 rounded-[1.25rem]" style={glass.nested}>
                                        <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/40 mb-1">
                                            {data.label}
                                        </span>
                                        <span className="text-xl font-bold tracking-tighter tabular-nums text-white">
                                            {data.value}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* ═══════════════════════════════════════
                    PANE 3: EXECUTION LOG (right)
                ═══════════════════════════════════════ */}
                <div className="w-[400px] rounded-[2.5rem] flex flex-col shrink-0 relative overflow-hidden" style={glass.base}>

                    {/* Terminal header — §1: no icon-in-box; typographic + status badge */}
                    <div className="p-6 border-b border-white/10 flex justify-between items-center shrink-0">
                        <div>
                            {/* Eyebrow eyebrow pattern — wide-tracked micro-caption */}
                            <p className="text-[10px] font-bold tracking-[0.18em] uppercase text-emerald-400 mb-1">
                                Execution Log
                            </p>
                            <h3 className="text-base font-bold tracking-tighter text-white">
                                Quant Copilot
                            </h3>
                        </div>
                        {/* §9 status/live badge — pulsing dot + label */}
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={glass.nested}>
                            <motion.div
                                className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"
                                animate={{ opacity: [1, 0.3, 1] }}
                                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                            />
                            <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/50">
                                {isProcessing ? 'Processing' : 'Ready'}
                            </span>
                        </div>
                    </div>

                    {/* Log output */}
                    <div className="flex-1 p-6 overflow-y-auto no-scrollbar flex flex-col gap-4 text-xs font-mono tracking-tight bg-[#010204]/60">
                        <AnimatePresence>
                            {log.map((msg, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 8 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={springSoft}
                                    className="flex flex-col gap-1.5 border-l-2 border-white/10 pl-3"
                                >
                                    <div className="flex items-center gap-2 text-[10px] font-bold tracking-widest uppercase">
                                        <span className={
                                            msg.role === 'user' ? 'text-white/30'
                                            : msg.role === 'sys' ? 'text-teal-400'
                                            : 'text-emerald-400'
                                        }>
                                            {msg.role === 'user' ? '> USER_INPUT' : msg.role === 'sys' ? '[SYS_INIT]' : '>> QUANT_OUTPUT'}
                                        </span>
                                        <span className="text-white/20">{msg.time}</span>
                                    </div>
                                    <span className={`leading-relaxed ${msg.role === 'user' ? 'text-white/60' : 'text-white'}`}>
                                        {msg.text}
                                    </span>
                                </motion.div>
                            ))}
                        </AnimatePresence>

                        {isProcessing && (
                            <div className="flex items-center gap-3 text-emerald-400/50 pl-3">
                                <motion.div
                                    className="w-1.5 h-3 bg-emerald-500"
                                    animate={{ opacity: [1, 0.2, 1] }}
                                    transition={{ duration: 0.8, repeat: Infinity }}
                                />
                                <span>Running vectorized math...</span>
                            </div>
                        )}
                        <div ref={logEndRef} />
                    </div>

                    {/* Command input — glass.nested form per §4 */}
                    <div className="p-4 border-t border-white/10 shrink-0 bg-black/40">
                        <form onSubmit={handleCommand} className="relative flex items-center rounded-[1.25rem] p-1" style={glass.nested}>
                            <CornerDownRight className="absolute left-4 w-4 h-4 text-white/30" />
                            <input
                                type="text"
                                value={command}
                                onChange={(e) => setCommand(e.target.value)}
                                placeholder="Enter query parameters..."
                                className="w-full bg-transparent border-none py-4 pl-12 pr-4 outline-none text-sm font-mono text-white placeholder-white/30"
                            />
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}