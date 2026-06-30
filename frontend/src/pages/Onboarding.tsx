import React, { useState, useRef, useMemo } from 'react';
import { motion, AnimatePresence, useSpring, useTransform } from 'framer-motion';
import { Canvas, useFrame } from '@react-three/fiber';
import { ArrowRight, ArrowLeft, Plus, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// --- 1. DESIGN SYSTEM TOKENS & PHYSICS ---
// Exact three-tier glass system per §4. Alpha values are final — do not increase.

const glass = {
    // Tier 1 — outer card surface
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

    // Tier 2 — nested panels, no backdrop-filter (sits inside an already-blurred surface)
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

// Shared spring physics — defined once, reused everywhere per §6.1
const springPress = { type: 'spring', stiffness: 420, damping: 26, mass: 0.6 } as const;
const springSoft  = { type: 'spring', stiffness: 220, damping: 28, mass: 0.9 } as const;

// --- 2. THREE.JS STARFIELD (§7 layer 2) ---

function Starfield() {
    const pointsRef = useRef<any>(null);

    const particles = useMemo(() => {
        const temp = new Float32Array(2500 * 3);
        for (let i = 0; i < 2500; i++) {
            temp[i * 3]     = (Math.random() - 0.5) * 35;
            temp[i * 3 + 1] = (Math.random() - 0.5) * 20;
            temp[i * 3 + 2] = (Math.random() - 0.5) * 20;
        }
        return temp;
    }, []);

    useFrame(({ clock }) => {
        if (pointsRef.current) {
            pointsRef.current.rotation.y = clock.getElapsedTime() * 0.06;
            pointsRef.current.rotation.z = Math.sin(clock.getElapsedTime() * 0.1) * 0.15;
        }
    });

    return (
        <points ref={pointsRef}>
            <bufferGeometry>
                <bufferAttribute attach="attributes-position" args={[particles, 3]} />
            </bufferGeometry>
            <pointsMaterial size={0.045} color="#10B981" transparent opacity={0.8} />
        </points>
    );
}

// --- 3. FLUID BACKGROUND (§7 — three-layer fixed stack) ---
// Layer 1: bg-grid CSS class. Layer 2: Three.js Canvas. Layer 3: morphing blobs.
// Blob A: top-right (emerald, 800px). Blob B: bottom-left (teal, 600px).
// Blob C: center (emerald/5, 450px) — page is ~100vh so glass depth needs center color.

function FluidCanvas() {
    return (
        <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden bg-[#030508]">

            {/* Layer 1 — static grid texture */}
            <div className="absolute inset-0 bg-grid opacity-50" />

            {/* Layer 2 — Three.js ambient point field, mix-blend-screen */}
            <div className="absolute inset-0 mix-blend-screen">
                <Canvas camera={{ position: [0, 0, 15], fov: 60 }}>
                    <Starfield />
                </Canvas>
            </div>

            {/* Layer 3 — Blob A: top-RIGHT, emerald, 800×800px per §7 */}
            <motion.div
                className="absolute -top-[10%] -right-[5%] w-[800px] h-[800px] bg-emerald-500/10 blur-[150px]"
                animate={{
                    x: [0, 40, -25, 0],
                    y: [0, -30, 20, 0],
                    scale: [1, 1.15, 0.94, 1],
                    borderRadius: [
                        '50%',
                        '42% 58% 60% 40% / 50% 45% 55% 50%',
                        '58% 42% 40% 60% / 45% 55% 45% 55%',
                        '50%',
                    ],
                }}
                transition={{ duration: 24, ease: 'easeInOut', repeat: Infinity }}
            />

            {/* Blob B: bottom-LEFT, teal, 600×600px per §7 */}
            <motion.div
                className="absolute -bottom-[10%] -left-[5%] w-[600px] h-[600px] bg-teal-500/10 blur-[150px]"
                animate={{
                    x: [0, -30, 30, 0],
                    y: [0, 25, -25, 0],
                    scale: [1, 0.9, 1.12, 1],
                    borderRadius: [
                        '50%',
                        '60% 40% 38% 62% / 55% 45% 55% 45%',
                        '40% 60% 62% 38% / 45% 55% 45% 55%',
                        '50%',
                    ],
                }}
                transition={{ duration: 28, ease: 'easeInOut', repeat: Infinity, delay: 2 }}
            />

            {/* Blob C: center — ensures glass cards mid-page get color variation behind them per §4.2 */}
            <motion.div
                className="absolute top-[35%] left-[35%] w-[450px] h-[450px] bg-emerald-500/5 blur-[120px]"
                animate={{
                    x: [0, 20, -20, 0],
                    y: [0, -20, 20, 0],
                    scale: [1, 1.1, 0.95, 1],
                    borderRadius: [
                        '50%',
                        '42% 58% 60% 40% / 50% 45% 55% 50%',
                        '58% 42% 40% 60% / 45% 55% 45% 55%',
                        '50%',
                    ],
                }}
                transition={{ duration: 20, ease: 'easeInOut', repeat: Infinity, delay: 5 }}
            />
        </div>
    );
}

// --- 4. CONFIGURATION DATA ---

const QUESTIONS = [
    {
        id: 'experience',
        eyebrow: 'System Variable 01',
        headline: 'Experience Level.',
        subhead: 'Dictates vocabulary complexity.',
        options: ['Beginner', 'Intermediate', 'Advanced'],
        type: 'choice',
    },
    {
        id: 'goal',
        eyebrow: 'System Variable 02',
        headline: 'Primary Goal.',
        subhead: 'Optimizes strategy targeting.',
        options: ['Wealth Growth', 'Dividend Income', 'Capital Preservation'],
        type: 'choice',
    },
    {
        id: 'style',
        eyebrow: 'System Variable 03',
        headline: 'Trading Style.',
        subhead: 'Calibrates timeframe horizons.',
        options: ['Intraday', 'Swing', 'Positional', 'Long-term'],
        type: 'choice',
    },
    {
        id: 'risk',
        eyebrow: 'System Variable 04',
        headline: 'Risk Tolerance.',
        subhead: 'Sets standard deviation boundaries.',
        options: ['Conservative', 'Moderate', 'Aggressive'],
        type: 'choice',
    },
    {
        id: 'portfolio',
        eyebrow: 'System Variable 05',
        headline: 'Current Diversification.',
        subhead: 'Map existing sector exposures.',
        type: 'allocation',
    },
    {
        id: 'capital',
        eyebrow: 'System Variable 06',
        headline: 'Monthly Capital.',
        subhead: 'Define pure numeric deployment.',
        type: 'numeric',
    },
] as const;

type QuestionId = typeof QUESTIONS[number]['id'];

// --- 5. MAIN PAGE ---

export default function ConfigurationPage() {
    const navigate = useNavigate();
    const { session, setProfileState } = useAuth();
    const [step, setStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [formData, setFormData] = useState<{
        experience: string;
        goal: string;
        style: string;
        risk: string;
        portfolio: { id: string; name: string; value: string }[];
        capital: string;
    }>({
        experience: '',
        goal: '',
        style: '',
        risk: '',
        portfolio: [
            { id: 'init-1', name: 'Equities', value: '' },
            { id: 'init-2', name: 'Cash', value: '' },
        ],
        capital: '',
    });

    const activeQuestion = QUESTIONS[step];

    // 3D tilt — same recipe as hero card per §9 hero dashboard card
    const cardX = useSpring(0, { stiffness: 150, damping: 20 });
    const cardY = useSpring(0, { stiffness: 150, damping: 20 });
    const rotateX = useTransform(cardY, [-0.5, 0.5], ['5deg', '-5deg']);
    const rotateY = useTransform(cardX, [-0.5, 0.5], ['-5deg', '5deg']);

    function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
        const rect = e.currentTarget.getBoundingClientRect();
        const xPct = (e.clientX - rect.left) / rect.width - 0.5;
        const yPct = (e.clientY - rect.top) / rect.height - 0.5;
        cardX.set(xPct);
        cardY.set(yPct);
    }

    function handleMouseLeave() {
        cardX.set(0);
        cardY.set(0);
    }

    const isStepComplete = (): boolean => {
        if (activeQuestion.type === 'choice') {
            return formData[activeQuestion.id as QuestionId] !== '';
        }
        if (activeQuestion.type === 'allocation') {
            const sum = formData.portfolio.reduce((a, b) => a + (Number(b.value) || 0), 0);
            const allNamed = formData.portfolio.every(p => p.name.trim() !== '');
            return sum === 100 && allNamed && formData.portfolio.length > 0;
        }
        if (activeQuestion.type === 'numeric') {
            return formData.capital !== '' && Number(formData.capital) > 0;
        }
        return false;
    };

    const handleNext = async () => {
        if (step < QUESTIONS.length - 1) {
            setStep(s => s + 1);
        } else {
            if (!session) {
                setSubmitError("No active session. Please log in again.");
                return;
            }
            setLoading(true);
            setSubmitError(null);

            const finalPortfolio = formData.portfolio.reduce((acc, curr) => {
                acc[curr.name] = Number(curr.value) / 100.0;
                return acc;
            }, {} as Record<string, number>);

            const goalMapped = formData.goal === 'Wealth Growth' ? 'wealth_growth' 
                : formData.goal === 'Dividend Income' ? 'dividend_income' 
                : 'capital_preservation';

            const styleMapped = formData.style === 'Long-term' ? 'long_term' : formData.style.toLowerCase();

            const payload = {
                experience: formData.experience.toLowerCase(),
                goal: goalMapped,
                timeframe: styleMapped,
                risk: formData.risk.toLowerCase(),
                portfolio: finalPortfolio,
                capital: parseFloat(formData.capital)
            };

            try {
                const response = await fetch('http://localhost:8000/api/v1/profiles/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${session.access_token}`
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || 'Failed to submit profile calibration.');
                }

                const responseData = await response.json();
                setProfileState(responseData);
                navigate('/workspace');
            } catch (err: any) {
                console.error(err);
                setSubmitError(err.message || 'An error occurred during submission.');
            } finally {
                setLoading(false);
            }
        }
    };

    const totalAlloc = formData.portfolio.reduce((a, b) => a + (Number(b.value) || 0), 0);
    const allocComplete = totalAlloc === 100;

    return (
        <div className="relative w-full min-h-screen bg-[#030508] text-white font-sans tracking-tighter font-bold selection:bg-emerald-500/30">
            <FluidCanvas />

            {/* ── NAV SCRIM (z-40) — fades in on scroll per §8 ── */}
            <div
                className="fixed top-0 inset-x-0 h-24 z-40 pointer-events-none"
                style={{
                    backdropFilter: 'blur(20px)',
                    WebkitBackdropFilter: 'blur(20px)',
                    background: 'linear-gradient(180deg, rgba(3,5,8,0.70) 0%, rgba(3,5,8,0) 100%)',
                }}
            />

            {/* ── NAV (z-50) — logo left, always visible per §8 ── */}
            <nav className="fixed top-0 w-full px-8 md:px-16 py-8 flex justify-between items-center z-50">
                <div className="font-bold text-2xl tracking-tighter text-white flex items-center">
                    INVR<span className="text-emerald-500">.</span>
                </div>

                {/* Step progress pill — right side of nav (glass.pill per §9) */}
                <div
                    className="hidden md:flex items-center gap-2 px-4 py-2 rounded-full"
                    style={glass.pill}
                >
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                    <span className="text-[11px] font-bold tracking-tighter text-white uppercase">
                        Calibration {step + 1} / {QUESTIONS.length}
                    </span>
                </div>
            </nav>

            {/* ── MAIN CONTENT ── */}
            <main className="relative z-10 flex min-h-screen items-center justify-center p-6 pt-28">

                {/* Outer glass.base card with 3D tilt */}
                <motion.div
                    style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
                    onMouseMove={handleMouseMove}
                    onMouseLeave={handleMouseLeave}
                    className="relative w-full max-w-4xl"
                >
                    {/* glass.base shell — absolute to not affect layout */}
                    <div
                        className="absolute inset-0 rounded-[2.5rem] overflow-hidden"
                        style={glass.base}
                    />

                    {/* Giant typographic watermark numeral per §9 narrative card recipe */}
                    <AnimatePresence mode="wait">
                        <motion.span
                            key={`wm-${step}`}
                            aria-hidden="true"
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            exit={{ y: -20, opacity: 0 }}
                            transition={springSoft}
                            className="absolute -top-8 -left-4 text-[11rem] md:text-[14rem] font-bold leading-none tabular-nums text-white/[0.045] pointer-events-none select-none tracking-tighter"
                        >
                            0{step + 1}
                        </motion.span>
                    </AnimatePresence>

                    {/* Card content */}
                    <div className="relative z-10 p-10 md:p-16 grid grid-cols-1 md:grid-cols-[1fr_1.2fr] gap-12">

                        {/* ── LEFT COLUMN: Question context ── */}
                        <div className="flex flex-col justify-between">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`ctx-${step}`}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 20 }}
                                    transition={springSoft}
                                    className="flex flex-col"
                                >
                                    {/* Eyebrow */}
                                    <p className="text-[10px] uppercase tracking-[0.18em] text-emerald-400 mb-4">
                                        {activeQuestion.eyebrow}
                                    </p>

                                    {/* Headline — idle float on the primary word per §6.2 */}
                                    <h1 className="text-5xl md:text-6xl leading-[1.05] mb-4">
                                        <motion.span
                                            className="inline-block"
                                            animate={{ y: [0, -5, 0] }}
                                            transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
                                        >
                                            {activeQuestion.headline.split('.')[0]}.
                                        </motion.span>
                                        <br />
                                        <span className="text-white/40">{activeQuestion.subhead}</span>
                                    </h1>

                                    {/* §4.2 MANDATORY — glass.pill badge inside glass.base card.
                                        Left column is text-only without this, which renders flat. */}
                                    <div className="mt-6">
                                        <span
                                            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-bold tracking-[0.12em] uppercase text-emerald-400"
                                            style={glass.pill}
                                        >
                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.8)]" />
                                            Step {step + 1} of {QUESTIONS.length}
                                        </span>
                                    </div>
                                </motion.div>
                            </AnimatePresence>

                            {/* Progress dots — compact, bottom of left col */}
                            <div className="hidden md:flex gap-2 mt-8">
                                {QUESTIONS.map((_, i) => (
                                    <div
                                        key={i}
                                        className={`h-1 rounded-full transition-all duration-500 ${
                                            i === step
                                                ? 'w-6 bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]'
                                                : i < step
                                                ? 'w-3 bg-white/30'
                                                : 'w-3 bg-white/10'
                                        }`}
                                    />
                                ))}
                            </div>
                        </div>

                        {/* ── RIGHT COLUMN: Dynamic input ── */}
                        <div className="flex flex-col justify-center min-h-[300px]">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`input-${step}`}
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 1.05 }}
                                    transition={springSoft}
                                    className="w-full"
                                >

                                    {/* TYPE: MULTIPLE CHOICE */}
                                    {activeQuestion.type === 'choice' && (
                                        <div className="flex flex-col gap-3">
                                            {(activeQuestion as any).options?.map((option: string) => {
                                                const isSelected = formData[activeQuestion.id as QuestionId] === option;
                                                return (
                                                    <motion.button
                                                        key={option}
                                                        onClick={() => setFormData({ ...formData, [activeQuestion.id]: option })}
                                                        whileHover={{ scale: 1.02 }}
                                                        whileTap={{ scale: 0.98 }}
                                                        transition={springPress}
                                                        style={glass.nested}
                                                        className="relative w-full rounded-[1.5rem] p-5 text-left flex items-center justify-between overflow-hidden"
                                                    >
                                                        <span className="relative z-10 text-xl">{option}</span>

                                                        {/* Shared layoutId pill slides between selected items */}
                                                        {isSelected && (
                                                            <motion.div
                                                                layoutId="active-choice"
                                                                className="absolute inset-0 bg-gradient-to-r from-teal-500/10 to-emerald-500/10 border border-emerald-500/30 rounded-[1.5rem] z-0"
                                                                transition={springSoft}
                                                            />
                                                        )}

                                                        {/* Selected indicator — status dot recipe from §9 */}
                                                        {isSelected && (
                                                            <motion.div
                                                                initial={{ scale: 0, opacity: 0 }}
                                                                animate={{ scale: 1, opacity: 1 }}
                                                                transition={springPress}
                                                                className="relative z-10 w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center shadow-[0_0_12px_rgba(16,185,129,0.6)]"
                                                            >
                                                                <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
                                                            </motion.div>
                                                        )}
                                                    </motion.button>
                                                );
                                            })}
                                        </div>
                                    )}

                                    {/* TYPE: PORTFOLIO ALLOCATION BUILDER */}
                                    {activeQuestion.type === 'allocation' && (
                                        <div style={glass.nested} className="rounded-[1.5rem] p-6 flex flex-col gap-4">

                                            {/* Gradient top-edge divider inside nested panel per §9 verdict panel */}
                                            <div className="absolute top-0 left-8 right-8 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />

                                            <p className="text-[10px] font-bold tracking-[0.18em] text-emerald-400 uppercase mb-1">
                                                Sector Allocation
                                            </p>

                                            <AnimatePresence>
                                                {formData.portfolio.map((sector, index) => (
                                                    <motion.div
                                                        key={sector.id}
                                                        initial={{ opacity: 0, height: 0 }}
                                                        animate={{ opacity: 1, height: 'auto' }}
                                                        exit={{ opacity: 0, height: 0 }}
                                                        transition={springSoft}
                                                        className="flex items-center justify-between gap-4"
                                                    >
                                                        <input
                                                            type="text"
                                                            placeholder="Sector"
                                                            value={sector.name}
                                                            onChange={(e) => {
                                                                const next = [...formData.portfolio];
                                                                next[index] = { ...next[index], name: e.target.value };
                                                                setFormData(prev => ({ ...prev, portfolio: next }));
                                                            }}
                                                            className="bg-transparent border-b border-white/10 text-white placeholder:text-white/30 outline-none text-[12px] uppercase tracking-[0.1em] w-28 pb-1 focus:border-emerald-500/50 transition-colors"
                                                        />

                                                        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                                                            <motion.div
                                                                className="h-full bg-gradient-to-r from-teal-500 to-emerald-500"
                                                                initial={{ width: 0 }}
                                                                animate={{ width: `${sector.value || 0}%` }}
                                                                transition={springSoft}
                                                            />
                                                        </div>

                                                        <div className="relative flex items-center">
                                                            <input
                                                                type="number"
                                                                min="0"
                                                                max="100"
                                                                placeholder="0"
                                                                value={sector.value}
                                                                onChange={(e) => {
                                                                    const val = Math.min(100, Math.max(0, Number(e.target.value) || 0));
                                                                    const next = [...formData.portfolio];
                                                                    next[index] = { ...next[index], value: e.target.value === '' ? '' : String(val) };
                                                                    setFormData(prev => ({ ...prev, portfolio: next }));
                                                                }}
                                                                className="w-16 bg-white/5 border border-white/10 rounded-lg py-2 px-2 text-right text-white tabular-nums outline-none focus:border-emerald-500/50 transition-colors [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                                            />
                                                            <span className="absolute right-3 text-white/40 text-sm pointer-events-none">%</span>
                                                        </div>

                                                        <motion.button
                                                            onClick={() =>
                                                                setFormData(prev => ({
                                                                    ...prev,
                                                                    portfolio: prev.portfolio.filter(p => p.id !== sector.id),
                                                                }))
                                                            }
                                                            whileHover={{ scale: 1.1 }}
                                                            whileTap={{ scale: 0.9 }}
                                                            transition={springPress}
                                                            className="text-white/30 hover:text-rose-400 transition-colors ml-2"
                                                        >
                                                            <X size={14} />
                                                        </motion.button>
                                                    </motion.div>
                                                ))}
                                            </AnimatePresence>

                                            <motion.button
                                                onClick={() =>
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        portfolio: [
                                                            ...prev.portfolio,
                                                            { id: Date.now().toString(), name: '', value: '' },
                                                        ],
                                                    }))
                                                }
                                                whileHover={{ scale: 1.02 }}
                                                whileTap={{ scale: 0.98 }}
                                                transition={springPress}
                                                className="text-left text-[10px] uppercase tracking-[0.18em] text-emerald-400 hover:text-emerald-300 transition-colors mt-2 flex items-center gap-2 w-max"
                                            >
                                                <Plus size={12} /> Add Custom Sector
                                            </motion.button>

                                            <div className="mt-4 pt-4 border-t border-white/10 flex justify-between items-center">
                                                <span className="text-[10px] uppercase tracking-[0.18em] text-white/40">Total Allocation</span>
                                                <span className={`text-xl tabular-nums ${allocComplete ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                    {totalAlloc}%
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    {/* TYPE: NUMERIC CAPITAL INPUT */}
                                    {activeQuestion.type === 'numeric' && (
                                        <div style={glass.nested} className="rounded-[1.5rem] p-8 flex flex-col items-center justify-center min-h-[200px] relative overflow-hidden">
                                            {/* Gradient top-edge divider per §9 verdict panel recipe */}
                                            <div className="absolute top-0 left-8 right-8 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />

                                            <div className="text-[10px] uppercase tracking-[0.18em] text-emerald-400 mb-6">
                                                Deployable monthly baseline
                                            </div>
                                            <div className="flex items-center text-6xl md:text-7xl">
                                                {/* ₹ for INR — product is India-focused per §9 */}
                                                <span className="text-white/20 mr-3 font-normal text-5xl">₹</span>
                                                <input
                                                    type="number"
                                                    autoFocus
                                                    value={formData.capital}
                                                    onChange={(e) => setFormData({ ...formData, capital: e.target.value })}
                                                    className="bg-transparent text-white outline-none w-[200px] tabular-nums placeholder:text-white/10 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                                    placeholder="0"
                                                />
                                            </div>

                                            {/* §4.2 extra nested depth inside the nested panel (pill tier) */}
                                            {Number(formData.capital) > 0 && (
                                                <motion.div
                                                    initial={{ opacity: 0, y: 8 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    transition={springSoft}
                                                    className="mt-6 flex items-center gap-2 px-3 py-1.5 rounded-full"
                                                    style={glass.pill}
                                                >
                                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.8)]" />
                                                    <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-emerald-400">
                                                        Capital Locked
                                                    </span>
                                                </motion.div>
                                            )}
                                        </div>
                                    )}

                                </motion.div>
                            </AnimatePresence>

                            {submitError && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    style={glass.nested}
                                    className="mt-4 p-4 rounded-[1.25rem] text-rose-400 text-sm font-bold tracking-tighter"
                                >
                                    {submitError}
                                </motion.div>
                            )}
                        </div>
                    </div>

                    {/* ── BOTTOM ACTION BAR ── */}
                    <div className="relative z-10 mx-10 md:mx-16 mb-10 md:mb-16 flex items-center justify-between border-t border-white/10 pt-8">

                        {/* Back — glass secondary button per §9 */}
                        <motion.button
                            onClick={() => setStep(s => Math.max(0, s - 1))}
                            whileHover={step === 0 ? {} : { scale: 1.03 }}
                            whileTap={step === 0 ? {} : { scale: 0.97 }}
                            transition={springPress}
                            className={`flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] transition-opacity px-4 py-2 rounded-[1rem] ${
                                step === 0
                                    ? 'opacity-0 pointer-events-none'
                                    : 'opacity-100 text-white/50 hover:text-white'
                            }`}
                            style={step === 0 ? {} : glass.pill}
                        >
                            <ArrowLeft size={14} /> Revert
                        </motion.button>

                        {/* Mobile-only progress dots */}
                        <div className="md:hidden flex gap-2">
                            {QUESTIONS.map((_, i) => (
                                <div
                                    key={i}
                                    className={`h-1 rounded-full transition-all duration-500 ${
                                        i === step
                                            ? 'w-6 bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]'
                                            : i < step
                                            ? 'w-3 bg-white/30'
                                            : 'w-3 bg-white/10'
                                    }`}
                                />
                            ))}
                        </div>

                        {/* Confirm — Primary CTA per §9 */}
                        <motion.button
                            disabled={!isStepComplete() || loading}
                            onClick={handleNext}
                            whileHover={{ scale: (isStepComplete() && !loading) ? 1.03 : 1 }}
                            whileTap={{ scale: (isStepComplete() && !loading) ? 0.97 : 1 }}
                            animate={
                                (isStepComplete() && !loading)
                                    ? {
                                          boxShadow: [
                                              '0 0 10px rgba(16,185,129,0.4)',
                                              '0 0 42px rgba(16,185,129,0.8)',
                                              '0 0 10px rgba(16,185,129,0.4)',
                                          ],
                                      }
                                    : {}
                            }
                            transition={{
                                ...springPress,
                                boxShadow: { duration: 3, repeat: Infinity, ease: 'easeInOut' },
                            }}
                            className={`flex items-center gap-3 px-8 py-4 rounded-[1.25rem] text-[12px] uppercase tracking-[0.15em] font-bold transition-all duration-300 ${
                                (isStepComplete() && !loading)
                                    ? 'bg-white text-black cursor-pointer'
                                    : 'bg-white/5 text-white/20 border border-white/10 cursor-not-allowed'
                            }`}
                        >
                            {loading ? 'Vectorizing...' : (step === QUESTIONS.length - 1 ? 'Finalize Calibration' : 'Confirm & Proceed')}
                            <ArrowRight size={16} />
                        </motion.button>
                    </div>
                </motion.div>
            </main>
        </div>
    );
}