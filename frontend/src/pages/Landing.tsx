import { useRef, useState } from 'react';
import { motion, AnimatePresence, useMotionValue, useTransform, useSpring, useScroll } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { ArrowRight, Menu, X } from 'lucide-react';

// ==========================================
// GLASS STYLE SYSTEM
// Layered optical glass — specular top/left
// highlight, dark bottom/right edge shadow,
// saturated blur for true refraction depth.
// ==========================================
const glass = {
    base: {
        background: 'linear-gradient(145deg, rgba(255,255,255,0.09) 0%, rgba(255,255,255,0.028) 100%)',
        backdropFilter: 'blur(72px) saturate(200%) brightness(108%)',
        WebkitBackdropFilter: 'blur(72px) saturate(200%) brightness(108%)',
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
        background: 'linear-gradient(145deg, rgba(255,255,255,0.09) 0%, rgba(255,255,255,0.028) 100%)',
        backdropFilter: 'blur(72px) saturate(200%) brightness(108%)',
        WebkitBackdropFilter: 'blur(72px) saturate(200%) brightness(108%)',
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

    pill: {
        background: 'linear-gradient(145deg, rgba(255,255,255,0.09) 0%, rgba(255,255,255,0.028) 100%)',
        backdropFilter: 'blur(72px) saturate(200%) brightness(108%)',
        WebkitBackdropFilter: 'blur(72px) saturate(200%) brightness(108%)',
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
};

// Shared physics curve — every hover/tap in the page pulls from this
// single spring so the whole UI feels like one consistent material.
const springPress = { type: 'spring', stiffness: 420, damping: 26, mass: 0.6 } as const;
const springSoft = { type: 'spring', stiffness: 220, damping: 28, mass: 0.9 } as const;

// ==========================================
// PRICE SERIES — six months of (illustrative)
// price action with real drawdowns and a
// recovery leg, not a single smooth arc.
// ==========================================
const RELIANCE_PRICES = [
    2652, 2638, 2671, 2659, 2694, 2683, 2705, 2691,
    2718, 2702, 2734, 2712, 2696, 2671, 2648, 2665,
    2689, 2716, 2748, 2731, 2709, 2742, 2771, 2758,
    2733, 2761, 2789, 2774, 2802, 2826, 2811, 2793,
    2818, 2841, 2829, 2847.5,
];
const CHART_MONTH_LABELS = ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'];
const CHART_W = 400;
const CHART_H = 96;
const CHART_PAD = 8;

// Maps a raw price series into the chart's coordinate space, then
// smooths it through a Catmull-Rom-to-Bezier spline so the line reads
// as continuous price action rather than a single decorative swoop.
function buildPriceChart(prices: number[]) {
    const min = Math.min(...prices);
    const max = Math.max(...prices);
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

const PRICE_CHART = buildPriceChart(RELIANCE_PRICES);

// ==========================================
// 1. THREE.JS: Continuous Market Data Stream
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
            <pointsMaterial size={0.045} color="#10B981" transparent opacity={0.8} sizeAttenuation />
        </points>
    );
}

// ==========================================
// 2. MAIN LANDING COMPONENT
// ==========================================
export default function Landing() {
    const navigate = useNavigate();

    const navItems = ['Features', 'Methodology', 'How it Works'];
    const [activeNav, setActiveNav] = useState(0);
    const [mobileOpen, setMobileOpen] = useState(false);

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

    // Page-level scroll progress — drives the nav surface and the
    // hero's gentle compression as the page is read.
    const { scrollYProgress: pageScroll } = useScroll();
    const navSurface = useTransform(pageScroll, [0, 0.04], [0, 1]);
    const heroOpacity = useTransform(pageScroll, [0, 0.1], [1, 0.55]);
    const heroScale = useTransform(pageScroll, [0, 0.1], [1, 0.97]);
    const heroY = useTransform(pageScroll, [0, 0.1], [0, -24]);

    // Scroll Animation for the Narrative Lineage
    const narrativeRef = useRef(null);
    const { scrollYProgress } = useScroll({
        target: narrativeRef,
        offset: ["start center", "end center"],
    });

    const orbY = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);
    const orbScale = useTransform(scrollYProgress, [0, 0.5, 1], [1, 1.5, 1]);

    // Class names spelled out in full per phase (not interpolated) so
    // Tailwind's JIT compiler can actually discover and generate them.
    const phases = [
        {
            num: '01',
            eyebrow: 'Phase 01 / The Discovery',
            title: 'Curiosity meets computation.',
            body:
                "Cut through the noise. Stop scrolling social feeds hoping for conviction. Input a ticker and watch the engine instantly dissect decades of SEC filings, historical price action, and institutional flow in milliseconds.",
            align: 'self-start' as const,
            edgeClass: 'absolute -left-12 top-10 w-24 h-[1px] bg-emerald-500/20 hidden md:block',
            eyebrowClass: 'text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400 mb-1.5',
        },
        {
            num: '02',
            eyebrow: 'Phase 02 / The Interrogation',
            title: 'Emotional detachment by design.',
            body:
                "No bias. No bags. The system ruthlessly forces the asset through strict quantitative hard-gates — comparing trailing valuations, momentum convergence, and sector relative strength against absolute market medians.",
            align: 'self-end' as const,
            edgeClass: 'absolute -right-12 top-10 w-24 h-[1px] bg-teal-500/20 hidden md:block',
            eyebrowClass: 'text-[11px] font-bold tracking-[0.15em] uppercase text-teal-400 mb-1.5',
        },
        {
            num: '03',
            eyebrow: 'Phase 03 / The Execution',
            title: 'Execute with conviction.',
            body:
                "Receive a crystal-clear, deterministic verdict. Know your exact entry parameters, understand the mathematical risk vector, and deploy your capital like a top-tier institutional fund. Get it done.",
            align: 'self-start' as const,
            edgeClass: 'absolute -left-12 top-10 w-24 h-[1px] bg-emerald-500/20 hidden md:block',
            eyebrowClass: 'text-[11px] font-bold tracking-[0.15em] uppercase text-emerald-400 mb-1.5',
        },
    ];

    return (
        <div className="relative w-full min-h-screen bg-[#030508] text-white overflow-hidden font-sans">
            {/* =========================================
          FIXED BACKGROUNDS — organic, breathing,
          never a static dead layer.
      ============================================= */}
            <div className="fixed inset-0 z-0 bg-grid pointer-events-none opacity-50" />
            <div className="fixed inset-0 z-0 mix-blend-screen pointer-events-none">
                <Canvas camera={{ position: [0, 0, 5] }}>
                    <DataPoints />
                </Canvas>
            </div>

            <motion.div
                className="fixed top-[-10%] right-[-5%] w-[800px] h-[800px] bg-emerald-500/10 blur-[150px] pointer-events-none"
                initial={{ borderRadius: '50%' }}
                animate={{
                    x: [0, 40, -25, 0],
                    y: [0, -30, 20, 0],
                    scale: [1, 1.15, 0.94, 1],
                    borderRadius: ['50%', '42% 58% 60% 40% / 50% 45% 55% 50%', '58% 42% 40% 60% / 45% 55% 45% 55%', '50%'],
                }}
                transition={{ duration: 24, repeat: Infinity, ease: 'easeInOut' }}
            />
            <motion.div
                className="fixed bottom-[-10%] left-[-5%] w-[600px] h-[600px] bg-teal-500/10 blur-[150px] pointer-events-none"
                initial={{ borderRadius: '50%' }}
                animate={{
                    x: [0, -30, 30, 0],
                    y: [0, 25, -25, 0],
                    scale: [1, 0.9, 1.12, 1],
                    borderRadius: ['50%', '60% 40% 38% 62% / 55% 45% 55% 45%', '40% 60% 62% 38% / 45% 55% 45% 55%', '50%'],
                }}
                transition={{ duration: 28, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
            />

            {/* =========================================
          TOP NAVIGATION
      ============================================= */}
            <motion.div
                className="fixed top-0 inset-x-0 h-24 z-40 pointer-events-none"
                style={{
                    opacity: navSurface,
                    background: 'linear-gradient(180deg, rgba(3,5,8,0.7) 0%, rgba(3,5,8,0) 100%)',
                    backdropFilter: 'blur(20px)',
                    WebkitBackdropFilter: 'blur(20px)',
                }}
            />
            <nav className="absolute top-0 w-full px-8 md:px-16 py-8 flex justify-between items-center z-50">
                <div className="font-bold text-2xl tracking-tighter text-white flex items-center gap-2">
                    INVR<span className="text-emerald-500">.</span>
                </div>



                <motion.button
                    onClick={() => navigate('/auth')}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    transition={springPress}
                    className="hidden md:block px-6 py-2.5 text-sm font-bold tracking-tighter rounded-[1rem] hover:bg-white/[0.08] transition-colors text-white"
                    style={glass.pill}
                >
                    Client Login
                </motion.button>

                {/* Mobile trigger */}
                <motion.button
                    whileTap={{ scale: 0.9 }}
                    transition={springPress}
                    onClick={() => setMobileOpen((v) => !v)}
                    className="md:hidden w-11 h-11 flex items-center justify-center rounded-[1rem] text-white"
                    style={glass.pill}
                >
                    <AnimatePresence mode="wait" initial={false}>
                        {mobileOpen ? (
                            <motion.span
                                key="close"
                                initial={{ rotate: -90, opacity: 0 }}
                                animate={{ rotate: 0, opacity: 1 }}
                                exit={{ rotate: 90, opacity: 0 }}
                                transition={springPress}
                            >
                                <X className="w-5 h-5" />
                            </motion.span>
                        ) : (
                            <motion.span
                                key="menu"
                                initial={{ rotate: 90, opacity: 0 }}
                                animate={{ rotate: 0, opacity: 1 }}
                                exit={{ rotate: -90, opacity: 0 }}
                                transition={springPress}
                            >
                                <Menu className="w-5 h-5" />
                            </motion.span>
                        )}
                    </AnimatePresence>
                </motion.button>
            </nav>

            <AnimatePresence>
                {mobileOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -16, scale: 0.96 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -16, scale: 0.96 }}
                        transition={springSoft}
                        className="md:hidden fixed top-24 right-8 z-50 flex flex-col gap-1 p-3 rounded-[1.5rem] min-w-[200px]"
                        style={glass.base}
                    >
                        {navItems.map((item, i) => (
                            <span
                                key={item}
                                onClick={() => {
                                    setActiveNav(i);
                                    setMobileOpen(false);
                                }}
                                className="px-4 py-3 text-sm font-bold tracking-tighter text-white/70 hover:text-white rounded-[1rem] hover:bg-white/[0.06] cursor-pointer transition-colors"
                            >
                                {item}
                            </span>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* =========================================
          SECTION 1: HERO (100vh)
      ============================================= */}
            <section className="relative z-10 w-full min-h-screen flex items-center pt-20">
                <motion.div
                    style={{ opacity: heroOpacity, scale: heroScale, y: heroY }}
                    className="w-full max-w-7xl mx-auto px-8 md:px-16 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center"
                >

                    {/* LEFT COLUMN: Hero Copy */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className="flex flex-col items-start text-left"
                    >
                        <h1 className="text-5xl md:text-[5.5rem] font-bold tracking-tighter mb-6 leading-[1.02] text-white">
                            Structured <br />
                            <motion.span
                                className="text-gradient-finance inline-block"
                                animate={{ y: [0, -5, 0] }}
                                transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
                            >
                                Intelligence
                            </motion.span>{' '}for <br />
                            Modern Investors.
                        </h1>

                        <p className="text-white/60 font-bold tracking-tighter mb-10 text-lg md:text-xl max-w-md leading-relaxed">
                            Privacy-aware, personalized stock analysis and contextual financial education without
                            linking your brokerage accounts.
                        </p>


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
                            <div
                                className="relative overflow-hidden p-8 rounded-[2.5rem]"
                                style={glass.base}
                            >
                                <div className="relative z-10">

                                    <div className="flex justify-between items-center mb-8">
                                        <div
                                            className="flex items-center gap-2 px-3 py-1.5 rounded-full"
                                            style={glass.pill}
                                        >
                                            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                                            <span className="text-[11px] font-bold tracking-tighter text-white uppercase">
                                                Live Analysis
                                            </span>
                                        </div>
                                        <span className="text-xs font-bold tracking-tighter text-white/40 tabular-nums">
                                            15 Apr 2026
                                        </span>
                                    </div>

                                    <div className="flex justify-between items-start mb-8">
                                        <div>
                                            <div className="flex items-center gap-3 mb-1">
                                                <h3 className="text-4xl font-bold tracking-tighter text-white">
                                                    RELIANCE
                                                </h3>
                                                <span
                                                    className="text-sm text-emerald-400 px-2 py-0.5 rounded-[0.5rem] font-bold tracking-tighter border border-emerald-400/15"
                                                    style={{ background: 'rgba(16,185,129,0.06)', backdropFilter: 'blur(12px)' }}
                                                >
                                                    +2.34%
                                                </span>
                                            </div>
                                            <p className="text-sm text-white/50 font-bold tracking-tighter">
                                                Reliance Industries Ltd • NSE
                                            </p>
                                        </div>

                                        <div
                                            className="flex flex-col items-center justify-center px-5 py-3 rounded-[1.25rem]"
                                            style={glass.nested}
                                        >
                                            <span className="font-bold tracking-tighter text-2xl text-white tabular-nums leading-none">
                                                7.8
                                            </span>
                                            <span className="text-[9px] font-bold tracking-[0.15em] text-emerald-400 uppercase mt-1">
                                                Score
                                            </span>
                                        </div>
                                    </div>

                                    <div
                                        className="mb-8 rounded-[1.5rem] p-6"
                                        style={glass.nested}
                                    >
                                        <div className="flex justify-between text-[12px] font-bold tracking-tighter text-white/40 mb-4 uppercase">
                                            <span>Price Action • 6M</span>
                                            <span className="tabular-nums text-white/70">₹2,847.50</span>
                                        </div>
                                        <div className="h-24 w-full relative">
                                            <svg
                                                viewBox={`0 0 ${CHART_W} ${CHART_H}`}
                                                className="w-full h-full overflow-visible"
                                                preserveAspectRatio="none"
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

                                                {/* faint reference lines — just enough to read the
                                                    series against, not a data grid */}
                                                {[0.25, 0.5, 0.75].map((f) => (
                                                    <line
                                                        key={f}
                                                        x1="0"
                                                        x2={CHART_W}
                                                        y1={CHART_H * f}
                                                        y2={CHART_H * f}
                                                        stroke="rgba(255,255,255,0.05)"
                                                        strokeWidth="1"
                                                    />
                                                ))}

                                                <motion.path
                                                    d={PRICE_CHART.area}
                                                    fill="url(#areaGrad)"
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    transition={{ duration: 1, delay: 1.7 }}
                                                />

                                                <motion.path
                                                    d={PRICE_CHART.line}
                                                    fill="none"
                                                    stroke="url(#lineGrad)"
                                                    strokeWidth="2.5"
                                                    strokeLinecap="round"
                                                    initial={{ pathLength: 0 }}
                                                    animate={{ pathLength: 1 }}
                                                    transition={{ duration: 2, ease: "easeInOut", delay: 0.5 }}
                                                    className="drop-shadow-[0_4px_12px_rgba(16,185,129,0.3)]"
                                                />
                                            </svg>

                                            <motion.div
                                                initial={{ opacity: 0, scale: 0 }}
                                                animate={{ opacity: 1, scale: 1 }}
                                                transition={{ delay: 2.3 }}
                                                style={{
                                                    left: `${(PRICE_CHART.last.x / CHART_W) * 100}%`,
                                                    top: `${(PRICE_CHART.last.y / CHART_H) * 100}%`,
                                                }}
                                                className="absolute -translate-y-1/2 -translate-x-1/2"
                                            >
                                                <div className="relative flex items-center justify-center">
                                                    <motion.div
                                                        animate={{ scale: [1, 2.5, 1], opacity: [0.8, 0, 0.8] }}
                                                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                                                        className="absolute w-4 h-4 rounded-full bg-emerald-400 blur-[2px]"
                                                    />
                                                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 relative z-10 shadow-[0_0_10px_rgba(16,185,129,1)]" />
                                                </div>
                                            </motion.div>
                                        </div>

                                        <div className="flex justify-between mt-3">
                                            {CHART_MONTH_LABELS.map((m) => (
                                                <span
                                                    key={m}
                                                    className="text-[9px] font-bold tracking-[0.1em] text-white/25 uppercase"
                                                >
                                                    {m}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <div
                                        className="rounded-[1.5rem] p-6 relative overflow-hidden"
                                        style={{ ...glass.nested, transform: "translateZ(30px)" }}
                                    >
                                        <div className="absolute top-0 left-8 right-8 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
                                        <p className="text-[10px] font-bold tracking-[0.18em] text-emerald-400 uppercase mb-2.5">
                                            System Verdict
                                        </p>
                                        <p className="text-sm text-white/75 font-bold tracking-tighter leading-relaxed">
                                            Strong P/E ratio indicates deep undervaluation. Momentum setup perfectly aligns
                                            with your stated wealth growth profile.
                                        </p>
                                    </div>

                                </div>
                            </div>
                        </motion.div>
                    </div>
                </motion.div>
            </section>

            {/* =========================================
          SECTION 2: THE LINEAGE JOURNEY
          Numbered phases are a real ordered sequence
          here (Discovery → Interrogation → Execution),
          so the 01/02/03 device is earned, not decorative.
          Each card now carries the number as a giant
          watermark typographic element rather than a
          small icon-in-a-box badge.
      ============================================= */}
            <section
                ref={narrativeRef}
                className="relative z-10 w-full py-32 flex flex-col items-center bg-transparent"
            >
                <div className="text-center mb-32 relative z-20">
                    <h2 className="text-5xl md:text-7xl font-bold tracking-tighter text-white mb-6 leading-[1.05]">
                        Precision engineering.<br />
                        <span className="text-white/40">Zero speculation.</span>
                    </h2>
                    <p className="text-white/50 text-xl max-w-2xl mx-auto font-bold tracking-tighter">
                        The anatomy of a definitive trade. Follow the engine's deterministic lifecycle from raw
                        data ingestion to absolute conviction.
                    </p>
                </div>

                <div className="relative w-full max-w-5xl mx-auto px-8 md:px-16 flex flex-col gap-32 pb-32">

                    <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[1px] bg-white/[0.04] -z-10" />
                    <motion.div
                        style={{ top: orbY, scale: orbScale }}
                        className="absolute left-1/2 -translate-x-1/2 w-[300px] h-[300px] bg-emerald-500/20 rounded-full blur-[100px] -z-10 pointer-events-none"
                    />

                    {phases.map((phase) => (
                        <motion.div
                            key={phase.num}
                            initial={{ opacity: 0, y: 50 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-100px" }}
                            className={`relative w-full md:w-[85%] ${phase.align}`}
                        >
                            <div className={phase.edgeClass} />
                            <div
                                className="p-10 md:p-14 rounded-[2.5rem] relative overflow-hidden"
                                style={glass.nested}
                            >
                                {/* Giant typographic numeral — replaces the
                                    generic icon-in-a-box badge entirely */}
                                <span
                                    aria-hidden="true"
                                    className="absolute -top-6 -left-3 text-[9rem] md:text-[11rem] font-bold leading-none text-white/[0.045] select-none pointer-events-none tracking-tighter"
                                >
                                    {phase.num}
                                </span>

                                <div className="relative z-10">
                                    <p className={phase.eyebrowClass}>
                                        {phase.eyebrow}
                                    </p>
                                    <h3 className="text-3xl font-bold text-white tracking-tighter mb-6 max-w-md">
                                        {phase.title}
                                    </h3>
                                    <p className="text-white/55 text-lg leading-relaxed font-bold tracking-tighter max-w-xl">
                                        {phase.body}
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    ))}

                </div>
            </section>
        </div>
    );
}