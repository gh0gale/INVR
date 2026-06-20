import { useState } from 'react';
import { Search, BookmarkPlus, Activity, TrendingUp, Cpu, MessageSquare } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Workspace() {
    const [activeTimeframe, setActiveTimeframe] = useState('1M');
    const [chatInput, setChatInput] = useState('');

    const metrics = [
        { label: "RSI (14)", value: "48.33", status: "neutral" },
        { label: "Trailing PE", value: "28.40", status: "good" },
        { label: "Volume Ratio", value: "1.85x", status: "excellent" },
        { label: "Sector RS", value: "+2.4%", status: "good" },
        { label: "SMA Gap", value: "-0.5%", status: "warning" },
        { label: "Debt/Equity", value: "0.4", status: "excellent" },
    ];

    return (
        <div className="h-screen w-screen flex flex-col overflow-hidden bg-obsidian-900">

            {/* Omni-Header */}
            <header className="h-16 border-b border-white/5 flex items-center px-6 justify-between bg-obsidian-900/50 backdrop-blur-md z-20">
                <div className="flex items-center gap-4">
                    <div className="w-8 h-8 rounded bg-neon-cyan/20 border border-neon-cyan/50 flex items-center justify-center">
                        <span className="font-mono font-bold text-neon-cyan">I</span>
                    </div>
                    <span className="font-mono font-bold tracking-widest text-lg">INVR</span>
                </div>

                <div className="flex items-center gap-3 w-[400px] glass-panel rounded-lg px-4 py-2 opacity-70 focus-within:opacity-100 transition-opacity">
                    <Search className="w-4 h-4 text-neon-cyan" />
                    <input
                        type="text"
                        placeholder="Search RELIANCE.NS..."
                        className="bg-transparent border-none outline-none w-full text-sm font-mono placeholder:font-sans placeholder:text-gray-600 text-white"
                    />
                </div>

                <div className="w-8" /> {/* Spacer */}
            </header>

            {/* Workspace Grid */}
            <main className="flex-1 grid grid-cols-12 gap-4 p-4 overflow-hidden relative z-10">

                {/* =========================================
            LEFT PANEL (65%): QUANTITATIVE ENGINE 
        ============================================= */}
                <section className="col-span-8 flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2 pb-10">

                    {/* Top Info Banner */}
                    <div className="glass-panel p-8 rounded-2xl relative overflow-hidden group">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-verdict-buy/5 rounded-full blur-[80px] -mr-20 -mt-20 transition-opacity" />

                        <div className="flex justify-between items-start relative z-10">
                            <div>
                                <h2 className="text-4xl font-mono font-bold tracking-tight text-white mb-1">RELIANCE.NS</h2>
                                <p className="text-gray-400 font-light tracking-wide">Reliance Industries Ltd. • Conglomerates</p>
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="px-5 py-2.5 rounded-lg border border-verdict-buy/30 bg-verdict-buy/10 shadow-[0_0_20px_rgba(0,255,163,0.15)] flex items-center gap-2">
                                    <Activity className="w-4 h-4 text-verdict-buy" />
                                    <span className="font-mono font-bold tracking-widest neon-text-buy text-lg">STRONG BUY</span>
                                </div>
                                <button className="p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/5 hover:border-neon-cyan/50 transition-all group-hover:shadow-[0_0_15px_rgba(0,240,255,0.1)]">
                                    <BookmarkPlus className="w-5 h-5 text-gray-400 hover:text-neon-cyan transition-colors" />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Chart Section */}
                    <div className="glass-panel p-6 rounded-2xl flex flex-col">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-sm font-medium text-gray-400 tracking-wider uppercase flex items-center gap-2">
                                <TrendingUp className="w-4 h-4" /> Price Action
                            </h3>
                            <div className="flex gap-1 bg-obsidian-900 p-1 rounded-lg border border-white/5">
                                {['1W', '1M', '3M', '1Y', '5Y'].map(tf => (
                                    <button
                                        key={tf}
                                        onClick={() => setActiveTimeframe(tf)}
                                        className={`px-3 py-1 rounded text-xs font-mono transition-colors ${activeTimeframe === tf ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-gray-300'}`}
                                    >
                                        {tf}
                                    </button>
                                ))}
                            </div>
                        </div>
                        {/* Mock Chart Area (Replace with Recharts LineChart later) */}
                        <div className="h-[280px] w-full border border-dashed border-white/10 rounded-lg flex items-center justify-center bg-gradient-to-t from-verdict-buy/5 to-transparent relative">
                            <svg className="absolute w-full h-full opacity-50" preserveAspectRatio="none" viewBox="0 0 100 100">
                                <path d="M0,80 Q20,20 40,60 T100,30" fill="none" stroke="#00FFA3" strokeWidth="0.5" />
                            </svg>
                            <span className="text-gray-600 font-mono text-sm">[Recharts Canvas Area]</span>
                        </div>
                    </div>

                    {/* Data Matrix */}
                    <div className="glass-panel p-6 rounded-2xl">
                        <h3 className="text-sm font-medium text-gray-400 tracking-wider uppercase flex items-center gap-2 mb-6">
                            <Cpu className="w-4 h-4" /> Medallion Metrics
                        </h3>
                        <div className="grid grid-cols-3 gap-4">
                            {metrics.map((m, i) => (
                                <div key={i} className="group p-4 rounded-xl border border-white/5 bg-white/[0.01] hover:bg-white/[0.03] transition-colors cursor-pointer">
                                    <p className="text-xs text-gray-500 mb-2 font-medium">{m.label}</p>
                                    <p className="text-2xl font-mono text-gray-200 group-hover:text-white transition-colors">{m.value}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>


                {/* =========================================
            RIGHT PANEL (35%): AI SYNTHESIZER 
        ============================================= */}
                <section className="col-span-4 glass-panel rounded-2xl flex flex-col overflow-hidden relative">

                    <div className="p-5 border-b border-white/5 flex items-center gap-3 bg-obsidian-900/50">
                        <MessageSquare className="w-4 h-4 text-neon-magenta" />
                        <h3 className="text-sm font-medium tracking-wide text-gray-200">Logic Synthesizer</h3>
                    </div>

                    {/* Chat Stream Area */}
                    <div className="flex-1 p-6 overflow-y-auto custom-scrollbar flex flex-col gap-6">
                        <div className="text-sm leading-relaxed text-gray-300 font-light">
                            <p className="mb-4">
                                <strong className="text-white font-medium">Trajectory Alignment:</strong> The stock's current consolidation sits directly on the <span className="font-mono text-neon-cyan bg-neon-cyan/10 px-1 rounded">SMA-50</span>, offering a high-probability bounce setup that aligns with your Wealth Growth goal.
                            </p>
                            <p>
                                <strong className="text-white font-medium">Actionable Triggers:</strong> Watch for the <span className="font-mono text-neon-purple bg-neon-purple/10 px-1 rounded">RSI (14)</span> to curl above 50 with a confirmed volume spike exceeding <span className="font-mono text-white bg-white/10 px-1 rounded">1.5x</span> average.
                            </p>
                        </div>

                        {/* Mock User Message */}
                        <div className="self-end bg-white/5 border border-white/10 px-4 py-3 rounded-2xl rounded-tr-sm text-sm text-gray-300 max-w-[85%]">
                            What does the SMA Gap mean here?
                        </div>

                        {/* Mock Typing Indicator */}
                        <motion.div
                            animate={{ opacity: [0.4, 1, 0.4] }}
                            transition={{ duration: 1.5, repeat: Infinity }}
                            className="text-xs font-mono text-neon-magenta flex items-center gap-2"
                        >
                            <div className="w-1.5 h-1.5 rounded-full bg-neon-magenta" /> Interrogating metrics...
                        </motion.div>
                    </div>

                    {/* Input Console */}
                    <div className="p-4 bg-obsidian-900/80 border-t border-white/5 backdrop-blur-md">
                        <div className="relative flex items-center">
                            <input
                                type="text"
                                value={chatInput}
                                onChange={(e) => setChatInput(e.target.value)}
                                placeholder="Query the algorithm..."
                                className="w-full bg-black/50 border border-white/10 rounded-xl pl-4 pr-12 py-3.5 text-sm text-white focus:border-neon-magenta/50 focus:bg-black outline-none transition-all shadow-inner"
                            />
                            <button className="absolute right-3 p-1.5 rounded-md hover:bg-white/10 text-gray-400 hover:text-neon-magenta transition-colors">
                                <svg className="w-4 h-4 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                </svg>
                            </button>
                        </div>
                    </div>

                </section>
            </main>
        </div>
    );
}