import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { Search, Plus, BookmarkCheck, ArrowRight, Terminal, Activity, ShieldCheck, Database, CornerDownRight } from 'lucide-react';

// ==========================================
// 1. EXACT GLASS TOKENS (Strictly from Landing)
// ==========================================
const glass = {
    base: {
        background: 'linear-gradient(145deg, rgba(255,255,255,0.09) 0%, rgba(255,255,255,0.028) 100%)',
        backdropFilter: 'blur(72px) saturate(200%) brightness(108%)',
        WebkitBackdropFilter: 'blur(72px) saturate(200%) brightness(108%)',
        border: '1px solid rgba(255,255,255,0.13)',
        boxShadow: 'inset 0 1.5px 0 rgba(255,255,255,0.26), inset 1.5px 0 0 rgba(255,255,255,0.09), inset -1px 0 0 rgba(0,0,0,0.08), inset 0 -1.5px 0 rgba(0,0,0,0.10), 0 40px 100px rgba(0,0,0,0.52), 0 8px 20px rgba(0,0,0,0.28)',
    } as React.CSSProperties,
    nested: {
        background: 'linear-gradient(145deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.01) 100%)',
        backdropFilter: 'blur(40px) saturate(180%)',
        WebkitBackdropFilter: 'blur(40px) saturate(180%)',
        border: '1px solid rgba(255,255,255,0.085)',
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.20), inset 1px 0 0 rgba(255,255,255,0.06), 0 8px 32px rgba(0,0,0,0.22)',
    } as React.CSSProperties,
    pill: {
        background: 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)',
        backdropFilter: 'blur(24px) saturate(160%)',
        WebkitBackdropFilter: 'blur(24px) saturate(160%)',
        border: '1px solid rgba(255,255,255,0.10)',
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.20), 0 4px 12px rgba(0,0,0,0.15)',
    } as React.CSSProperties,
};

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

// Catmull-Rom smoothing for real data rendering
function buildSmoothPath(prices: number[], width: number, height: number, pad: number) {
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min || 1;
    const points = prices.map((p, i) => ({
        x: (i / (prices.length - 1)) * width,
        y: pad + (1 - (p - min) / range) * (height - pad * 2),
    }));

    let d = `M${points[0].x},${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
        const p0 = points[i - 1] || points[i];
        const p1 = points[i];
        const p2 = points[i + 1];
        const p3 = points[i + 2] || p2;
        const cp1x = p1.x + (p2.x - p0.x) / 6, cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6, cp2y = p2.y - (p3.y - p1.y) / 6;
        d += ` C${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`;
    }
    return { line: d, area: `${d} L${width},${height} L0,${height} Z`, last: points[points.length - 1] };
}

// ==========================================
// 3. MOCK DATA
// ==========================================
const MOCK_DATA = {
    '1W': [2800, 2790, 2810, 2825, 2840, 2835, 2847.50],
    '1M': [2750, 2730, 2760, 2780, 2775, 2810, 2800, 2820, 2835, 2847.50],
    '6M': [2652, 2638, 2694, 2705, 2734, 2696, 2648, 2748, 2709, 2771, 2733, 2789, 2826, 2847.50],
    '1Y': [2400, 2450, 2380, 2500, 2550, 2600, 2580, 2650, 2700, 2680, 2750, 2847.50],
};

const BRONZE_DATA = [
    { label: "Market Cap", value: "19.3T" },
    { label: "P/E Ratio", value: "28.4" },
    { label: "Div Yield", value: "0.35%" },
    { label: "52W High", value: "3,024" },
    { label: "52W Low", value: "2,220" },
    { label: "Beta", value: "1.12" },
];

// ==========================================
// 4. MAIN WORKSPACE
// ==========================================
export default function Workspace() {
    const navigate = useNavigate();

    const [timeframe, setTimeframe] = useState<'1W' | '1M' | '6M' | '1Y'>('6M');
    const [watchlist, setWatchlist] = useState<string[]>(['HDFCBANK.NS', 'TCS.NS']);
    const [searchQuery, setSearchQuery] = useState('');

    // Command Log (Terminal Chat)
    const [command, setCommand] = useState('');
    const [log, setLog] = useState([
        { role: 'system', text: 'SYSTEM INITIALIZED. QUANTITATIVE ENGINE ONLINE.' },
        { role: 'ai', text: 'Loaded RELIANCE.NS. Valuation parameters conform to standard deviations. Ready for query.' }
    ]);
    const [isProcessing, setIsProcessing] = useState(false);
    const logEndRef = useRef<HTMLDivElement>(null);

    const chartData = buildSmoothPath(MOCK_DATA[timeframe], 600, 160, 10);
    const isWatched = watchlist.includes('RELIANCE.NS');

    const toggleWatchlist = () => {
        if (isWatched) setWatchlist(watchlist.filter(t => t !== 'RELIANCE.NS'));
        else setWatchlist([...watchlist, 'RELIANCE.NS']);
    };

    const handleCommand = (e: React.FormEvent) => {
        e.preventDefault();
        if (!command.trim()) return;

        setLog(prev => [...prev, { role: 'user', text: command }]);
        setCommand('');
        setIsProcessing(true);

        setTimeout(() => {
            setIsProcessing(false);
            setLog(prev => [...prev, {
                role: 'ai',
                text: 'Calculation complete. The recent localized drawdown of 4.2% presents a statistically significant entry vector when weighted against sector momentum metrics.'
            }]);
            logEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 800);
    };

    return (
        <div className="relative w-full h-screen bg-[#030508] text-white overflow-hidden font-sans flex flex-col">

            {/* FIXED BACKGROUNDS (Strict constraint) */}
            <div className="fixed inset-0 z-0 bg-grid pointer-events-none opacity-50" />
            <div className="fixed inset-0 z-0 mix-blend-screen pointer-events-none">
                <Canvas camera={{ position: [0, 0, 5] }}><DataPoints /></Canvas>
            </div>
            {/* Very faint background orbs to provide light for the glass, no motion */}
            <div className="fixed top-[-10%] right-[-5%] w-[800px] h-[800px] bg-emerald-500/10 rounded-full blur-[150px] pointer-events-none" />

            {/* =========================================
                TOP NAVIGATION BAR (Strict geometric)
            ============================================= */}
            <nav className="relative z-50 w-full h-16 border-b border-white/10 bg-[#030508]/80 backdrop-blur-md flex items-center px-6 justify-between shrink-0">
                <div
                    onClick={() => navigate('/')}
                    className="font-bold text-xl tracking-tighter text-white flex items-center gap-2 cursor-pointer"
                >
                    INVR<span className="text-emerald-500">.</span>
                </div>

                {/* Search Bar - Center */}
                <div className="flex-1 max-w-xl mx-8 relative group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30 group-focus-within:text-emerald-500 transition-colors" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Query ticker or asset class..."
                        className="w-full bg-white/5 border border-white/10 rounded-md py-1.5 pl-10 pr-4 outline-none text-sm font-bold tracking-tighter text-white placeholder-white/30 focus:border-emerald-500/50 transition-colors"
                    />
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded border border-white/10 text-[9px] font-mono text-white/30">
                        CTRL K
                    </div>
                </div>

                <div className="flex items-center gap-4 text-[10px] font-bold tracking-widest uppercase text-white/40">
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Live
                    </div>
                    <span>Client: 0x9A8F...</span>
                </div>
            </nav>

            {/* =========================================
                MAIN 3-PANE LAYOUT
            ============================================= */}
            <div className="flex-1 flex overflow-hidden relative z-10">

                {/* PANE 1: WATCHLIST (Left Sidebar) */}
                <div className="w-64 border-r border-white/10 bg-[#030508]/60 backdrop-blur-sm flex flex-col shrink-0">
                    <div className="p-4 border-b border-white/10">
                        <p className="text-[10px] font-bold tracking-widest uppercase text-white/40 mb-1">Index</p>
                        <h2 className="text-sm font-bold tracking-tighter text-white">Active Watchlist</h2>
                    </div>
                    <div className="flex-1 overflow-y-auto custom-scrollbar p-2 flex flex-col gap-1">
                        {/* Active Item */}
                        <div className="px-3 py-2.5 rounded-md bg-white/5 border border-white/10 flex justify-between items-center cursor-pointer">
                            <div>
                                <h4 className="text-sm font-bold tracking-tighter text-emerald-400">RELIANCE</h4>
                                <span className="text-[10px] text-white/40 font-mono">NSE</span>
                            </div>
                            <Activity className="w-3.5 h-3.5 text-emerald-500" />
                        </div>
                        {/* Inactive Items */}
                        {watchlist.filter(t => t !== 'RELIANCE.NS').map(ticker => (
                            <div key={ticker} className="px-3 py-2.5 rounded-md hover:bg-white/5 border border-transparent transition-colors flex justify-between items-center cursor-pointer">
                                <div>
                                    <h4 className="text-sm font-bold tracking-tighter text-white/60">{ticker.split('.')[0]}</h4>
                                    <span className="text-[10px] text-white/40 font-mono">NSE</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* PANE 2: EXPLORER (Center Stage) */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 md:p-8 flex flex-col gap-8">

                    {/* Header Data */}
                    <div className="flex justify-between items-end">
                        <div>
                            <div className="flex items-center gap-3 mb-1">
                                <h1 className="text-5xl font-bold tracking-tighter text-white">RELIANCE</h1>
                                <button onClick={toggleWatchlist} className="hover:text-emerald-400 transition-colors">
                                    {isWatched ? <BookmarkCheck className="w-5 h-5 text-emerald-500" /> : <Plus className="w-5 h-5 text-white/40" />}
                                </button>
                            </div>
                            <p className="text-sm text-white/50 font-bold tracking-tighter">Reliance Industries Ltd</p>
                        </div>
                        <div className="text-right">
                            <h2 className="text-4xl font-bold tracking-tighter tabular-nums text-white">₹2,847.50</h2>
                            <p className="text-sm font-bold tracking-tighter text-emerald-400">+₹65.20 (+2.34%)</p>
                        </div>
                    </div>

                    {/* Chart Container (Glass isolation) */}
                    <div className="rounded-[1.5rem] p-6 relative overflow-hidden" style={glass.base}>
                        {/* Timeframe Selector (Rigid text, no rounded pills) */}
                        <div className="flex gap-4 mb-6 border-b border-white/10 pb-2">
                            {['1W', '1M', '6M', '1Y'].map((tf) => (
                                <button
                                    key={tf}
                                    onClick={() => setTimeframe(tf as any)}
                                    className={`text-[11px] font-bold tracking-widest uppercase transition-colors pb-2 relative ${timeframe === tf ? 'text-emerald-400' : 'text-white/40 hover:text-white/80'}`}
                                >
                                    {tf}
                                    {timeframe === tf && (
                                        <motion.div layoutId="tf-underline" className="absolute bottom-0 left-0 right-0 h-[2px] bg-emerald-500" />
                                    )}
                                </button>
                            ))}
                        </div>

                        {/* Interactive Chart */}
                        <div className="h-[280px] w-full relative">
                            <svg viewBox="0 0 600 160" className="w-full h-full overflow-visible" preserveAspectRatio="none">
                                <defs>
                                    <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                                        <stop offset="0%" stopColor="#0D9488" />
                                        <stop offset="100%" stopColor="#10B981" />
                                    </linearGradient>
                                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#10B981" stopOpacity="0.15" />
                                        <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
                                    </linearGradient>
                                </defs>
                                {[0.25, 0.5, 0.75].map((f) => (
                                    <line key={f} x1="0" x2="600" y1={160 * f} y2={160 * f} stroke="rgba(255,255,255,0.05)" strokeWidth="1" strokeDasharray="4 4" />
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
                                />
                            </svg>
                            {/* Live Dot */}
                            <motion.div
                                style={{ left: `${(chartData.last.x / 600) * 100}%`, top: `${(chartData.last.y / 160) * 100}%` }}
                                className="absolute -translate-y-1/2 -translate-x-1/2"
                            >
                                <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,1)]" />
                            </motion.div>
                        </div>
                    </div>

                    {/* Data Grids */}
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

                        {/* GOLD LAYER VERDICT */}
                        <div className="xl:col-span-2 rounded-[1.5rem] p-6 relative overflow-hidden" style={glass.base}>
                            <div className="absolute top-0 left-0 bottom-0 w-1 bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.5)]" />
                            <div className="flex items-center gap-2 mb-3 ml-2">
                                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                                <h3 className="text-sm font-bold tracking-widest uppercase text-emerald-400">System Verdict: Approved</h3>
                            </div>
                            <p className="text-white/80 font-bold tracking-tighter text-base leading-relaxed ml-2">
                                Asset clears all mandatory valuation hard-gates. P/E ratio is 14% below the 5-year historical median. Relative momentum convergence aligns perfectly with your stated parameters.
                            </p>
                        </div>

                        {/* BRONZE LAYER DATA GRID */}
                        <div className="xl:col-span-1 rounded-[1.5rem] p-6 flex flex-col justify-between" style={glass.base}>
                            <div className="flex items-center gap-2 text-[10px] font-bold tracking-widest uppercase text-white/40 mb-4 border-b border-white/10 pb-2">
                                <Database className="w-3 h-3" /> Raw Ingestion
                            </div>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                                {BRONZE_DATA.map((data, i) => (
                                    <div key={i} className="flex flex-col">
                                        <span className="text-[9px] font-bold tracking-widest uppercase text-white/40">{data.label}</span>
                                        <span className="text-sm font-bold tracking-tighter tabular-nums text-white">{data.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* PANE 3: EXECUTION LOG (Terminal/Copilot) */}
                <div className="w-[400px] border-l border-white/10 bg-[#030508]/80 backdrop-blur-md flex flex-col shrink-0 relative z-20">

                    {/* Terminal Header */}
                    <div className="p-4 border-b border-white/10 flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-emerald-400" />
                        <h3 className="text-xs font-bold tracking-widest uppercase text-white/60">Execution Log</h3>
                    </div>

                    {/* Terminal Output Area (Replaces chat bubbles) */}
                    <div className="flex-1 p-4 overflow-y-auto custom-scrollbar flex flex-col gap-1 text-sm font-mono tracking-tight">
                        {log.map((msg, i) => (
                            <div key={i} className="py-2 border-b border-white/5 last:border-0 flex flex-col gap-1">
                                <span className={`text-[10px] font-bold tracking-widest uppercase ${msg.role === 'user' ? 'text-white/30' : msg.role === 'system' ? 'text-teal-400' : 'text-emerald-400'}`}>
                                    {msg.role === 'user' ? '> USER_INPUT' : msg.role === 'system' ? '[SYS_INIT]' : '>> QUANT_OUTPUT'}
                                </span>
                                <span className={`leading-relaxed ${msg.role === 'user' ? 'text-white/60' : 'text-white'}`}>
                                    {msg.text}
                                </span>
                            </div>
                        ))}
                        {isProcessing && (
                            <div className="py-2 flex items-center gap-2 text-emerald-400/50">
                                <div className="w-1.5 h-3 bg-emerald-500 animate-pulse" />
                                <span className="text-xs">Processing compute...</span>
                            </div>
                        )}
                        <div ref={logEndRef} />
                    </div>

                    {/* Command Input */}
                    <div className="p-4 border-t border-white/10 bg-black/20">
                        <form onSubmit={handleCommand} className="relative flex items-center">
                            <CornerDownRight className="absolute left-3 w-4 h-4 text-white/30" />
                            <input
                                type="text"
                                value={command}
                                onChange={(e) => setCommand(e.target.value)}
                                placeholder="Enter query parameters..."
                                className="w-full bg-transparent border border-white/10 rounded-sm py-2 pl-9 pr-4 outline-none text-sm font-mono text-white placeholder-white/30 focus:border-emerald-500/50 transition-colors"
                            />
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}