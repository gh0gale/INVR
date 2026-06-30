import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { Search, Plus, BookmarkCheck, CornerDownRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../supabase';

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
    const pointsRef = useRef<any>(null);
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
                <bufferAttribute attach="attributes-position" args={[positions, 3]} />
            </bufferGeometry>
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
// 4. DATA FALLBACKS
// ==========================================
const MOCK_PRICES = {
    '1W': [2800, 2790, 2810, 2825, 2840, 2835, 2847.50],
    '1M': [2750, 2730, 2760, 2780, 2775, 2810, 2800, 2820, 2835, 2847.50],
    '6M': [2652, 2638, 2694, 2705, 2734, 2696, 2648, 2748, 2709, 2771, 2733, 2789, 2826, 2847.50],
    '1Y': [2400, 2450, 2380, 2500, 2550, 2600, 2580, 2650, 2700, 2680, 2750, 2847.50],
} as const;

function getPricesForChart(tf: '1W' | '1M' | '6M' | '1Y', currentPrice?: number): number[] {
    const mockPattern = MOCK_PRICES[tf];
    if (!currentPrice) return [...mockPattern];
    const base = mockPattern[mockPattern.length - 1];
    const scale = currentPrice / base;
    return mockPattern.map(p => p * scale);
}

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
    const { session, profile, logout } = useAuth();
    const [timeframe, setTimeframe] = useState<'1W' | '1M' | '6M' | '1Y'>('6M');
    
    // Watchlist state (tickers user has bookmarked)
    const [watchlist, setWatchlist] = useState<string[]>(['RELIANCE.NS', 'TCS.NS', 'INFY.NS']);
    const [searchQuery, setSearchQuery] = useState('');

    // Dynamic ledger items fetched from DB
    const [ledgerItems, setLedgerItems] = useState<any[]>([]);
    const [activeItem, setActiveItem] = useState<any | null>(null);

    const [command, setCommand] = useState('');
    const [log, setLog] = useState<{ role: 'sys' | 'user' | 'ai'; text: string; time: string }[]>([
        { role: 'sys', text: 'INVR QUANTITATIVE ENGINE ONLINE. KERNEL V4.2.0', time: getTime() },
        { role: 'sys', text: 'READY: INPUT TICKER (e.g. RELIANCE) OR ASK THE COPILOT.', time: getTime() }
    ]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [sessionId] = useState(() => crypto.randomUUID());
    const logEndRef = useRef<HTMLDivElement>(null);

    // Dynamic metrics & price series based on activeItem or mock fallbacks
    const activePrice = activeItem?.silver_state?.current_price ?? 2847.50;
    const chartPrices = getPricesForChart(timeframe, activeItem?.silver_state?.current_price);
    const chartData = buildPriceChart(chartPrices);
    const isWatched = activeItem ? watchlist.includes(activeItem.ticker) : watchlist.includes('RELIANCE.NS');

    // Dynamic Display Metrics
    const displayMetrics = activeItem ? [
        { label: 'Current Price', value: `₹${activeItem.silver_state.current_price?.toFixed(2) || 'N/A'}` },
        { label: 'Current Volume', value: activeItem.silver_state.current_volume?.toLocaleString() || 'N/A' },
        { label: 'RSI (14)', value: activeItem.silver_state.rsi_14?.toFixed(2) || 'N/A' },
        { label: 'ATR (14)', value: `₹${activeItem.silver_state.atr_14?.toFixed(2) || 'N/A'}` },
        { label: 'SMA (20)', value: `₹${activeItem.silver_state.sma_20?.toFixed(2) || 'N/A'}` },
        { label: 'SMA (50)', value: `₹${activeItem.silver_state.sma_50?.toFixed(2) || 'N/A'}` },
    ] : BRONZE_DATA;

    // Dynamic System Verdict
    const verdictData = activeItem ? {
        verdict: activeItem.gold_verdict.verdict,
        score: (activeItem.gold_verdict.confidence_score / 10.0) || 0.0,
        reason: activeItem.gold_verdict.primary_reason,
        gates: Object.entries(activeItem.gold_verdict.gate_results || {}).map(([name, status]) => ({
            name: name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            status: String(status)
        })),
        setup: activeItem.gold_verdict.trade_setup ? {
            entry_low: activeItem.gold_verdict.trade_setup.entry_zone_low,
            entry_high: activeItem.gold_verdict.trade_setup.entry_zone_high,
            stop_loss: activeItem.gold_verdict.trade_setup.stop_loss,
            target_1: activeItem.gold_verdict.trade_setup.target_1,
            target_2: activeItem.gold_verdict.trade_setup.target_2,
            rr_ratio: activeItem.gold_verdict.trade_setup.risk_reward_ratio,
        } : null
    } : VERDICT_DATA;

    // Load active ledger history on mount
    const fetchLedger = async () => {
        if (!session) return;
        try {
            const { data, error } = await supabase
                .from('algorithmic_ledger')
                .select('*')
                .order('created_at', { ascending: false })
                .limit(20);
            
            if (error) throw error;
            if (data && data.length > 0) {
                setLedgerItems(data);
                // Set the most recent one as active if nothing is selected
                if (!activeItem) {
                    setActiveItem(data[0]);
                }
            }
        } catch (err) {
            console.error('Error fetching algorithmic ledger:', err);
        }
    };

    useEffect(() => {
        fetchLedger();
    }, [session]);

    // Handle ticker analysis execution
    const runAnalysis = async (rawTicker: string) => {
        if (!session || !profile) return;
        
        let ticker = rawTicker.trim().toUpperCase();
        if (!ticker.endsWith('.NS')) {
            ticker += '.NS';
        }

        setIsProcessing(true);
        setLog(prev => [
            ...prev,
            { role: 'sys', text: `SPAWNING QUANT PIPELINE INSTANCE FOR ${ticker}...`, time: getTime() }
        ]);

        try {
            // Step-by-step logs simulating state nodes
            setTimeout(() => {
                setLog(prev => [...prev, { role: 'sys', text: `[STAGE 1]: Fetching Bronze telemetry for ${ticker}...`, time: getTime() }]);
            }, 500);

            setTimeout(() => {
                setLog(prev => [...prev, { role: 'sys', text: `[STAGE 2]: Computing Silver vectorized metrics...`, time: getTime() }]);
            }, 1200);

            setTimeout(() => {
                setLog(prev => [...prev, { role: 'sys', text: `[STAGE 3]: Testing Gold logic and hard gates...`, time: getTime() }]);
            }, 2000);

            const payload = {
                ticker: ticker,
                timeframe: profile.timeframe || 'swing',
                user_profile: {
                    risk_tolerance: profile.risk,
                    experience_level: profile.experience,
                    goal: profile.goal,
                    available_capital: profile.capital
                },
                session_id: sessionId
            };

            const response = await fetch('http://localhost:8000/api/v1/analytics/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Pipeline execution failed.');
            }

            const resData = await response.json();
            
            // Wait slightly to ensure background task has written to the DB ledger
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Query database ledger for the results
            const { data, error } = await supabase
                .from('algorithmic_ledger')
                .select('*')
                .eq('ticker', ticker)
                .order('created_at', { ascending: false })
                .limit(1);

            if (error) throw error;
            
            if (data && data.length > 0) {
                setActiveItem(data[0]);
                // Refresh full active list
                fetchLedger();
                
                // Set log outputs from the LLM synthesis
                const reasoning = resData.llm_analysis?.personalized_reasoning ?? [];
                const finalSummary = reasoning.join(' ') || `Analysis complete. Verdict: ${resData.verdict}`;
                
                setLog(prev => [
                    ...prev,
                    { role: 'sys', text: `[STAGE 8]: Hybrid Ledger logged successfully.`, time: getTime() },
                    { role: 'ai', text: finalSummary, time: getTime() }
                ]);
            } else {
                throw new Error('Ledger record was not found after execution.');
            }

        } catch (err: any) {
            setLog(prev => [
                ...prev,
                { role: 'sys', text: `[ERROR]: ${err.message || 'Verification failed.'}`, time: getTime() }
            ]);
        } finally {
            setIsProcessing(false);
            setTimeout(() => {
                logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
            }, 200);
        }
    };

    // Chat command / message handler
    const handleCommand = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!command.trim() || isProcessing) return;
        const cmd = command.trim();
        setCommand('');
        setLog(prev => [...prev, { role: 'user', text: cmd, time: getTime() }]);
        setIsProcessing(true);

        // Check if user is typing a direct analyze command
        if (cmd.toUpperCase().startsWith('/ANALYZE ')) {
            const tk = cmd.substring(9).trim();
            if (tk) {
                await runAnalysis(tk);
                return;
            }
        }

        try {
            // Post to the Tutor stream
            const response = await fetch('http://localhost:8000/api/v1/tutor/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session?.access_token}`
                },
                body: JSON.stringify({
                    message: cmd,
                    session_id: sessionId,
                    analysis_context: {
                        silver: activeItem?.silver_state || {},
                        gold: activeItem?.gold_verdict || {}
                    },
                    user_profile: {
                        risk_tolerance: profile?.risk || 'moderate',
                        experience_level: profile?.experience || 'intermediate',
                        goal: profile?.goal || 'wealth_growth',
                        available_capital: profile?.capital || 100000.0
                    }
                })
            });

            if (!response.ok) {
                throw new Error('Failed to stream response from Tutor.');
            }

            const reader = response.body?.getReader();
            if (!reader) throw new Error('Stream reader unavailable.');

            const decoder = new TextDecoder();
            let aiText = '';

            // Add the streaming message slot
            setLog(prev => [...prev, { role: 'ai', text: '', time: getTime() }]);

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6).trim();
                        if (dataStr === '[DONE]') break;
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.token) {
                                aiText += data.token;
                                setLog(prev => {
                                    const next = [...prev];
                                    if (next.length > 0) {
                                        next[next.length - 1] = {
                                            ...next[next.length - 1],
                                            text: aiText
                                        };
                                    }
                                    return next;
                                });
                            } else if (data.error) {
                                throw new Error(data.error);
                            }
                        } catch (e) {
                            // JSON parse error or similar
                        }
                    }
                }
            }

        } catch (err: any) {
            setLog(prev => [
                ...prev,
                { role: 'sys', text: `[TUTOR ERROR]: ${err.message || 'Stream disrupted.'}`, time: getTime() }
            ]);
        } finally {
            setIsProcessing(false);
            setTimeout(() => {
                logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
            }, 200);
        }
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
            <div
                className="fixed top-0 inset-x-0 h-20 z-40 pointer-events-none"
                style={{
                    backdropFilter: 'blur(20px)',
                    WebkitBackdropFilter: 'blur(20px)',
                    background: 'linear-gradient(180deg, rgba(3,5,8,0.80) 0%, rgba(3,5,8,0) 100%)',
                }}
            />
            <nav className="relative z-50 w-full px-2 flex items-center justify-between shrink-0 h-14">
                <div
                    onClick={() => navigate('/')}
                    className="font-bold text-2xl tracking-tighter text-white flex items-center cursor-pointer select-none"
                >
                    INVR<span className="text-emerald-500">.</span>
                </div>

                {/* Search Explorer — glass.nested form */}
                <form 
                    onSubmit={(e) => {
                        e.preventDefault();
                        if (searchQuery.trim()) {
                            runAnalysis(searchQuery);
                            setSearchQuery('');
                        }
                    }}
                    className="flex-1 max-w-2xl mx-8 relative group"
                >
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
                            ENTER
                        </div>
                    </div>
                </form>

                {/* Live status badge & logout button */}
                <div className="hidden lg:flex items-center gap-3">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-full" style={glass.pill}>
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                        <span className="text-[11px] font-bold tracking-tighter text-emerald-400 uppercase">Live</span>
                        <span className="text-[10px] font-bold tracking-[0.12em] text-white/40 uppercase">
                          {profile?.experience ? `${profile.experience.toUpperCase()}` : 'USER'}
                        </span>
                    </div>
                    <motion.button
                        onClick={logout}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="px-4 py-2 rounded-full text-[10px] font-bold tracking-[0.15em] uppercase text-rose-400 hover:bg-rose-500/10 transition-colors"
                        style={glass.pill}
                    >
                        Disconnect
                    </motion.button>
                </div>
            </nav>

            {/* ── MAIN WORKSPACE (3 panes) ── */}
            <div className="flex-1 flex gap-4 min-h-0 relative z-10 w-full">

                {/* ═══════════════════════════════════════
                    PANE 1: ACTIVE LEDGER (left sidebar)
                ═══════════════════════════════════════ */}
                <div className="hidden lg:flex w-[260px] flex-col rounded-[2.5rem] overflow-hidden shrink-0" style={glass.base}>
                    <div className="p-6 border-b border-white/10 shrink-0">
                        <p className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40">Active Ledger</p>
                    </div>

                    <div className="flex-1 overflow-y-auto no-scrollbar p-4 flex flex-col gap-3">
                        {ledgerItems.length === 0 ? (
                            <div className="p-4 text-center text-xs text-white/30 uppercase tracking-[0.1em]">
                                No active predictions. Run search.
                            </div>
                        ) : (
                            ledgerItems.map((item) => {
                                const isSelected = activeItem?.log_id === item.log_id;
                                return (
                                    <motion.div
                                        key={item.log_id}
                                        onClick={() => setActiveItem(item)}
                                        className="p-4 rounded-[1.25rem] flex justify-between items-center cursor-pointer relative overflow-hidden"
                                        style={isSelected ? {
                                            border: '1px solid rgba(16,185,129,0.35)',
                                            background: 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(13,148,136,0.04) 100%)',
                                            boxShadow: '0 0 20px rgba(16,185,129,0.12), inset 0 1px 0 rgba(255,255,255,0.18)',
                                        } : glass.nested}
                                        whileHover={{ scale: 1.01 }}
                                        transition={springSoft}
                                    >
                                        <div>
                                            <h4 className={`text-lg font-bold tracking-tighter ${isSelected ? 'text-white' : 'text-white/50 hover:text-white transition-colors'}`}>
                                                {item.ticker.split('.')[0]}
                                            </h4>
                                            <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-1 rounded-[0.875rem]" style={glass.nested}>
                                                <span className="text-[10px] font-bold tracking-[0.15em] text-emerald-400 uppercase tabular-nums">
                                                    {(item.gold_verdict.confidence_score / 10.0)?.toFixed(1) || '0.0'} Score
                                                </span>
                                            </div>
                                        </div>
                                        {isSelected && (
                                            <motion.div
                                                className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"
                                                animate={{ scale: [1, 1.4, 1], opacity: [1, 0.6, 1] }}
                                                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                                            />
                                        )}
                                    </motion.div>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* ═══════════════════════════════════════
                    PANE 2: EXPLORER (center, scrollable)
                ═══════════════════════════════════════ */}
                <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col gap-4">

                    {/* TOP: Primary Chart Card */}
                    <div className="rounded-[2.5rem] p-8 flex flex-col gap-6 shrink-0 relative overflow-hidden" style={glass.base}>
                        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 relative z-10">
                            <div>
                                <div className="flex items-center gap-4 mb-2">
                                    <motion.h1
                                        className="text-5xl md:text-[4rem] font-bold tracking-tighter text-white leading-none"
                                        animate={{ y: [0, -3, 0] }}
                                        transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
                                    >
                                        {activeItem?.ticker?.split('.')[0] ?? 'RELIANCE'}
                                    </motion.h1>
                                    <motion.button
                                        onClick={() => {
                                            const activeTicker = activeItem?.ticker ?? 'RELIANCE.NS';
                                            isWatched
                                                ? setWatchlist(watchlist.filter(t => t !== activeTicker))
                                                : setWatchlist([...watchlist, activeTicker]);
                                        }}
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
                                    {activeItem ? `${activeItem.ticker} • ${activeItem.timeframe.toUpperCase()}` : 'Reliance Industries Ltd • NSE'}
                                </p>
                            </div>

                            <div className="flex flex-col md:items-end">
                                <div className="inline-flex flex-col items-end gap-1">
                                    <span className="text-4xl md:text-5xl font-bold tracking-tighter tabular-nums text-white">
                                        ₹{activePrice.toFixed(2)}
                                    </span>
                                    <span className="text-sm font-bold tracking-tighter text-emerald-400">
                                        +2.34%
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Chart panel */}
                        <div className="rounded-[1.5rem] p-6 relative" style={glass.nested}>
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

                            {/* Chart */}
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
                                                <stop offset="0%" stopColor="#10B981" stopOpacity="0.20" />
                                                <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
                                            </linearGradient>
                                        </defs>

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

                        {/* GOLD VERDICT CARD (3 cols) */}
                        <div className="xl:col-span-3 rounded-[2.5rem] p-8 flex flex-col relative overflow-hidden" style={glass.base}>
                            <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-gradient-to-b from-emerald-400 to-teal-500 shadow-[0_0_20px_rgba(16,185,129,0.5)]" />

                            <div className="ml-5">
                                <p className="text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400 mb-1.5">
                                    Gold Layer · System Verdict
                                </p>

                                <div className="flex items-center gap-4 mb-4">
                                    <h3 className="text-2xl font-bold tracking-tighter text-white">
                                        {verdictData.verdict}
                                    </h3>
                                    <div
                                        className="flex flex-col items-center justify-center px-4 py-2 rounded-[1.25rem]"
                                        style={glass.nested}
                                    >
                                        <span className="font-bold tracking-tighter text-xl text-white tabular-nums leading-none">
                                            {verdictData.score.toFixed(1)}
                                        </span>
                                        <span className="text-[9px] font-bold tracking-[0.15em] text-emerald-400 uppercase mt-1">
                                            Score
                                        </span>
                                    </div>
                                </div>

                                <p className="text-white/55 font-bold tracking-tighter text-base leading-relaxed mb-6 max-w-xl">
                                    {verdictData.reason}
                                </p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {/* Gates list */}
                                    <div className="flex flex-col gap-3">
                                        <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40 mb-1">
                                            Hard Gates Cleared
                                        </h4>
                                        {verdictData.gates.map((g, i) => (
                                            <div key={i} className="flex justify-between items-center py-2 border-b border-white/5">
                                                <span className="text-sm font-bold tracking-tighter text-white/70">{g.name}</span>
                                                <span className="text-[10px] font-bold tracking-[0.15em] text-emerald-400 uppercase">{g.status}</span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Trade setup */}
                                    {verdictData.setup && (
                                        <div className="rounded-[1.5rem] p-5 relative overflow-hidden" style={glass.nested}>
                                            <div className="absolute top-0 left-6 right-6 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
                                            <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400 mb-3 mt-1">
                                                Trade Architecture
                                            </h4>
                                            {[
                                                { label: 'Entry Zone',  val: `₹${verdictData.setup.entry_low} – ${verdictData.setup.entry_high}`, cls: 'text-white' },
                                                { label: 'Stop Loss',   val: `₹${verdictData.setup.stop_loss}`, cls: 'text-red-400' },
                                                { label: 'Targets',     val: `₹${verdictData.setup.target_1} / ${verdictData.setup.target_2}`, cls: 'text-emerald-400' },
                                                { label: 'R/R Ratio',   val: `${verdictData.setup.rr_ratio}×`, cls: 'text-white/70' },
                                            ].map(({ label, val, cls }) => (
                                                <div key={label} className="flex justify-between items-center py-1.5">
                                                    <span className="text-sm font-bold tracking-tighter text-white/55">{label}</span>
                                                    <span className={`text-sm font-bold tracking-tighter tabular-nums ${cls}`}>{val}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* BRONZE DATA GRID (2 cols) */}
                        <div className="xl:col-span-2 rounded-[2.5rem] p-8 flex flex-col" style={glass.base}>
                            <div className="mb-5 border-b border-white/10 pb-4">
                                <p className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40">
                                    Bronze Layer · Raw Ingestion
                                </p>
                            </div>
                            <div className="grid grid-cols-2 gap-3 flex-1 content-start">
                                {displayMetrics.map((data, i) => (
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
                    <div className="p-6 border-b border-white/10 flex justify-between items-center shrink-0">
                        <div>
                            <p className="text-[10px] font-bold tracking-[0.18em] uppercase text-emerald-400 mb-1">
                                Execution Log
                            </p>
                            <h3 className="text-base font-bold tracking-tighter text-white">
                                Quant Copilot
                            </h3>
                        </div>
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

                    {/* Command input */}
                    <div className="p-4 border-t border-white/10 shrink-0 bg-black/40">
                        <form onSubmit={handleCommand} className="relative flex items-center rounded-[1.25rem] p-1" style={glass.nested}>
                            <CornerDownRight className="absolute left-4 w-4 h-4 text-white/30" />
                            <input
                                type="text"
                                value={command}
                                onChange={(e) => setCommand(e.target.value)}
                                placeholder={isProcessing ? 'Waiting for engine...' : 'Enter query parameters or /analyze TICKER...'}
                                disabled={isProcessing}
                                className="w-full bg-transparent border-none py-4 pl-12 pr-4 outline-none text-sm font-mono text-white placeholder-white/30 disabled:opacity-50"
                            />
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}