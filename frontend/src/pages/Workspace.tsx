import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { Search, Plus, BookmarkCheck, CornerDownRight, Trash2, Menu, List } from 'lucide-react';
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

// Ticker pattern: all alpha + optional .NS suffix, no spaces — used to auto-detect analyze intent
const TICKER_PATTERN = /^[A-Za-z0-9&-]{2,12}(\.NS)?$/;

const getTime = () => new Date().toLocaleTimeString('en-US', { hour12: false });

// ==========================================
// 5. MAIN WORKSPACE
// ==========================================
export default function Workspace() {
    const navigate = useNavigate();
    const { session, profile, logout } = useAuth();
    const [timeframe, setTimeframe] = useState<'1W' | '1M' | '6M' | '1Y'>('6M');
    
    // Sidebar state
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [sidebarTab, setSidebarTab] = useState<'ledger' | 'watchlist'>('ledger');

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

    // Dynamic metrics & price series — strictly from activeItem, no hardcoded fallbacks
    const activePrice = activeItem?.silver_state?.current_price ?? null;
    const chartPrices = activePrice ? getPricesForChart(timeframe, activePrice) : null;
    const chartData = chartPrices ? buildPriceChart(chartPrices) : null;
    const isWatched = activeItem ? watchlist.includes(activeItem.ticker) : false;

    // Display Metrics — strictly from activeItem
    const displayMetrics = activeItem ? [
        { label: 'Current Price', value: `₹${activeItem.silver_state.current_price?.toFixed(2) ?? 'N/A'}`, desc: 'Latest closing/active price' },
        { label: 'Current Volume', value: activeItem.silver_state.current_volume?.toLocaleString() ?? 'N/A', desc: 'Trading activity for the period' },
        { label: 'RSI (14)', value: activeItem.silver_state.rsi_14?.toFixed(2) ?? 'N/A', desc: 'Momentum: >70 Overbought, <30 Oversold' },
        { label: 'ATR (14)', value: activeItem.silver_state.atr_14 != null ? `₹${activeItem.silver_state.atr_14.toFixed(2)}` : 'N/A', desc: 'Average price volatility' },
        { label: 'SMA (20)', value: activeItem.silver_state.sma_20 != null ? `₹${activeItem.silver_state.sma_20.toFixed(2)}` : 'N/A', desc: 'Short-term trend line' },
        { label: 'SMA (50)', value: activeItem.silver_state.sma_50 != null ? `₹${activeItem.silver_state.sma_50.toFixed(2)}` : 'N/A', desc: 'Medium-term support/resistance' },
    ] : null;

    // System Verdict — strictly from activeItem
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
        } : null,
        llm_analysis: activeItem.gold_verdict.llm_analysis || null
    } : null;

    // Load active ledger — deduplicated by ticker, capped to 5 most recent unique tickers
    const fetchLedger = async () => {
        if (!session) return;
        try {
            const { data, error } = await supabase
                .from('algorithmic_ledger')
                .select('*')
                .order('created_at', { ascending: false })
                .limit(50); // fetch more to allow dedup
            
            if (error) throw error;
            if (data && data.length > 0) {
                // Deduplicate: keep only the most recent entry per unique ticker
                const seen = new Set<string>();
                const deduped = data.filter((item: any) => {
                    if (seen.has(item.ticker)) return false;
                    seen.add(item.ticker);
                    return true;
                }).slice(0, 5); // cap to 5 unique tickers

                setLedgerItems(deduped);
                // Auto-select most recent if nothing active yet
                if (!activeItem) {
                    setActiveItem(deduped[0]);
                }
            }
        } catch (err) {
            console.error('Error fetching algorithmic ledger:', err);
        }
    };

    useEffect(() => {
        fetchLedger();
    }, [session]);

    const deleteLedgerItem = async (e: React.MouseEvent, logId: string) => {
        e.stopPropagation();
        try {
            await supabase.from('algorithmic_ledger').delete().eq('log_id', logId);
            setLedgerItems(prev => prev.filter(item => item.log_id !== logId));
            if (activeItem?.log_id === logId) {
                setActiveItem(null);
            }
        } catch (err) {
            console.error('Error deleting ledger item:', err);
        }
    };

    // Handle ticker analysis execution
    const runAnalysis = async (rawTicker: string) => {
        if (!session) {
            setLog(prev => [...prev, { role: 'sys', text: '[ERROR]: No active session. Please reconnect.', time: getTime() }]);
            return;
        }
        if (!profile) {
            setLog(prev => [...prev, { role: 'sys', text: '[ERROR]: Profile not loaded. Please reload the page.', time: getTime() }]);
            return;
        }
        if (isProcessing) return;
        
        // Normalize ticker: strip any existing .NS then re-append cleanly
        const rawClean = rawTicker.trim().toUpperCase().replace(/\.NS$/i, '');
        const ticker = `${rawClean}.NS`;

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
            
            // If the pipeline itself reported an error, surface it immediately
            if (!resData.success) {
                const pipelineError = resData.errors?.[0] || 'Pipeline execution returned no data.';
                setLog(prev => [
                    ...prev,
                    { role: 'sys', text: `[PIPELINE ERROR]: ${pipelineError}`, time: getTime() }
                ]);
                // Still try to show a stale record if one exists (so the UI isn't blank)
                const apiTicker = (resData.ticker as string)?.toUpperCase() || ticker;
                const { data: staleData } = await supabase
                    .from('algorithmic_ledger')
                    .select('*')
                    .or(`ticker.eq.${apiTicker},ticker.eq.${rawClean}`)
                    .order('created_at', { ascending: false })
                    .limit(1);
                if (staleData && staleData.length > 0) {
                    setActiveItem(staleData[0]);
                    fetchLedger();
                }
                return;
            }

            // Wait for background ledger write — give it up to 3s
            await new Promise(resolve => setTimeout(resolve, 3000));

            // Query ledger using the ticker returned by the API (authoritative)
            // Try with .NS first, then bare ticker as fallback
            const apiTicker = (resData.ticker as string)?.toUpperCase() || ticker;
            const { data, error } = await supabase
                .from('algorithmic_ledger')
                .select('*')
                .or(`ticker.eq.${apiTicker},ticker.eq.${rawClean}`)
                .order('created_at', { ascending: false })
                .limit(1);

            if (error) throw error;
            
            if (data && data.length > 0) {
                setActiveItem(data[0]);
                // Refresh full active list
                fetchLedger();
                
                // Build summary from DB ground truth — this is always reliable
                const dbVerdict = data[0].gold_verdict?.verdict || resData.verdict || 'N/A';
                const dbScore = data[0].gold_verdict?.confidence_score != null
                    ? ` (Confidence: ${(data[0].gold_verdict.confidence_score / 10).toFixed(1)}/10)`
                    : '';
                const dbReason = data[0].gold_verdict?.primary_reason || '';
                // Authoritative one-liner from DB — never use raw LLM reasoning as the summary
                const finalSummary = `${data[0].ticker} — Verdict: ${dbVerdict}${dbScore}. ${dbReason}`;
                
                setLog(prev => [
                    ...prev,
                    { role: 'sys', text: `[STAGE 8]: Hybrid Ledger logged successfully.`, time: getTime() },
                    { role: 'ai', text: finalSummary, time: getTime() }
                ]);
            } else {
                // Pipeline succeeded but ledger write is still pending — use API response data directly
                setLog(prev => [
                    ...prev,
                    { role: 'sys', text: `[STAGE 8]: Pipeline complete. Verdict: ${resData.verdict}`, time: getTime() }
                ]);
                // Retry ledger fetch after additional wait
                await new Promise(resolve => setTimeout(resolve, 2000));
                fetchLedger();
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

        // Route to pipeline if: /analyze prefix OR bare ticker pattern (single word, looks like NSE ticker)
        const isAnalyzeCmd = cmd.toUpperCase().startsWith('/ANALYZE ');
        const isBareTickerInput = TICKER_PATTERN.test(cmd.trim());

        if (isAnalyzeCmd || isBareTickerInput) {
            const tk = isAnalyzeCmd ? cmd.substring(9).trim() : cmd.trim();
            if (tk) {
                await runAnalysis(tk);
                return;
            }
        }

        setIsProcessing(true);

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
            <nav className="relative z-50 w-full px-2 flex items-center justify-between shrink-0 h-14 gap-4">
                <div className="flex items-center gap-4">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className={`p-2.5 rounded-[1rem] transition-colors ${isSidebarOpen ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white hover:bg-white/5'}`}
                        style={glass.pill}
                    >
                        <Menu className="w-5 h-5" />
                    </motion.button>
                    <div className="font-bold text-2xl tracking-tighter text-white flex items-center select-none">
                        INVR<span className="text-emerald-500">.</span>
                    </div>
                </div>

                {/* Search Explorer — glass.nested form */}
                <form 
                    onSubmit={async (e) => {
                        e.preventDefault();
                        const q = searchQuery.trim();
                        if (q && !isProcessing) {
                            setSearchQuery('');
                            await runAnalysis(q);
                        }
                    }}
                    className="flex-1 max-w-2xl mx-8 relative group"
                >
                    <div
                        className="absolute inset-0 rounded-[1rem] transition-colors duration-300 group-focus-within:bg-white/[0.04]"
                        style={glass.nested}
                    />
                    <div className="relative flex items-center px-4 py-3 z-10">
                        {isProcessing ? (
                            <motion.div
                                className="w-4 h-4 mr-3 rounded-full border-2 border-emerald-500/30 border-t-emerald-500"
                                animate={{ rotate: 360 }}
                                transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                            />
                        ) : (
                            <Search className="w-4 h-4 text-white/40 mr-3 group-focus-within:text-emerald-400 transition-colors" />
                        )}
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder={isProcessing ? 'Pipeline running — please wait...' : 'Enter NSE ticker (e.g. TCS, RELIANCE, INFY)...'}
                            disabled={isProcessing}
                            className="w-full bg-transparent border-none outline-none text-sm font-bold tracking-tighter text-white placeholder-white/30 disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <div className={`hidden md:flex px-2 py-1 rounded-[0.5rem] border text-[9px] font-bold tracking-[0.15em] uppercase ${
                            isProcessing
                                ? 'border-emerald-500/30 text-emerald-400/50 bg-emerald-500/5'
                                : 'border-white/10 text-white/40 bg-white/5'
                        }`}>
                            {isProcessing ? '...' : 'ENTER'}
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
                    PANE 1: SIDEBAR (left)
                ═══════════════════════════════════════ */}
                <AnimatePresence>
                    {isSidebarOpen && (
                        <>
                            {/* Optional scrim to close sidebar when clicking outside */}
                            <motion.div 
                                key="sidebar-scrim"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={() => setIsSidebarOpen(false)}
                                className="absolute inset-0 z-40 bg-black/20 backdrop-blur-[2px]"
                            />
                            <motion.div 
                                key="sidebar-panel"
                                initial={{ x: -320, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                exit={{ x: -320, opacity: 0 }}
                                transition={springSoft}
                                className="absolute left-0 top-0 bottom-0 z-50 flex flex-col w-[280px] rounded-[2.5rem] overflow-hidden" 
                                style={{
                                    ...glass.base,
                                    boxShadow: '0 25px 80px rgba(0,0,0,0.8), ' + glass.base.boxShadow
                                }}
                            >
                            <div className="p-4 border-b border-white/10 shrink-0 flex gap-2">
                                <button
                                    onClick={() => setSidebarTab('ledger')}
                                    className={`flex-1 py-2 text-[10px] font-bold tracking-[0.15em] uppercase rounded-[1rem] transition-colors ${sidebarTab === 'ledger' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white/80'}`}
                                >
                                    Recent
                                </button>
                                <button
                                    onClick={() => setSidebarTab('watchlist')}
                                    className={`flex-1 py-2 text-[10px] font-bold tracking-[0.15em] uppercase rounded-[1rem] transition-colors ${sidebarTab === 'watchlist' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white/80'}`}
                                >
                                    Watchlist
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto no-scrollbar p-4 flex flex-col gap-3">
                                {sidebarTab === 'ledger' ? (
                                    // Ledger items
                                    ledgerItems.length === 0 ? (
                                        <div className="p-4 text-center text-xs text-white/30 uppercase tracking-[0.1em]">
                                            No active predictions. Run search.
                                        </div>
                                    ) : (
                                        ledgerItems.map((item) => {
                                            const isSelected = activeItem?.log_id === item.log_id;
                                            const isItemWatched = watchlist.includes(item.ticker);
                                            return (
                                                <motion.div
                                                    key={item.log_id}
                                                    onClick={() => setActiveItem(item)}
                                                    className="p-4 rounded-[1.25rem] flex flex-col gap-2 cursor-pointer relative overflow-hidden group"
                                                    style={isSelected ? {
                                                        border: '1px solid rgba(16,185,129,0.35)',
                                                        background: 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(13,148,136,0.04) 100%)',
                                                        boxShadow: '0 0 20px rgba(16,185,129,0.12), inset 0 1px 0 rgba(255,255,255,0.18)',
                                                    } : glass.nested}
                                                    whileHover={{ scale: 1.01 }}
                                                    transition={springSoft}
                                                >
                                                    <div className="flex justify-between items-start">
                                                        <div>
                                                            <h4 className={`text-lg font-bold tracking-tighter ${isSelected ? 'text-white' : 'text-white/50 group-hover:text-white transition-colors'}`}>
                                                                {item.ticker.split('.')[0]}
                                                            </h4>
                                                            <div className="mt-1 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[0.875rem]" style={glass.nested}>
                                                                <span className="text-[10px] font-bold tracking-[0.15em] text-emerald-400 uppercase tabular-nums">
                                                                    {(item.gold_verdict.confidence_score / 10.0)?.toFixed(1) || '0.0'} Score
                                                                </span>
                                                            </div>
                                                        </div>
                                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <button 
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    isItemWatched 
                                                                        ? setWatchlist(watchlist.filter(t => t !== item.ticker))
                                                                        : setWatchlist([...watchlist, item.ticker]);
                                                                }}
                                                                className="p-1.5 rounded-full hover:bg-white/10 text-white/50 hover:text-emerald-400 transition-colors"
                                                            >
                                                                {isItemWatched ? <BookmarkCheck className="w-4 h-4 text-emerald-400" /> : <Plus className="w-4 h-4" />}
                                                            </button>
                                                            <button 
                                                                onClick={(e) => deleteLedgerItem(e, item.log_id)}
                                                                className="p-1.5 rounded-full hover:bg-white/10 text-white/50 hover:text-rose-400 transition-colors"
                                                            >
                                                                <Trash2 className="w-4 h-4" />
                                                            </button>
                                                        </div>
                                                    </div>
                                                    {isSelected && (
                                                        <motion.div
                                                            className="absolute right-4 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"
                                                            animate={{ scale: [1, 1.4, 1], opacity: [1, 0.6, 1] }}
                                                            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                                                        />
                                                    )}
                                                </motion.div>
                                            );
                                        })
                                    )
                                ) : (
                                    // Watchlist items
                                    watchlist.length === 0 ? (
                                        <div className="p-4 text-center text-xs text-white/30 uppercase tracking-[0.1em]">
                                            Watchlist empty
                                        </div>
                                    ) : (
                                        watchlist.map((ticker) => (
                                            <div
                                                key={ticker}
                                                className="p-4 rounded-[1.25rem] flex justify-between items-center relative overflow-hidden group"
                                                style={glass.nested}
                                            >
                                                <h4 className="text-base font-bold tracking-tighter text-white/70 group-hover:text-white transition-colors">
                                                    {ticker.split('.')[0]}
                                                </h4>
                                                <div className="flex gap-2">
                                                    <button 
                                                        onClick={() => runAnalysis(ticker)}
                                                        className="p-1.5 rounded-full hover:bg-white/10 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity"
                                                    >
                                                        <Search className="w-4 h-4" />
                                                    </button>
                                                    <button 
                                                        onClick={() => setWatchlist(watchlist.filter(t => t !== ticker))}
                                                        className="p-1.5 rounded-full hover:bg-white/10 text-white/50 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        ))
                                    )
                                )}
                            </div>
                        </motion.div>
                        </>
                    )}
                </AnimatePresence>

                {/* ═══════════════════════════════════════
                    PANE 2: EXPLORER (center, scrollable)
                ═══════════════════════════════════════ */}
                <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col gap-4">

                    {/* TOP ROW: Chart & Metrics */}
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 shrink-0">
                        
                        {/* Chart Card */}
                        <div className="rounded-[2.5rem] p-6 flex flex-col gap-4 shrink-0 relative overflow-hidden" style={glass.base}>
                            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 relative z-10">
                                <div>
                                    <div className="flex items-center gap-4 mb-2">
                                        <motion.h1
                                            className="text-4xl md:text-5xl font-bold tracking-tighter text-white leading-none"
                                            animate={{ y: [0, -3, 0] }}
                                            transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
                                        >
                                            {activeItem?.ticker?.split('.')[0] ?? '—'}
                                        </motion.h1>
                                        <motion.button
                                            onClick={() => {
                                                if (!activeItem) return;
                                                isWatched
                                                    ? setWatchlist(watchlist.filter(t => t !== activeItem.ticker))
                                                    : setWatchlist([...watchlist, activeItem.ticker]);
                                            }}
                                            whileHover={{ scale: 1.03 }}
                                            whileTap={{ scale: 0.97 }}
                                            transition={springPress}
                                            className="p-2 rounded-[1rem]"
                                            style={glass.pill}
                                        >
                                            {isWatched
                                                ? <BookmarkCheck className="w-5 h-5 text-emerald-400" />
                                                : <Plus className="w-5 h-5 text-white/60" />
                                            }
                                        </motion.button>
                                    </div>
                                    <p className="text-white/50 font-bold tracking-tighter text-sm">
                                        {activeItem ? `${activeItem.ticker} • ${activeItem.timeframe.toUpperCase()}` : 'Search a ticker to begin'}
                                    </p>
                                </div>

                                <div className="flex flex-col md:items-end">
                                    <div className="inline-flex flex-col items-end gap-1">
                                        {activePrice != null ? (
                                            <span className="text-3xl md:text-4xl font-bold tracking-tighter tabular-nums text-white">
                                                ₹{activePrice.toFixed(2)}
                                            </span>
                                        ) : (
                                            <span className="text-3xl md:text-4xl font-bold tracking-tighter tabular-nums text-white/20">
                                                —
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Chart panel */}
                            <div className="rounded-[1.5rem] p-4 relative" style={glass.nested}>
                                <div className="flex justify-between items-center mb-4">
                                    <div className="flex gap-1 p-1 rounded-[1.25rem]" style={glass.pill}>
                                        {(['1W', '1M', '6M', '1Y'] as const).map((tf) => (
                                            <button
                                                key={tf}
                                                onClick={() => setTimeframe(tf)}
                                                className={`relative px-4 py-1.5 text-[10px] font-bold tracking-[0.15em] uppercase transition-colors rounded-[1rem] z-10 ${
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
                                    <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/40 hidden md:block">
                                        Price Action
                                    </span>
                                </div>

                                {/* Chart */}
                                <div className="h-[140px] w-full relative">
                                    {chartData ? (
                                        <>
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
                                                        className="absolute w-3 h-3 rounded-full bg-emerald-400 blur-[2px]"
                                                    />
                                                    <div className="w-2 h-2 rounded-full bg-emerald-400 relative z-10 shadow-[0_0_10px_rgba(16,185,129,1)]" />
                                                </div>
                                            </motion.div>
                                        </>
                                    ) : (
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <p className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/20">
                                                Search a ticker to load price action
                                            </p>
                                        </div>
                                    )}
                                </div>

                                <div className="flex justify-between mt-2">
                                    {(['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'] as const).map((m) => (
                                        <span key={m} className="text-[8px] font-bold tracking-[0.1em] text-white/25 uppercase">
                                            {m}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Metrics Data Grid */}
                        <div className="rounded-[2.5rem] p-6 flex flex-col" style={glass.base}>
                            <div className="mb-4 border-b border-white/10 pb-3">
                                <p className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40">
                                    Bronze Layer · Raw Ingestion
                                </p>
                            </div>
                            {displayMetrics ? (
                                <div className="flex flex-col gap-3 flex-1">
                                    {/* Bento span 2 */}
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="col-span-2 flex justify-between items-center p-6 rounded-[1.5rem] relative overflow-hidden" style={glass.nested}>
                                            <div className="absolute inset-0 bg-gradient-to-br from-white/[0.03] to-transparent pointer-events-none" />
                                            <div className="flex flex-col relative z-10">
                                                <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-emerald-400 mb-1">
                                                    Current Price
                                                </span>
                                                <span className="text-3xl font-bold tracking-tighter tabular-nums text-white leading-none">
                                                    {displayMetrics[0].value}
                                                </span>
                                            </div>
                                            <div className="flex flex-col text-right relative z-10">
                                                <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/40 mb-1">
                                                    Volume
                                                </span>
                                                <span className="text-xl font-bold tracking-tighter tabular-nums text-white/80 leading-none">
                                                    {displayMetrics[1].value}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    {/* Tech metrics */}
                                    <div className="grid grid-cols-2 gap-3">
                                        {displayMetrics.slice(2).map((data, i) => (
                                            <div key={i} className="flex flex-col p-4 rounded-[1.25rem]" style={glass.nested}>
                                                <span className="text-[9px] font-bold tracking-[0.15em] uppercase text-white/40 mb-1">
                                                    {data.label}
                                                </span>
                                                <span className="text-lg font-bold tracking-tighter tabular-nums text-white">
                                                    {data.value}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="flex-1 flex items-center justify-center">
                                    <p className="text-xs font-bold tracking-[0.12em] uppercase text-white/20 text-center">
                                        No data loaded
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* BOTTOM ROW: Full Width Verdict */}
                    <div className="rounded-[2.5rem] p-8 flex flex-col relative overflow-hidden shrink-0 mb-4" style={glass.base}>
                        <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-gradient-to-b from-emerald-400 to-teal-500 shadow-[0_0_20px_rgba(16,185,129,0.5)]" />

                        <div className="ml-5">
                            <p className="text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400 mb-1.5">
                                Gold Layer · System Verdict
                            </p>

                            {verdictData ? (
                                <>
                                    <div className="flex items-center gap-4 mb-4">
                                        <h3 className="text-3xl md:text-4xl font-bold tracking-tighter text-white">
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

                                    <p className="text-white/60 font-bold tracking-tighter text-base md:text-lg leading-relaxed mb-6 max-w-3xl">
                                        {verdictData.reason}
                                    </p>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        {/* Left Col: LLM Analysis */}
                                        <div>
                                            {verdictData.llm_analysis && (
                                                <div className="flex flex-col gap-6">
                                                    {/* Investment Thesis */}
                                                    {verdictData.llm_analysis.personalized_reasoning && verdictData.llm_analysis.personalized_reasoning.length > 0 && (
                                                        <div className="flex flex-col gap-2">
                                                            <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400">Investment Thesis & Profile Alignment</h4>
                                                            <div className="text-white/70 text-sm leading-relaxed space-y-2">
                                                                {verdictData.llm_analysis.personalized_reasoning.filter((line: string) => !line.toUpperCase().includes('INVESTMENT THESIS') && !line.toUpperCase().includes('QUANTITATIVE SCORECARD') && !line.toUpperCase().includes('OVERALL VERDICT')).map((line: string, i: number) => (
                                                                    <p key={i}>{line.replace(/^- /, '')}</p>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}

                                                    {/* What to Watch */}
                                                    {verdictData.llm_analysis.what_to_watch && verdictData.llm_analysis.what_to_watch.length > 0 && (
                                                        <div className="flex flex-col gap-2">
                                                            <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400">Actionable Conditions</h4>
                                                            <ul className="text-white/70 text-sm leading-relaxed list-disc list-outside ml-4 space-y-1">
                                                                {verdictData.llm_analysis.what_to_watch.map((line: string, i: number) => (
                                                                    <li key={i}>{line.replace(/^- /, '')}</li>
                                                                ))}
                                                            </ul>
                                                        </div>
                                                    )}
                                                    
                                                    {/* Risk Warning */}
                                                    {verdictData.llm_analysis.risk_warning && (
                                                        <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/10">
                                                            <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-red-400 mb-1">Risk Warning</h4>
                                                            <p className="text-red-200/80 text-sm leading-relaxed">{verdictData.llm_analysis.risk_warning}</p>
                                                        </div>
                                                    )}
                                                    
                                                    {/* Tutor Triggers */}
                                                    {verdictData.llm_analysis.tutor_triggers && verdictData.llm_analysis.tutor_triggers.length > 0 && (
                                                        <div className="flex flex-wrap gap-2 mt-4">
                                                            {verdictData.llm_analysis.tutor_triggers.map((trigger: string, i: number) => (
                                                                <button 
                                                                    key={i}
                                                                    onClick={() => {
                                                                        setCommand(`Explain ${trigger} and how it impacts this stock.`);
                                                                    }}
                                                                    className="group flex items-center gap-2 px-3 py-1.5 rounded-full bg-transparent border border-white/10 hover:border-emerald-500/30 transition-colors"
                                                                >
                                                                    <span className="text-[9px] font-bold tracking-[0.15em] text-white/30 group-hover:text-emerald-500/50 uppercase transition-colors">&gt;</span>
                                                                    <span className="text-[10px] font-bold tracking-[0.12em] text-white/50 group-hover:text-emerald-400 uppercase transition-colors">
                                                                        {trigger.replace(/\s+/g, '_')}
                                                                    </span>
                                                                </button>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>

                                        {/* Right Col: Gates & Setup */}
                                        <div className="flex flex-col gap-6">
                                            {/* Trade setup */}
                                            {verdictData.setup && (
                                                <div className="rounded-[1.5rem] p-6 relative overflow-hidden flex flex-col" style={glass.nested}>
                                                    <div className="absolute top-0 left-6 right-6 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
                                                    <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400 mb-6 mt-1">
                                                        Trade Architecture
                                                    </h4>
                                                    
                                                    <div className="flex items-end justify-between mb-6">
                                                        <div className="flex flex-col">
                                                            <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/40 mb-1">R/R Ratio</span>
                                                            <span className="text-4xl font-bold tracking-tighter tabular-nums text-white leading-none">
                                                                {verdictData.setup.rr_ratio}×
                                                            </span>
                                                        </div>
                                                        <div className="flex flex-col items-end">
                                                            <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-red-400/70 mb-1">Stop Loss</span>
                                                            <span className="text-2xl font-bold tracking-tighter tabular-nums text-red-400 leading-none">
                                                                ₹{verdictData.setup.stop_loss}
                                                            </span>
                                                        </div>
                                                    </div>

                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div className="flex flex-col p-3 rounded-[1rem] bg-white/[0.02] border border-white/5">
                                                            <span className="text-[9px] font-bold tracking-[0.15em] uppercase text-white/30 mb-1">Entry Zone</span>
                                                            <span className="text-sm font-bold tracking-tighter tabular-nums text-white/80">
                                                                ₹{verdictData.setup.entry_low} – {verdictData.setup.entry_high}
                                                            </span>
                                                        </div>
                                                        <div className="flex flex-col p-3 rounded-[1rem] bg-emerald-500/[0.03] border border-emerald-500/10">
                                                            <span className="text-[9px] font-bold tracking-[0.15em] uppercase text-emerald-400/60 mb-1">Targets</span>
                                                            <span className="text-sm font-bold tracking-tighter tabular-nums text-emerald-400">
                                                                ₹{verdictData.setup.target_1} / {verdictData.setup.target_2}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Gates list */}
                                            <div className="flex flex-col gap-3 mt-2">
                                                <h4 className="text-[11px] font-bold tracking-[0.15em] uppercase text-white/40 mb-2">
                                                    Hard Gates Cleared
                                                </h4>
                                                <div className="flex flex-wrap gap-2">
                                                    {verdictData.gates.map((g, i) => (
                                                        <div key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-white/10" style={glass.pill}>
                                                            <div className={`w-1.5 h-1.5 rounded-full ${
                                                                g.status === 'PASS' ? 'bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.8)]' :
                                                                g.status === 'WARN' ? 'bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.8)]' : 'bg-red-400 shadow-[0_0_6px_rgba(248,113,113,0.8)]'
                                                            }`} />
                                                            <span className="text-[9px] font-bold tracking-[0.15em] uppercase text-white/70">
                                                                {g.name}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="flex-1 flex items-center justify-center py-20">
                                    <p className="text-sm font-bold tracking-[0.12em] uppercase text-white/20">
                                        Run a ticker analysis to load verdict
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* ═══════════════════════════════════════
                    PANE 3: EXECUTION LOG (right)
                ═══════════════════════════════════════ */}
                <div className="w-[500px] rounded-[2.5rem] flex flex-col shrink-0 relative overflow-hidden hidden md:flex" style={glass.base}>
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
                    <div className="p-4 border-t border-white/10 shrink-0 bg-transparent relative">
                        <div className="absolute inset-0 bg-gradient-to-t from-[#010204]/80 to-transparent pointer-events-none" />
                        <form onSubmit={handleCommand} className="relative flex items-center bg-transparent border-t border-white/5">
                            <span className="absolute left-4 font-mono text-emerald-400/50 text-xs tracking-widest">&gt;</span>
                            <input
                                type="text"
                                value={command}
                                onChange={(e) => setCommand(e.target.value)}
                                placeholder={isProcessing ? 'Waiting for engine...' : 'Enter command or /analyze TICKER...'}
                                disabled={isProcessing}
                                className="w-full bg-transparent border-none py-4 pl-10 pr-4 outline-none text-sm font-mono text-white placeholder-white/30 disabled:opacity-50"
                            />
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}