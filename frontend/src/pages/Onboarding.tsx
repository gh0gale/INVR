import React, { useState, useRef, useMemo } from 'react';
import { motion, AnimatePresence, useSpring, useTransform } from 'framer-motion';
import { Canvas, useFrame } from '@react-three/fiber';
import { ArrowRight, ArrowLeft, Plus, X } from 'lucide-react';

// --- 1. DESIGN SYSTEM TOKENS & PHYSICS ---

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
    },
    nested: {
        background: 'linear-gradient(145deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.01) 100%)',
        border: '1px solid rgba(255,255,255,0.085)',
        boxShadow: [
            'inset 0 1px 0 rgba(255,255,255,0.20)',
            'inset 1px 0 0 rgba(255,255,255,0.06)',
            '0 8px 32px rgba(0,0,0,0.22)',
        ].join(', '),
    },
    pill: {
        background: 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)',
        border: '1px solid rgba(255,255,255,0.10)',
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.20), 0 4px 12px rgba(0,0,0,0.15)',
    },
};

const springPress = { type: 'spring', stiffness: 420, damping: 26, mass: 0.6 };
const springSoft = { type: 'spring', stiffness: 220, damping: 28, mass: 0.9 };

// --- 2. AMBIENT BACKGROUND CANVAS ---

function Starfield() {
    const pointsRef = useRef<THREE.Points>(null);

    const particles = useMemo(() => {
        const temp = new Float32Array(2500 * 3);
        for (let i = 0; i < 2500; i++) {
            temp[i * 3] = (Math.random() - 0.5) * 35;
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
                <bufferAttribute attach="attributes-position" count={2500} array={particles} itemSize={3} />
            </bufferGeometry>
            <pointsMaterial size={0.045} color="#10B981" transparent opacity={0.8} />
        </points>
    );
}

function FluidCanvas() {
    return (
        <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden bg-[#030508]">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz48L3N2Zz4=')] opacity-50" />

            <div className="absolute inset-0 mix-blend-screen">
                <Canvas camera={{ position: [0, 0, 15], fov: 60 }}>
                    <Starfield />
                </Canvas>
            </div>

            <motion.div
                className="absolute -top-[20%] -left-[10%] w-[800px] h-[800px] bg-emerald-500/20 blur-[150px]"
                animate={{
                    x: [-40, 40, -40],
                    y: [-20, 30, -20],
                    scale: [0.9, 1.15, 0.9],
                    borderRadius: ['42% 58% 60% 40% / 50% 45% 55% 50%', '55% 45% 50% 50% / 40% 60% 45% 55%', '42% 58% 60% 40% / 50% 45% 55% 50%'],
                }}
                transition={{ duration: 28, ease: 'easeInOut', repeat: Infinity }}
            />

            <motion.div
                className="absolute -bottom-[20%] -right-[10%] w-[600px] h-[600px] bg-teal-500/20 blur-[150px]"
                animate={{
                    x: [30, -30, 30],
                    y: [40, -20, 40],
                    scale: [1.1, 0.9, 1.1],
                    borderRadius: ['50% 50% 40% 60% / 55% 45% 60% 40%', '40% 60% 55% 45% / 50% 50% 45% 55%', '50% 50% 40% 60% / 55% 45% 60% 40%'],
                }}
                transition={{ duration: 22, ease: 'easeInOut', repeat: Infinity, delay: 2 }}
            />
        </div>
    );
}

// --- 3. CONFIGURATION DATA ---

const QUESTIONS = [
    {
        id: 'experience',
        eyebrow: 'System Variable 01',
        headline: 'Experience Level.',
        subhead: 'Dictates vocabulary complexity.',
        options: ['Beginner', 'Intermediate', 'Advanced'],
        type: 'choice'
    },
    {
        id: 'goal',
        eyebrow: 'System Variable 02',
        headline: 'Primary Goal.',
        subhead: 'Optimizes strategy targeting.',
        options: ['Wealth Growth', 'Dividend Income', 'Diversification'],
        type: 'choice'
    },
    {
        id: 'style',
        eyebrow: 'System Variable 03',
        headline: 'Trading Style.',
        subhead: 'Calibrates timeframe horizons.',
        options: ['Intraday', 'Swing', 'Positional', 'Long-term'],
        type: 'choice'
    },
    {
        id: 'risk',
        eyebrow: 'System Variable 04',
        headline: 'Risk Tolerance.',
        subhead: 'Sets standard deviation boundaries.',
        options: ['Conservative', 'Moderate', 'Aggressive'],
        type: 'choice'
    },
    {
        id: 'portfolio',
        eyebrow: 'System Variable 05',
        headline: 'Current Diversification.',
        subhead: 'Map existing sector exposures.',
        type: 'allocation'
    },
    {
        id: 'capital',
        eyebrow: 'System Variable 06',
        headline: 'Monthly Capital.',
        subhead: 'Define pure numeric deployment.',
        type: 'numeric'
    }
];

// --- 4. MAIN APPLICATION ---

export default function ConfigurationPage() {
    const [step, setStep] = useState(0);

    // State definitions matching the requested schema with dynamic portfolio
    const [formData, setFormData] = useState({
        experience: '',
        goal: '',
        style: '',
        risk: '',
        portfolio: [
            { id: 'init-1', name: 'Equities', value: '' },
            { id: 'init-2', name: 'Cash', value: '' }
        ],
        capital: ''
    });

    const activeQuestion = QUESTIONS[step];

    // 3D Tilt Logic
    const cardX = useSpring(0, { stiffness: 150, damping: 20 });
    const cardY = useSpring(0, { stiffness: 150, damping: 20 });
    const rotateX = useTransform(cardY, [-0.5, 0.5], ['5deg', '-5deg']);
    const rotateY = useTransform(cardX, [-0.5, 0.5], ['-5deg', '5deg']);

    function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
        const rect = e.currentTarget.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        const xPct = mouseX / width - 0.5;
        const yPct = mouseY / height - 0.5;
        cardX.set(xPct);
        cardY.set(yPct);
    }

    function handleMouseLeave() {
        cardX.set(0);
        cardY.set(0);
    }

    const isStepComplete = () => {
        if (activeQuestion.type === 'choice') return formData[activeQuestion.id as keyof typeof formData] !== '';
        if (activeQuestion.type === 'allocation') {
            const sum = formData.portfolio.reduce((a, b) => a + (Number(b.value) || 0), 0);
            const allNamed = formData.portfolio.every(p => p.name.trim() !== '');
            return sum === 100 && allNamed && formData.portfolio.length > 0;
        }
        if (activeQuestion.type === 'numeric') return formData.capital !== '' && Number(formData.capital) > 0;
        return false;
    };

    const handleNext = () => {
        if (step < QUESTIONS.length - 1) setStep(s => s + 1);
        else {
            // Clean transform mapping the dynamic array back into the strict object backend expects
            const finalPortfolio = formData.portfolio.reduce((acc, curr) => {
                acc[curr.name] = Number(curr.value);
                return acc;
            }, {} as Record<string, number>);

            console.log('Final Payload Ready:', { ...formData, portfolio: finalPortfolio });
        }
    };

    return (
        <div className="min-h-screen font-sans tracking-tighter font-bold text-white selection:bg-emerald-500/30">
            <FluidCanvas />

            {/* Navbar Scrim & Container (Pill Removed) */}
            <div className="fixed top-0 left-0 right-0 h-24 z-50 flex items-center justify-between px-8"
                style={{ background: 'linear-gradient(to bottom, #030508 0%, transparent 100%)' }}>
                <div className="text-xl tracking-tighter">INVR<span className="text-white/40">.</span></div>
            </div>

            <main className="relative z-10 flex min-h-screen items-center justify-center p-6 pt-24">

                {/* Giant active card with subtle 3D tilt */}
                <motion.div
                    style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
                    onMouseMove={handleMouseMove}
                    onMouseLeave={handleMouseLeave}
                    className="relative w-full max-w-4xl rounded-[2.5rem] p-10 md:p-16"
                >
                    <div className="absolute inset-0 rounded-[2.5rem] overflow-hidden" style={glass.base} />
                    {/* Typographic Watermark Bleed */}
                    <motion.div
                        key={`watermark-${step}`}
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        className="absolute -top-12 -left-8 text-[14rem] leading-none tabular-nums text-white/[0.045] pointer-events-none select-none"
                    >
                        0{step + 1}
                    </motion.div>

                    <div className="relative z-10 grid grid-cols-1 md:grid-cols-[1fr_1.2fr] gap-12">

                        {/* Left Column: Context */}
                        <div className="flex flex-col justify-center">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`content-${step}`}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 20 }}
                                    transition={springSoft}
                                >
                                    <p className="text-[10px] uppercase tracking-[0.18em] text-emerald-400 mb-4">
                                        {activeQuestion.eyebrow}
                                    </p>
                                    <h1 className="text-5xl md:text-6xl leading-[1.05]">
                                        {activeQuestion.headline.split('.')[0]}.<br />
                                        <span className="text-white/40">{activeQuestion.subhead}</span>
                                    </h1>
                                </motion.div>
                            </AnimatePresence>
                        </div>

                        {/* Right Column: Dynamic Input Types */}
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
                                            {activeQuestion.options?.map((option) => {
                                                const isSelected = formData[activeQuestion.id as keyof typeof formData] === option;
                                                return (
                                                    <motion.button
                                                        key={option}
                                                        onClick={() => setFormData({ ...formData, [activeQuestion.id]: option })}
                                                        whileHover={{ scale: 1.02 }}
                                                        whileTap={{ scale: 0.98 }}
                                                        transition={springPress}
                                                        style={glass.nested}
                                                        className="relative w-full rounded-[1.5rem] p-5 text-left flex items-center justify-between group overflow-hidden"
                                                    >
                                                        <span className="relative z-10 text-xl">{option}</span>

                                                        {/* Inner active layout pill */}
                                                        {isSelected && (
                                                            <motion.div
                                                                layoutId="active-choice"
                                                                className="absolute inset-0 bg-gradient-to-r from-teal-500/10 to-emerald-500/10 border border-emerald-500/30 rounded-[1.5rem] z-0"
                                                                transition={springSoft}
                                                            />
                                                        )}

                                                        {isSelected && (
                                                            <motion.div
                                                                initial={{ scale: 0, opacity: 0 }}
                                                                animate={{ scale: 1, opacity: 1 }}
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

                                    {/* TYPE: DYNAMIC ALLOCATION / PORTFOLIO BUILDER */}
                                    {activeQuestion.type === 'allocation' && (
                                        <div style={glass.nested} className="rounded-[1.5rem] p-6 flex flex-col gap-4">
                                            <AnimatePresence>
                                                {formData.portfolio.map((sector, index) => (
                                                    <motion.div
                                                        key={sector.id}
                                                        initial={{ opacity: 0, height: 0 }}
                                                        animate={{ opacity: 1, height: 'auto' }}
                                                        exit={{ opacity: 0, height: 0 }}
                                                        className="flex items-center justify-between gap-4"
                                                    >
                                                        <input
                                                            type="text"
                                                            placeholder="Sector name"
                                                            value={sector.name}
                                                            onChange={(e) => {
                                                                const newPortfolio = [...formData.portfolio];
                                                                newPortfolio[index].name = e.target.value;
                                                                setFormData(prev => ({ ...prev, portfolio: newPortfolio }));
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
                                                                    const newPortfolio = [...formData.portfolio];
                                                                    newPortfolio[index].value = e.target.value === '' ? '' : String(val);
                                                                    setFormData(prev => ({ ...prev, portfolio: newPortfolio }));
                                                                }}
                                                                // Tailwind arbitrary variants to hide browser spin buttons
                                                                className="w-16 bg-white/5 border border-white/10 rounded-lg py-2 px-2 text-right text-white tabular-nums outline-none focus:border-emerald-500/50 transition-colors [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                                            />
                                                            <span className="absolute right-3 text-white/40 text-sm pointer-events-none">%</span>
                                                        </div>

                                                        <button
                                                            onClick={() => {
                                                                setFormData(prev => ({ ...prev, portfolio: prev.portfolio.filter(p => p.id !== sector.id) }));
                                                            }}
                                                            className="text-white/30 hover:text-rose-400 transition-colors ml-2"
                                                        >
                                                            <X size={14} />
                                                        </button>
                                                    </motion.div>
                                                ))}
                                            </AnimatePresence>

                                            <button
                                                onClick={() => {
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        portfolio: [...prev.portfolio, { id: Date.now().toString(), name: '', value: '' }]
                                                    }));
                                                }}
                                                className="text-left text-[10px] uppercase tracking-[0.18em] text-emerald-400 hover:text-emerald-300 transition-colors mt-2 flex items-center gap-2 w-max"
                                            >
                                                <Plus size={12} /> Add Custom Sector
                                            </button>

                                            <div className="mt-4 pt-4 border-t border-white/10 flex justify-between items-center">
                                                <span className="text-[10px] uppercase tracking-[0.18em] text-white/40">Total Allocation</span>
                                                <span className={`text-xl tabular-nums ${formData.portfolio.reduce((a, b) => a + (Number(b.value) || 0), 0) === 100 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                    {formData.portfolio.reduce((a, b) => a + (Number(b.value) || 0), 0)}%
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    {/* TYPE: PURE NUMERIC (CAPITAL) */}
                                    {activeQuestion.type === 'numeric' && (
                                        <div style={glass.nested} className="rounded-[1.5rem] p-8 flex flex-col items-center justify-center min-h-[200px]">
                                            <div className="text-[10px] uppercase tracking-[0.18em] text-white/50 mb-2">Deployable monthly baseline</div>
                                            <div className="flex items-center text-6xl md:text-7xl">
                                                <span className="text-white/20 mr-2 font-normal">$</span>
                                                <input
                                                    type="number"
                                                    autoFocus
                                                    value={formData.capital}
                                                    onChange={(e) => setFormData({ ...formData, capital: e.target.value })}
                                                    // Hiding spin buttons here as well
                                                    className="bg-transparent text-white outline-none w-[200px] tabular-nums placeholder:text-white/10 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                                    placeholder="0.00"
                                                />
                                            </div>
                                        </div>
                                    )}

                                </motion.div>
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Bottom Action Bar */}
                    <div className="mt-16 flex items-center justify-between border-t border-white/10 pt-8 relative z-10">
                        <button
                            onClick={() => setStep(s => Math.max(0, s - 1))}
                            className={`flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] transition-opacity ${step === 0 ? 'opacity-0 pointer-events-none' : 'opacity-100 text-white/50 hover:text-white'}`}
                        >
                            <ArrowLeft size={14} /> Revert Step
                        </button>

                        {/* Pagination Dots */}
                        <div className="flex gap-2">
                            {QUESTIONS.map((_, i) => (
                                <div
                                    key={i}
                                    className={`w-1.5 h-1.5 rounded-full transition-colors duration-500 ${i === step ? 'bg-emerald-500' : i < step ? 'bg-white/30' : 'bg-white/10'}`}
                                />
                            ))}
                        </div>

                        <motion.button
                            disabled={!isStepComplete()}
                            onClick={handleNext}
                            whileHover={{ scale: isStepComplete() ? 1.03 : 1 }}
                            whileTap={{ scale: isStepComplete() ? 0.97 : 1 }}
                            animate={isStepComplete() ? { boxShadow: ['0 0 10px rgba(16,185,129,0.4)', '0 0 30px rgba(16,185,129,0.8)', '0 0 10px rgba(16,185,129,0.4)'] } : {}}
                            transition={{ ...springPress, boxShadow: { duration: 3, repeat: Infinity, ease: 'easeInOut' } }}
                            className={`flex items-center gap-3 px-8 py-4 rounded-[1.25rem] text-[12px] uppercase tracking-[0.15em] font-bold transition-all duration-300 ${isStepComplete()
                                ? 'bg-white text-black shadow-[0_0_20px_rgba(16,185,129,0.5)] cursor-pointer'
                                : 'bg-white/5 text-white/20 border border-white/10 cursor-not-allowed'
                                }`}
                        >
                            {step === QUESTIONS.length - 1 ? 'Finalize Calibration' : 'Confirm & Proceed'}
                            <ArrowRight size={16} />
                        </motion.button>
                    </div>
                </motion.div>
            </main>
        </div>
    );
}