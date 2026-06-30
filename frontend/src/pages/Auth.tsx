import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { ArrowRight, X } from 'lucide-react';
import { supabase } from '../supabase';
import { useAuth } from '../context/AuthContext';

// ==========================================
// 1. EXACT GLASS STYLE SYSTEM (From .md)
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

const springPress = { type: 'spring', stiffness: 420, damping: 26, mass: 0.6 } as const;
const springSoft = { type: 'spring', stiffness: 220, damping: 28, mass: 0.9 } as const;

// ==========================================
// 2. THREE.JS: Continuous Market Data Stream
// ==========================================
function DataPoints() {
    const pointsRef = useRef<any>(null);
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
                <bufferAttribute attach="attributes-position" args={[positions, 3]} />
            </bufferGeometry>
            <pointsMaterial size={0.045} color="#10B981" transparent opacity={0.8} sizeAttenuation />
        </points>
    );
}

// ==========================================
// 3. SIGNATURE ELEMENT: Cryptographic Prism
// ==========================================
function CryptographicCore() {
    const [hash, setHash] = useState('0x00000000');

    // Idle motion element: Simulates a live encryption key calculation
    useEffect(() => {
        const interval = setInterval(() => {
            const randomHash = Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0').toUpperCase();
            setHash(`0x${randomHash}`);
        }, 150);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="absolute inset-0 flex flex-col items-center justify-center overflow-hidden perspective-1000">
            {/* The 3D Glass Prism */}
            <div className="relative w-48 h-48 flex items-center justify-center transform-style-3d">
                <motion.div
                    animate={{ rotateX: [0, 360], rotateY: [0, 180] }}
                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 rounded-[2rem]"
                    style={glass.nested}
                />
                <motion.div
                    animate={{ rotateX: [180, 0], rotateY: [0, 360], rotateZ: [0, 90] }}
                    transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 rounded-[2rem]"
                    style={glass.pill}
                />
                <motion.div
                    animate={{ scale: [0.9, 1.1, 0.9], opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="w-4 h-4 rounded-full bg-emerald-500 shadow-[0_0_30px_rgba(16,185,129,1)]"
                />
            </div>

            {/* Live Data Stream Terminal */}
            <div className="absolute bottom-12 flex flex-col items-center gap-2">
                <div className="flex justify-between w-48 text-[9px] font-bold tracking-[0.18em] text-white/40 uppercase mb-1">
                    <span>Session Key</span>
                    <span className="text-emerald-400">Live</span>
                </div>
                <div className="w-48 p-3 rounded-[1rem] flex items-center justify-between" style={glass.pill}>
                    <span className="font-mono text-sm font-bold tracking-widest text-white/80">{hash}</span>
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                </div>
            </div>
        </div>
    );
}

// ==========================================
// 4. MAIN AUTH COMPONENT
// ==========================================
export default function Auth() {
    const navigate = useNavigate();
    const { fetchProfile } = useAuth();
    const [mode, setMode] = useState<'login' | 'register'>('login');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setErrorMsg(null);
        try {
            if (mode === 'register') {
                const { data, error } = await supabase.auth.signUp({
                    email,
                    password,
                });
                if (error) throw error;
                if (data.session) {
                    const profile = await fetchProfile(data.session.access_token);
                    if (profile) {
                        navigate('/workspace');
                    } else {
                        navigate('/onboarding');
                    }
                } else {
                    setErrorMsg("Verification email sent or account initialized. Please sign in.");
                    setMode('login');
                }
            } else {
                const { data, error } = await supabase.auth.signInWithPassword({
                    email,
                    password,
                });
                if (error) throw error;
                if (data.session) {
                    const profile = await fetchProfile(data.session.access_token);
                    if (profile) {
                        navigate('/workspace');
                    } else {
                        navigate('/onboarding');
                    }
                }
            }
        } catch (err: any) {
            setErrorMsg(err.message || 'Authentication failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative w-full min-h-screen bg-[#030508] text-white overflow-hidden font-sans flex flex-col perspective-1000">
            {/* CSS to strip browser autofill styling so it doesn't break the glass */}
            <style>{`
                input:-webkit-autofill,
                input:-webkit-autofill:hover, 
                input:-webkit-autofill:focus, 
                input:-webkit-autofill:active{
                    -webkit-box-shadow: 0 0 0 30px transparent inset !important;
                    -webkit-text-fill-color: white !important;
                    transition: background-color 5000s ease-in-out 0s;
                }
            `}</style>

            {/* FIXED BACKGROUNDS */}
            <div className="fixed inset-0 z-0 bg-grid pointer-events-none opacity-50" />
            <div className="fixed inset-0 z-0 mix-blend-screen pointer-events-none">
                <Canvas camera={{ position: [0, 0, 5] }}><DataPoints /></Canvas>
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

            {/* MINIMAL NAV */}
            <nav className="relative z-50 w-full px-8 md:px-16 py-8 flex justify-between items-center">
                <div
                    onClick={() => navigate('/')}
                    className="font-bold text-2xl tracking-tighter text-white flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
                >
                    INVR<span className="text-emerald-500">.</span>
                </div>

                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    transition={springPress}
                    onClick={() => navigate('/')}
                    className="flex items-center gap-2 p-3 rounded-full hover:bg-white/5 transition-colors text-white/50 hover:text-white"
                >
                    <X className="w-6 h-6" />
                </motion.button>
            </nav>

            {/* ASYMMETRIC AUTH TERMINAL */}
            <div className="flex-1 flex items-center justify-center p-6 relative z-10 w-full">
                <motion.div
                    initial={{ opacity: 0, y: 30, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={springSoft}
                    className="w-full max-w-4xl relative rounded-[2.5rem] flex flex-col md:flex-row min-h-[500px]"
                    style={{ transformStyle: "preserve-3d" }}
                >
                    <div className="absolute inset-0 rounded-[2.5rem] overflow-hidden" style={glass.base} />
                    {/* LEFT PANE: Signature Element */}
                    <div className="hidden md:flex flex-1 relative border-r border-white/10 overflow-hidden">
                        {/* Huge background watermark for depth */}
                        <span aria-hidden="true" className="absolute -top-10 -left-10 text-[18rem] font-bold leading-none text-white/[0.02] select-none pointer-events-none tracking-tighter">
                            ID
                        </span>

                        <CryptographicCore />
                    </div>

                    {/* RIGHT PANE: Pure Auth Form */}
                    <div className="flex-1 flex flex-col p-10 md:p-14 relative z-10">
                        {/* Header */}
                        <div className="mb-10">
                            <h2 className="text-4xl font-bold tracking-tighter text-white mb-2">
                                Authenticate.
                            </h2>
                            <p className="text-white/50 font-bold tracking-tighter text-sm leading-relaxed">
                                Establish your local portfolio state.
                            </p>
                        </div>

                        {/* Tab Switcher */}
                        <div className="flex gap-1 p-1.5 mb-8 rounded-[1.25rem] w-full" style={glass.pill}>
                            {['login', 'register'].map((tab) => {
                                const isActive = mode === tab;
                                return (
                                    <button
                                        key={tab}
                                        type="button"
                                        onClick={() => setMode(tab as 'login' | 'register')}
                                        className={`relative flex-1 py-3 text-[12px] font-bold tracking-widest uppercase transition-colors rounded-[1rem] z-10 ${isActive ? 'text-white' : 'text-white/40 hover:text-white/80'}`}
                                    >
                                        {isActive && (
                                            <motion.div
                                                layoutId="auth-tab-pill"
                                                className="absolute inset-0 rounded-[1rem] bg-white/[0.07]"
                                                style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.18)' }}
                                                transition={springSoft}
                                            />
                                        )}
                                        <span className="relative z-10">{tab === 'login' ? 'Sign In' : 'Initialize'}</span>
                                    </button>
                                );
                            })}
                        </div>

                        {/* Form Engine */}
                        <form onSubmit={handleAuth} className="flex flex-col gap-6 flex-1 justify-center">
                            <div className="flex flex-col gap-4">
                                {/* Email Field */}
                                <div
                                    className="relative rounded-[1.25rem] overflow-hidden group transition-colors duration-300"
                                    style={glass.nested}
                                >
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="Identification (Email)"
                                        required
                                        className="w-full bg-transparent px-6 py-5 outline-none text-white font-bold tracking-tighter placeholder-white/20 relative z-10"
                                    />
                                    <div className="absolute bottom-0 left-0 w-full h-[2px] bg-emerald-500/0 group-focus-within:bg-emerald-500/60 shadow-[0_0_10px_rgba(16,185,129,0)] group-focus-within:shadow-[0_0_15px_rgba(16,185,129,0.8)] transition-all duration-300" />
                                </div>

                                {/* Password Field */}
                                <div
                                    className="relative rounded-[1.25rem] overflow-hidden group transition-colors duration-300"
                                    style={glass.nested}
                                >
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="Cryptographic Key (Password)"
                                        required
                                        className="w-full bg-transparent px-6 py-5 outline-none text-white font-bold tracking-tighter placeholder-white/20 relative z-10"
                                    />
                                    <div className="absolute bottom-0 left-0 w-full h-[2px] bg-emerald-500/0 group-focus-within:bg-emerald-500/60 shadow-[0_0_10px_rgba(16,185,129,0)] group-focus-within:shadow-[0_0_15px_rgba(16,185,129,0.8)] transition-all duration-300" />
                                </div>
                            </div>

                            {errorMsg && (
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    style={glass.nested}
                                    className="p-4 rounded-[1.25rem] text-rose-400 text-sm font-bold tracking-tighter"
                                >
                                    {errorMsg}
                                </motion.div>
                            )}

                            {/* Forgot Password Link */}
                            <AnimatePresence>
                                {mode === 'login' && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: 'auto' }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="self-end overflow-hidden"
                                    >
                                        <button type="button" className="text-[11px] font-bold tracking-[0.18em] uppercase text-white/40 hover:text-emerald-400 transition-colors mt-2">
                                            Recover Key?
                                        </button>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            {/* Action Button */}
                            <div className="mt-2">
                                <motion.button
                                    type="submit"
                                    disabled={loading}
                                    whileHover={{ scale: loading ? 1 : 1.02 }}
                                    whileTap={{ scale: loading ? 1 : 0.98 }}
                                    animate={loading ? {} : {
                                        boxShadow: [
                                            '0 0 20px rgba(255,255,255,0.1)',
                                            '0 0 35px rgba(255,255,255,0.2)',
                                            '0 0 20px rgba(255,255,255,0.1)',
                                        ],
                                    }}
                                    transition={{
                                        scale: springPress,
                                        boxShadow: { duration: 3, repeat: Infinity, ease: 'easeInOut' },
                                    }}
                                    className="w-full py-5 rounded-[1.25rem] bg-white text-black font-bold tracking-tighter flex items-center justify-center gap-3 hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? 'Processing...' : (mode === 'login' ? 'Grant Access' : 'Establish Identity')}
                                    <ArrowRight className="w-4 h-4" strokeWidth={2.5} />
                                </motion.button>
                            </div>
                        </form>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}