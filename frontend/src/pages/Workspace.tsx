import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence, useScroll, useTransform, useSpring } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { Search, Plus, BookmarkCheck, Terminal, Activity, ShieldCheck, Database, CornerDownRight, ChevronRight, AlertTriangle } from 'lucide-react';

// ==========================================
// 1. EXACT LIQUID GLASS SYSTEM (From Landing.tsx)
// ==========================================
const glass = {
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

    nested: {
        background: 'linear-gradient(145deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.01) 100%)',
        border: '1px solid rgba(255,255,255,0.085)',
        boxShadow: [
            'inset 0 1px 0 rgba(255,255,255,0.20)',
            'inset 1px 0 0 rgba(255,255,255,0.06)',
            '0 8px 32px rgba(0,0,0,0.22)',
        ].join(', '),
    } as React.CSSProperties,

    pill: {
        background: 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)',
        border: '1px solid rgba(255,255,255,0.10)',
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.20), 0 4px 12px rgba(0,0,0,0.15)',
    } as React.CSSProperties,
};

const springSoft = { type: 'spring', stiffness: 220, damping: 28, mass: 0.9 } as const;
const springPress = { type: 'spring', stiffness: 420, damping: 26, mass: 0.6 } as const;

// ==========================================
// 2. THREE.JS & CHART UTILS
// ==========================================
function DataPoints() {
    const pointsRef = useRef<any>();
    const count = 2500;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 35;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }
    useFrame((state) => {
        if (pointsRef.current) {
            pointsRef.current.rotation.y = state.clock.elapsedTime * 0.04;
            pointsRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.08) * 0.1;
        }
    });
    return (
        <points ref={pointsRef}>
            <bufferGeometry><bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} /></bufferGeometry>
            <pointsMaterial size={0.045} color="#10B981" transparent opacity={0.6} sizeAttenuation />
        </points>
    );
}

function buildPriceChart(prices: number[]) {
    const CHART_W = 600; const CHART_H = 160; const CHART_PAD = 10;
    const min = Math.min(...prices); const max = Math.max(...prices);
    const range = max - min || 1;
    const points = prices.map((p, i) => ({
        x: (i / (prices.length - 1)) * CHART_W,
        y: CHART_PAD + (1 - (p - min) / range) * (CHART_H - CHART_PAD * 2),
    }));

    let line = `M${points[0].x},${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
        const p0 = points[i - 1] || points[i]; const p1 = points[i];
        const p2 = points[i + 1]; const p3 = points[i + 2] || p2;
        const cp1x = p1.x + (p2.x - p0.x) / 6; const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6; const cp2y = p2.y - (p3.y - p1.y) / 6;
        line += ` C${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`;
    }
    const area = `${line} L${CHART_W},${CHART_H} L0,${CHART_H} Z`;
    return { line, area, last: points[points.length - 1] };
}

// ==========================================
// 3. BACKEND DATA SCHEMAS
// ==========================================
const MOCK_PRICES = {
    '1W': [2800, 2790, 2810, 2825, 2840, 2835, 2847.50],
    '1M': [2750, 2730, 2760, 2780, 2775, 2810, 2800, 2820, 2835, 2847.50],
    '6M': [2652, 2638, 2694, 2705, 2734, 2696, 2648, 2748, 2709, 2771, 2733, 2789, 2826, 2847.50],
    '1Y': [2400, 2450, 2380, 2500, 2550, 2600, 2580, 2650, 2700, 2680, 2750, 2847.50],
};

const BRONZE_DATA = [
    { label: "Market Cap", value: "19.3T" },
    { label: "P/E Ratio", value: "28.4" },
    { label: "Div Yield", value: "0.35%" },
    { label: "52W High", value: "₹3,024" },
    { label: "52W Low", value: "₹2,220" },
    { label: "Beta", value: "1.12" },
];

const VERDICT_DATA = {
    verdict: "STRONG BUY",
    score: 8.4,
    reason: "Cleared all hard-gates. Showing immense Institutional Volume expansion and Sector Relative Strength. Ready for entry within the calculated ATR zone.",
    gates: [
        { name: "Circuit Limits", status: "PASS" },
        { name: "Institutional Volume", status: "PASS" },
        { name: "Trend (20 DMA)", status: "PASS" },
        { name: "Momentum (RSI)", status: "PASS" },
    ],
    setup: {
        entry_low: 2835.50, entry_high: 2855.00,
        stop_loss: 2750.00,
        target_1: 2950.00, target_2: 3100.00,
        rr_ratio: 2.8
    }
};

const getTime = () => new Date().toLocaleTimeString('en-US', { hour12: false });

// ==========================================
// 4. MAIN WORKSPACE
// ==========================================
export default function Workspace() {
    const navigate = useNavigate();
    const [timeframe, setTimeframe] = useState<'1W' | '1M' | '6M' | '1Y'>('6M');
    const [watchlist, setWatchlist] = useState<string[]>(['HDFCBANK.NS', 'TCS.NS', 'INFY.NS']);
    const [searchQuery, setSearchQuery] = useState('');

    // Terminal State
    const [command, setCommand] = useState('');
    const [log, setLog] = useState<{ role: 'sys' | 'user' | 'ai', text: string, time: string }[]>([
        { role: 'sys', text: 'INVR QUANTITATIVE ENGINE ONLINE. KERNEL V4.2.0', time: getTime() },
        { role: 'sys', text: 'LOADED: RELIANCE.NS [NSE]', time: getTime() },
        { role: 'ai', text: 'Valuation and momentum matrices verified. Awaiting deployment parameters.', time: getTime() }
    ]);
    const [isProcessing, setIsProcessing] = useState(false);
    const logEndRef = useRef<HTMLDivElement>(null);

    const chartData = buildPriceChart(MOCK_PRICES[timeframe]);
    const isWatched = watchlist.includes('RELIANCE.NS');

    const handleCommand = (e: React.FormEvent) => {
        e.preventDefault();
        if (!command.trim()) return;

        const newCmd = command;
        setCommand('');
        setLog(prev => [...prev, { role: 'user', text: newCmd, time: getTime() }]);
        setIsProcessing(true);

        // Simulate engine streaming output
        setTimeout(() => {
            setLog(prev => [...prev, { role: 'sys', text: 'FETCHING BRONZE LAYER TELEMETRY... [OK]', time: getTime() }]);
        }, 600);

        setTimeout(() => {
            setLog(prev => [...prev, { role: 'sys', text: 'EVALUATING GOLD LAYER HARD-GATES...', time: getTime() }]);
        }, 1200);

        setTimeout(() => {
            setIsProcessing(false);
            setLog(prev => [...prev, {
                role: 'ai',
                text: 'Analysis complete. The requested metric (P/E 28.4) is currently 14% below its 5-year historical median, validating the STRONG BUY setup. Risk parameters remain locked.',
                time: getTime()
            }]);
            logEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 2200);
    };

    return (
        <div className="relative w-full h-screen bg-[#030508] text-white overflow-hidden font-sans flex flex-col p-4 md:p-6 gap-6">
            {/* OBLITERATE SCROLLBARS */}
            <style>{`
                .no-scrollbar::-webkit-scrollbar { display: none; }
                .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
            `}</style>

            {/* FIXED BACKGROUNDS (Strict adherence) */}
            <div className="fixed inset-0 z-0 bg-grid pointer-events-none opacity-50" />
            <div className="fixed inset-0 z-0 mix-blend-screen pointer-events-none">
                <Canvas camera={{ position: [0, 0, 5] }}><DataPoints /></Canvas>
            </div>
            <motion.div
                className="fixed top-[-10%] right-[-5%] w-[800px] h-[800px] bg-emerald-500/10 blur-[150px] pointer-events-none"
                initial={{ borderRadius: '50%' }}
                animate={{
                    x: [0, 40, -25, 0], y: [0, -30, 20, 0], scale: [1, 1.15, 0.94, 1],
                    borderRadius: ['50%', '42% 58% 60% 40% / 50% 45% 55% 50%', '58% 42% 40% 60% / 45% 55% 45% 55%', '50%'],
                }}
                transition={{ duration: 24, repeat: Infinity, ease: 'easeInOut' }}
            />
            <motion.div
                className="fixed bottom-[-10%] left-[-5%] w-[600px] h-[600px] bg-teal-500/10 blur-[150px] pointer-events-none"
                initial={{ borderRadius: '50%' }}
                animate={{
                    x: [0, -30, 30, 0], y: [0, 25, -25, 0], scale: [1, 0.9, 1.12, 1],
                    borderRadius: ['50%', '60% 40% 38% 62% / 55% 45% 55% 45%', '40% 60% 62% 38% / 45% 55% 45% 55%', '50%'],
                }}
                transition={{ duration: 28, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
            />

            {/* =========================================
                TOP NAVIGATION BAR
            ============================================= */}
            <nav className="relative z-50 w-full rounded-[1.5rem] px-6 py-4 flex items-center justify-between shrink-0" style={glass.base}>
                <div onClick={() => navigate('/')} className="font-bold text-2xl tracking-tighter text-white flex items-center gap-2 cursor-pointer">
                    INVR<span className="text-emerald-500">.</span>
                </div>

                {/* Search Explorer */}
                <div className="flex-1 max-w-2xl mx-8 relative group">
                    <div className="absolute inset-0 rounded-[1rem] transition-colors duration-300 group-focus-within:bg-white/[0.04]" style={glass.nested} />
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

                <div className="hidden lg:flex items-center gap-4 text-[10px] font-bold tracking-[0.15em] uppercase text-white/50">
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                        <span className="text-emerald-400">Live</span>
                    </div>
                    <span>ID: 0x9A8F</span>
                </div>
            </nav>

            {/* =========================================
                MAIN WORKSPACE (3 PANES)
            ============================================= */}
            <div className="flex-1 flex gap-6 min-h-0 relative z-10 w-full">

                {/* PANE 1: LEDGER */}
                <div className="hidden lg:flex w-[280px] flex-col rounded-[2.5rem] overflow-hidden shrink-0" style={glass.base}>
                    <div className="p-6 border-b border-white/10">
                        <h2 className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40">Active Ledger</h2>
                    </div>
                    <div className="flex-1 overflow-y-auto no-scrollbar p-4 flex flex-col gap-3">
                        {/* Active Item */}
                        <div className="p-4 rounded-[1.25rem] flex justify-between items-center cursor-pointer border border-emerald-500/40 shadow-[0_0_20px_rgba(16,185,129,0.15),inset_0_1px_1px_rgba(255,255,255,0.2)] bg-gradient-to-br from-emerald-500/10 to-transparent">
                            <div>
                                <h4 className="text-lg font-bold tracking-tighter text-white">RELIANCE</h4>
                                <span className="text-[9px] font-bold tracking-[0.15em] uppercase text-emerald-400">Score 7.8</span>
                            </div>
                            <Activity className="w-4 h-4 text-emerald-500" />
                        </div>
                        {/* Inactive Items */}
                        {watchlist.filter(t => t !== 'RELIANCE.NS').map(ticker => (
                            <div key={ticker} className="p-4 rounded-[1.25rem] hover:bg-white/[0.04] transition-colors flex justify-between items-center cursor-pointer group" style={glass.nested}>
                                <div>
                                    <h4 className="text-lg font-bold tracking-tighter text-white/60 group-hover:text-white transition-colors">{ticker.split('.')[0]}</h4>
                                    <span className="text-[9px] font-bold tracking-[0.15em] uppercase text-white/30">NSE</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* PANE 2: THE EXPLORER (Center Stage) */}
                <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col gap-6">

                    {/* TOP: Primary Chart Card */}
                    <div className="rounded-[2.5rem] p-8 flex flex-col gap-8 shrink-0 relative overflow-hidden" style={glass.base}>
                        {/* Header Data */}
                        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 relative z-10">
                            <div>
                                <div className="flex items-center gap-4 mb-2">
                                    <h1 className="text-5xl md:text-[4rem] font-bold tracking-tighter text-white leading-none">RELIANCE</h1>
                                    <button
                                        onClick={() => isWatched ? setWatchlist(watchlist.filter(t => t !== 'RELIANCE.NS')) : setWatchlist([...watchlist, 'RELIANCE.NS'])}
                                        className="p-2.5 rounded-[1rem] hover:bg-white/10 transition-colors"
                                        style={glass.pill}
                                    >
                                        {isWatched ? <BookmarkCheck className="w-5 h-5 text-emerald-400" /> : <Plus className="w-5 h-5 text-white/60" />}
                                    </button>
                                </div>
                                <p className="text-white/50 font-bold tracking-tighter text-lg">Reliance Industries Ltd • NSE</p>
                            </div>
                            <div className="flex flex-col md:items-end">
                                <h2 className="text-4xl md:text-5xl font-bold tracking-tighter tabular-nums text-white">₹2,847.50</h2>
                                <span className="text-sm font-bold tracking-tighter text-emerald-400 mt-1">+₹65.20 (+2.34%)</span>
                            </div>
                        </div>

                        {/* Interactive Chart Area */}
                        <div className="rounded-[1.5rem] p-6 relative" style={glass.nested}>
                            {/* Fluid LayoutId Pills for Timeframes */}
                            <div className="flex justify-between items-center mb-6">
                                <div className="flex gap-1 p-1 rounded-[1.25rem]" style={glass.pill}>
                                    {['1W', '1M', '6M', '1Y'].map((tf) => (
                                        <button
                                            key={tf}
                                            onClick={() => setTimeframe(tf as any)}
                                            className={`relative px-5 py-2 text-[11px] font-bold tracking-[0.15em] uppercase transition-colors rounded-[1rem] z-10 ${timeframe === tf ? 'text-white' : 'text-white/40 hover:text-white/80'}`}
                                        >
                                            {timeframe === tf && (
                                                <motion.div layoutId="tf-pill" className="absolute inset-0 rounded-[1rem] bg-white/[0.08]" style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.18)' }} transition={springSoft} />
                                            )}
                                            <span className="relative z-10">{tf}</span>
                                        </button>
                                    ))}
                                </div>
                                <span className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40 hidden md:block">Price Action</span>
                            </div>

                            <div className="h-[220px] w-full relative">
                                <svg viewBox="0 0 600 160" className="w-full h-full overflow-visible" preserveAspectRatio="none">
                                    <defs>
                                        <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                                            <stop offset="0%" stopColor="#0D9488" />
                                            <stop offset="100%" stopColor="#10B981" />
                                        </linearGradient>
                                        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#10B981" stopOpacity="0.25" />
                                            <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
                                        </linearGradient>
                                    </defs>
                                    {[0.25, 0.5, 0.75].map((f) => (
                                        <line key={f} x1="0" x2="600" y1={160 * f} y2={160 * f} stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                                    ))}
                                    <motion.path
                                        key={`area-${timeframe}`}
                                        d={chartData.area} fill="url(#areaGrad)"
                                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8 }}
                                    />
                                    <motion.path
                                        key={`line-${timeframe}`}
                                        d={chartData.line} fill="none" stroke="url(#lineGrad)" strokeWidth="2.5" strokeLinecap="round"
                                        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.5, ease: "easeInOut" }}
                                        className="drop-shadow-[0_4px_12px_rgba(16,185,129,0.3)]"
                                    />
                                </svg>
                                {/* Live Dot mapped to actual final coordinate */}
                                <motion.div
                                    style={{ left: `${(chartData.last.x / 600) * 100}%`, top: `${(chartData.last.y / 160) * 100}%` }}
                                    className="absolute -translate-y-1/2 -translate-x-1/2"
                                >
                                    <div className="relative flex items-center justify-center">
                                        <motion.div animate={{ scale: [1, 2.5, 1], opacity: [0.8, 0, 0.8] }} transition={{ duration: 2, repeat: Infinity }} className="absolute w-4 h-4 rounded-full bg-emerald-400 blur-[2px]" />
                                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 relative z-10 shadow-[0_0_10px_rgba(16,185,129,1)]" />
                                    </div>
                                </motion.div>
                            </div>
                        </div>
                    </div>

                    {/* BOTTOM: Data Matrices */}
                    <div className="grid grid-cols-1 xl:grid-cols-5 gap-6 shrink-0 pb-6">

                        {/* GOLD LAYER VERDICT (Spans 3 cols) */}
                        <div className="xl:col-span-3 rounded-[2.5rem] p-8 flex flex-col relative overflow-hidden" style={glass.base}>
                            <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-gradient-to-b from-emerald-400 to-teal-500 shadow-[0_0_20px_rgba(16,185,129,0.5)]" />

                            <div className="flex items-center gap-3 mb-4 ml-2">
                                <ShieldCheck className="w-6 h-6 text-emerald-400" />
                                <h3 className="text-2xl font-bold tracking-tighter text-white uppercase">System Verdict: <span className="text-emerald-400">{VERDICT_DATA.verdict}</span></h3>
                            </div>

                            <p className="text-white/60 font-bold tracking-tighter text-base leading-relaxed mb-8 ml-2 max-w-xl">
                                {VERDICT_DATA.reason}
                            </p>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 ml-2">
                                {/* Passed Gates */}
                                <div className="flex flex-col gap-3">
                                    <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40 mb-1">Hard Gates Cleared</h4>
                                    {VERDICT_DATA.gates.map((g, i) => (
                                        <div key={i} className="flex justify-between items-center py-2 border-b border-white/5">
                                            <span className="text-sm font-bold tracking-tighter text-white/70">{g.name}</span>
                                            <span className="text-[10px] font-bold tracking-[0.15em] text-emerald-400 uppercase">{g.status}</span>
                                        </div>
                                    ))}
                                </div>
                                {/* Trade Setup Specs */}
                                <div className="flex flex-col gap-3 rounded-[1.25rem] p-5" style={glass.nested}>
                                    <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40 mb-1">Trade Architecture</h4>
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm font-bold tracking-tighter text-white/60">Entry Zone</span>
                                        <span className="text-sm font-bold tracking-tighter tabular-nums text-white">₹{VERDICT_DATA.setup.entry_low} - {VERDICT_DATA.setup.entry_high}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm font-bold tracking-tighter text-white/60">Stop Loss</span>
                                        <span className="text-sm font-bold tracking-tighter tabular-nums text-red-400">₹{VERDICT_DATA.setup.stop_loss}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm font-bold tracking-tighter text-white/60">Targets</span>
                                        <span className="text-sm font-bold tracking-tighter tabular-nums text-emerald-400">₹{VERDICT_DATA.setup.target_1} / {VERDICT_DATA.setup.target_2}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* BRONZE LAYER DATA GRID (Spans 2 cols) */}
                        <div className="xl:col-span-2 rounded-[2.5rem] p-8 flex flex-col" style={glass.base}>
                            <div className="flex items-center gap-2 text-[11px] font-bold tracking-[0.15em] uppercase text-white/40 mb-6 border-b border-white/10 pb-4">
                                <Database className="w-4 h-4" /> Raw Ingestion Metrics
                            </div>
                            <div className="grid grid-cols-2 gap-4 flex-1 content-start">
                                {BRONZE_DATA.map((data, i) => (
                                    <div key={i} className="flex flex-col p-4 rounded-[1.25rem]" style={glass.nested}>
                                        <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/40 mb-1">{data.label}</span>
                                        <span className="text-xl font-bold tracking-tighter tabular-nums text-white">{data.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* PANE 3: EXECUTION LOG (Terminal/Copilot) */}
                <div className="w-[420px] rounded-[2.5rem] flex flex-col shrink-0 relative overflow-hidden" style={glass.base}>

                    {/* Terminal Header */}
                    <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/[0.01]">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-[1rem] flex items-center justify-center" style={glass.pill}>
                                <Terminal className="w-5 h-5 text-emerald-400" />
                            </div>
                            <div>
                                <h3 className="text-base font-bold tracking-tighter text-white">Execution Log</h3>
                                <p className="text-[9px] font-bold tracking-[0.15em] uppercase text-white/40 mt-0.5">Awaiting Parameters</p>
                            </div>
                        </div>
                        <div className="px-3 py-1.5 rounded-[0.75rem] flex items-center gap-2" style={glass.nested}>
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                        </div>
                    </div>

                    {/* Terminal Output Area (Strict Monospace) */}
                    <div className="flex-1 p-6 overflow-y-auto no-scrollbar flex flex-col gap-4 text-xs font-mono tracking-tight bg-[#010204]/60">
                        {log.map((msg, i) => (
                            <div key={i} className="flex flex-col gap-1.5 border-l-2 border-white/10 pl-3">
                                <div className="flex items-center gap-2 text-[10px] font-bold tracking-widest uppercase">
                                    <span className={msg.role === 'user' ? 'text-white/30' : msg.role === 'sys' ? 'text-teal-400' : 'text-emerald-400'}>
                                        {msg.role === 'user' ? '> USER_INPUT' : msg.role === 'sys' ? '[SYS_INIT]' : '>> QUANT_OUTPUT'}
                                    </span>
                                    <span className="text-white/20">{msg.time}</span>
                                </div>
                                <span className={`leading-relaxed ${msg.role === 'user' ? 'text-white/60' : 'text-white'}`}>
                                    {msg.text}
                                </span>
                            </div>
                        ))}
                        {isProcessing && (
                            <div className="flex items-center gap-3 text-emerald-400/50 pl-3">
                                <div className="w-1.5 h-3 bg-emerald-500 animate-pulse" />
                                <span>Running vectorized math...</span>
                            </div>
                        )}
                        <div ref={logEndRef} />
                    </div>

                    {/* Command Input Area */}
                    <div className="p-4 border-t border-white/10 relative z-10 bg-black/40">
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