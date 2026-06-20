import { useRef } from 'react';
import { motion, useMotionValue, useTransform, useSpring } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { ArrowRight } from 'lucide-react';

// ==========================================
// 1. THREE.JS: Continuous Market Data Stream
// ==========================================
function DataPoints() {
    const pointsRef = useRef<any>();

    // INCREASED VISIBILITY: More points, larger distribution
    const count = 2500;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 35;
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
                <bufferAttribute
                    attach="attributes-position"
                    count={count}
                    array={positions}
                    itemSize={3}
                />
            </bufferGeometry>
            {/* INCREASED VISIBILITY: Larger size, higher opacity */}
            <pointsMaterial size={0.045} color="#10B981" transparent opacity={0.8} sizeAttenuation />
        </points>
    );
}

// ==========================================
// 2. MAIN LANDING COMPONENT
// ==========================================
export default function Landing() {
    const navigate = useNavigate();

    // 3D Tilt Effect for the Hero Card
    const x = useMotionValue(0);
    const y = useMotionValue(0);
    const mouseXSpring = useSpring(x, { stiffness: 150, damping: 20 });
    const mouseYSpring = useSpring(y, { stiffness: 150, damping: 20 });
    const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ["10deg", "-10deg"]);
    const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ["-10deg", "10deg"]);

    const handleMouseMove = (e: React.MouseEvent) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        const xPct = mouseX / width - 0.5;
        const yPct = mouseY / height - 0.5;
        x.set(xPct);
        y.set(yPct);
    };

    const handleMouseLeave = () => {
        x.set(0);
        y.set(0);
    };

    return (
        <div className="relative w-full min-h-screen bg-[#030508] text-white overflow-hidden">
            {/* =========================================
                FIXED BACKGROUNDS (Stays during entire scroll)
            ============================================= */}
            <div className="fixed inset-0 z-0 bg-grid pointer-events-none opacity-50" />
            <div className="fixed inset-0 z-0 mix-blend-screen pointer-events-none">
                <Canvas camera={{ position: [0, 0, 5] }}>
                    <DataPoints />
                </Canvas>
            </div>

            {/* Adjusted Ambient Glows to pure Teal/Emerald (No blues/purples) */}
            <div className="fixed top-[-10%] right-[-5%] w-[800px] h-[800px] bg-emerald-500/10 rounded-full blur-[150px] pointer-events-none" />
            <div className="fixed bottom-[-10%] left-[-5%] w-[600px] h-[600px] bg-teal-500/10 rounded-full blur-[150px] pointer-events-none" />

            {/* =========================================
                TOP NAVIGATION
            ============================================= */}
            <nav className="absolute top-0 w-full px-8 md:px-16 py-8 flex justify-between items-center z-50">
                <div className="font-sans font-bold text-2xl tracking-tighter text-white flex items-center gap-2">
                    INVR<span className="text-emerald-500">.</span>
                </div>
                <div className="hidden md:flex gap-8 text-sm font-medium text-white/50">
                    <span className="hover:text-white cursor-pointer transition-colors tracking-tight">Features</span>
                    <span className="hover:text-white cursor-pointer transition-colors tracking-tight">Methodology</span>
                    <span className="hover:text-white cursor-pointer transition-colors tracking-tight">How it Works</span>
                </div>
                <button className="hidden md:block px-6 py-2.5 text-sm font-bold tracking-tight rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors backdrop-blur-md">
                    Client Login
                </button>
            </nav>

            {/* =========================================
                SECTION 1: HERO (100vh)
            ============================================= */}
            <section className="relative z-10 w-full min-h-screen flex items-center pt-20">
                <div className="w-full max-w-7xl mx-auto px-8 md:px-16 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

                    {/* LEFT COLUMN: Hero Copy */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className="flex flex-col items-start text-left"
                    >
                        {/* Synchronized Typography */}
                        <h1 className="text-5xl md:text-[5.5rem] font-bold tracking-tighter mb-6 leading-[1.02] text-white">
                            Structured <br />
                            <span className="text-gradient-finance">Intelligence</span> for <br />
                            Modern Investors.
                        </h1>

                        <p className="text-white/60 font-medium mb-10 text-lg md:text-xl tracking-tight max-w-md leading-relaxed">
                            Privacy-aware, personalized stock analysis and contextual financial education without
                            linking your brokerage accounts.
                        </p>

                        <div className="flex flex-col gap-6">
                            <div className="flex items-center gap-4">
                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => navigate('/onboarding')}
                                    className="px-8 py-4 rounded-xl bg-white text-black font-bold tracking-tight flex items-center gap-3 hover:bg-gray-100 transition-colors shadow-[0_0_30px_rgba(255,255,255,0.1)]"
                                >
                                    Deploy Engine
                                    <ArrowRight className="w-4 h-4" strokeWidth={2.5} />
                                </motion.button>

                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    className="px-8 py-4 rounded-xl bg-transparent border border-white/10 text-white font-bold tracking-tight hover:bg-white/5 transition-colors backdrop-blur-md"
                                >
                                    Explore Methodology
                                </motion.button>
                            </div>

                            {/* Upgraded Seamless AI Badge */}
                            <div className="flex items-center gap-2 text-[11px] font-bold tracking-widest uppercase text-white/40 mt-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                <span>Quantitative Execution • Zero Hallucination</span>
                            </div>
                        </div>
                    </motion.div>

                    {/* RIGHT COLUMN: Interactive Dashboard Card */}
                    <div
                        className="hidden lg:flex justify-center items-center perspective-1000"
                        onMouseMove={handleMouseMove}
                        onMouseLeave={handleMouseLeave}
                    >
                        <motion.div
                            style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
                            className="relative w-full max-w-[520px]"
                        >
                            <div className="glass-panel p-8 rounded-3xl border-t border-t-white/20 shadow-[0_40px_80px_-20px_rgba(0,0,0,1)]">

                                {/* Header */}
                                <div className="flex justify-between items-center mb-8">
                                    <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
                                        <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                                        {/* Synchronized Font */}
                                        <span className="text-[10px] font-bold tracking-tighter text-white uppercase">
                                            Live Analysis
                                        </span>
                                    </div>
                                    <span className="text-xs font-mono text-white/40 tabular-nums">15 Apr 2026</span>
                                </div>

                                {/* Stock Info */}
                                <div className="flex justify-between items-start mb-8">
                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            {/* Synchronized Font */}
                                            <h3 className="text-4xl font-bold tracking-tighter text-white">
                                                RELIANCE
                                            </h3>
                                            <span className="text-sm font-mono text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2 py-0.5 rounded font-medium">
                                                +2.34%
                                            </span>
                                        </div>
                                        {/* Synchronized Font */}
                                        <p className="text-sm text-white/50 font-medium tracking-tight">
                                            Reliance Industries Ltd • NSE
                                        </p>
                                    </div>
                                    <div className="w-16 h-16 rounded-full border-2 border-emerald-500/20 flex items-center justify-center relative bg-obsidian-900/50 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                                        <svg className="absolute inset-0 w-full h-full -rotate-90">
                                            <circle
                                                cx="30"
                                                cy="30"
                                                r="30"
                                                fill="none"
                                                stroke="#10B981"
                                                strokeWidth="2.5"
                                                strokeDasharray="188"
                                                strokeDashoffset="40"
                                            />
                                        </svg>
                                        <span className="font-bold tracking-tighter text-xl text-white">7.8</span>
                                    </div>
                                </div>

                                {/* Animated Chart */}
                                <div className="mb-8">
                                    <div className="flex justify-between text-[11px] font-bold tracking-tighter text-white/40 mb-3 uppercase">
                                        <span>Price Action • 6M</span>
                                        <span className="font-mono tracking-normal text-white/70">₹2,847.50</span>
                                    </div>
                                    <div className="h-32 w-full relative">
                                        <svg
                                            viewBox="0 0 400 100"
                                            className="w-full h-full overflow-visible preserve-3d"
                                            preserveAspectRatio="none"
                                        >
                                            <defs>
                                                <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                                                    <stop offset="0%" stopColor="#0D9488" />
                                                    <stop offset="100%" stopColor="#10B981" />
                                                </linearGradient>
                                            </defs>
                                            {/* Animated Line Drawing */}
                                            <motion.path
                                                d="M0,80 Q50,70 100,85 T200,50 T300,30 T400,20"
                                                fill="none"
                                                stroke="url(#lineGrad)"
                                                strokeWidth="3.5"
                                                strokeLinecap="round"
                                                initial={{ pathLength: 0 }}
                                                animate={{ pathLength: 1 }}
                                                transition={{ duration: 2, ease: "easeInOut", delay: 0.5 }}
                                            />
                                        </svg>

                                        {/* Live Pulsing Market Dot */}
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            transition={{ delay: 2.3 }}
                                            className="absolute right-[0%] top-[12%] flex items-center gap-2 -translate-y-1/2 translate-x-1/2"
                                        >
                                            <div className="relative flex items-center justify-center">
                                                <motion.div
                                                    animate={{ scale: [1, 2.5, 1], opacity: [0.8, 0, 0.8] }}
                                                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                                                    className="absolute w-4 h-4 rounded-full bg-emerald-400"
                                                />
                                                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 relative z-10 shadow-[0_0_10px_rgba(16,185,129,1)]" />
                                            </div>
                                        </motion.div>
                                    </div>
                                </div>

                                {/* Integrated Text Verdict */}
                                <div
                                    className="mt-6 pl-5 border-l-2 border-emerald-500/50 relative"
                                    style={{ transform: "translateZ(30px)" }}
                                >
                                    <div className="absolute -left-[5px] top-0 w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]" />
                                    {/* Synchronized Font */}
                                    <h4 className="text-[11px] font-bold text-emerald-400 tracking-tighter uppercase mb-2">
                                        System Verdict
                                    </h4>
                                    {/* Synchronized Font */}
                                    <p className="text-sm text-white/70 font-medium tracking-tight leading-relaxed">
                                        Strong P/E ratio indicates deep undervaluation. Momentum setup perfectly aligns
                                        with your stated wealth growth profile.
                                    </p>
                                </div>

                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* =========================================
                SECTION 2: EDITORIAL BENTO GRID (Scrollable)
            ============================================= */}
            <section className="relative z-10 w-full min-h-screen py-32 flex flex-col items-center justify-center border-t border-white/5 bg-gradient-to-b from-transparent to-[#030508]">
                <div className="max-w-7xl mx-auto px-8 md:px-16 w-full">

                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-100px" }}
                        className="mb-20"
                    >
                        <h2 className="text-5xl md:text-7xl font-bold tracking-tighter text-white mb-6 leading-[1.05]">
                            Precision engineering.<br />
                            <span className="text-white/40">Zero speculation.</span>
                        </h2>
                    </motion.div>

                    {/* Bento Grid Architecture (No Generic Alternating Blocks) */}
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-6">

                        {/* BLOCK 1: Institutional Math (Wide) */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-50px" }}
                            className="col-span-1 md:col-span-8 glass-panel p-10 md:p-12 rounded-3xl border-t border-white/10 relative overflow-hidden group"
                        >
                            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-[100px] -mr-40 -mt-40 transition-opacity" />

                            <h3 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tighter">Institutional Math.</h3>
                            <p className="text-white/50 text-lg leading-relaxed max-w-xl font-medium tracking-tight">
                                Our system computes millions of data points across price action, fundamentals, and relative strength to deliver definitive trade setups. The exact quantitative edge used by top-tier funds.
                            </p>

                            {/* Programmatic Data Matrix Visual (No Generic Icons) */}
                            <div className="mt-12 h-32 w-full border-t border-white/10 pt-6 flex items-end gap-1.5 opacity-50">
                                {[...Array(30)].map((_, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ height: "10%" }}
                                        animate={{ height: `${20 + Math.random() * 80}%` }}
                                        transition={{ duration: 1.5 + Math.random() * 2, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
                                        className="flex-1 bg-emerald-500/30 rounded-t-sm"
                                    />
                                ))}
                            </div>
                        </motion.div>

                        {/* BLOCK 2: Absolute Privacy (Square) */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-50px" }}
                            transition={{ delay: 0.1 }}
                            className="col-span-1 md:col-span-4 glass-panel p-10 md:p-12 rounded-3xl border-t border-white/10 relative overflow-hidden"
                        >
                            <div className="absolute bottom-0 left-0 w-full h-1/2 bg-teal-500/5 blur-[50px]" />

                            <h3 className="text-4xl font-bold text-white mb-6 tracking-tighter leading-[1.05]">Absolute<br />Privacy.</h3>
                            <p className="text-white/50 text-lg leading-relaxed font-medium tracking-tight">
                                Zero broker links. Your portfolio macro allocation stays on your device. We evaluate the market, not your identity.
                            </p>

                            {/* Cryptographic Hash Visual (No Generic Shields) */}
                            <div className="mt-10 font-mono text-xs text-teal-500/40 break-all leading-loose opacity-60">
                                0x9a8f4c2<br />
                                [LOCAL_ENV_LOCK]<br />
                                PORTFOLIO_STATE=SECURE<br />
                                0x11f9a8f
                            </div>
                        </motion.div>

                        {/* BLOCK 3: Deterministic Execution (Full Width) */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-50px" }}
                            transition={{ delay: 0.2 }}
                            className="col-span-1 md:col-span-12 glass-panel p-10 md:p-16 rounded-3xl border-t border-white/10 relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-12"
                        >
                            <div className="flex-1">
                                <h3 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tighter leading-[1.05]">
                                    Emotional detachment<br />
                                    <span className="text-white/40">by design.</span>
                                </h3>
                                <p className="text-white/50 text-lg leading-relaxed font-medium tracking-tight max-w-2xl">
                                    The engine evaluates hard-gates across fundamentals, relative strength, and price action. If a setup fails the math, it is blocked. No exceptions. No hallucinations.
                                </p>
                            </div>

                            {/* Structural Logic Visual (No Solar Systems) */}
                            <div className="flex-1 w-full relative h-full flex flex-col justify-center items-end opacity-80 gap-4">
                                <div className="w-full max-w-md">
                                    <div className="flex justify-between text-[10px] font-bold tracking-widest uppercase text-white/40 mb-2">
                                        <span>Valuation Gate</span>
                                        <span className="text-emerald-400">Pass</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                        <motion.div className="h-full bg-emerald-500" initial={{ width: 0 }} whileInView={{ width: "100%" }} transition={{ duration: 1.5, delay: 0.2 }} />
                                    </div>
                                </div>
                                <div className="w-full max-w-md">
                                    <div className="flex justify-between text-[10px] font-bold tracking-widest uppercase text-white/40 mb-2">
                                        <span>Momentum Convergence</span>
                                        <span className="text-emerald-400">Pass</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                        <motion.div className="h-full bg-emerald-500" initial={{ width: 0 }} whileInView={{ width: "100%" }} transition={{ duration: 1.5, delay: 0.4 }} />
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                    </div>
                </div>
            </section>

        </div>
    );
}
