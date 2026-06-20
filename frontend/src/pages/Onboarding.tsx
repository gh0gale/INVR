import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, IndianRupee, ShieldAlert, Target, Clock, Zap } from 'lucide-react';

const steps = [
    { id: 'experience', title: 'Experience Level', icon: Zap, options: ['Beginner', 'Intermediate', 'Advanced'] },
    { id: 'goal', title: 'Primary Goal', icon: Target, options: ['Wealth Growth', 'Dividend Income', 'Capital Preservation'] },
    { id: 'timeframe', title: 'Trading Style', icon: Clock, options: ['Intraday', 'Swing', 'Positional', 'Long-term'] },
    { id: 'risk', title: 'Risk Tolerance', icon: ShieldAlert, options: ['Conservative', 'Moderate', 'Aggressive'] }
];

export default function Onboarding() {
    const navigate = useNavigate();
    const [currentStep, setCurrentStep] = useState(0);
    const [profile, setProfile] = useState<Record<string, string>>({});
    const [capital, setCapital] = useState("100000");

    const handleSelect = (option: string) => {
        setProfile({ ...profile, [steps[currentStep].id]: option });
        if (currentStep < steps.length - 1) {
            setTimeout(() => setCurrentStep(curr => curr + 1), 300);
        }
    };

    // const isLastStep = currentStep === steps.length - 1;

    return (
        <div className="w-screen h-screen flex flex-col items-center justify-center p-6">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-2xl glass-panel rounded-3xl p-10 flex flex-col relative overflow-hidden"
            >
                {/* Progress Bar */}
                <div className="absolute top-0 left-0 h-1 bg-white/5 w-full">
                    <motion.div
                        className="h-full bg-neon-cyan shadow-[0_0_10px_rgba(0,240,255,0.5)]"
                        initial={{ width: "0%" }}
                        animate={{ width: `${((currentStep + 1) / (steps.length + 1)) * 100}%` }}
                        transition={{ ease: "easeInOut", duration: 0.5 }}
                    />
                </div>

                <div className="mb-10 text-center">
                    <h2 className="text-3xl font-light tracking-tight text-white mb-2">Configure Engine</h2>
                    <p className="text-gray-400 font-light">Calibrating parameters for your specific risk vector.</p>
                </div>

                <div className="flex-1 min-h-[300px] flex flex-col justify-center">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={currentStep}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ duration: 0.3 }}
                            className="flex flex-col items-center w-full"
                        >
                            {currentStep < steps.length ? (
                                <>
                                    <div className="flex items-center gap-3 mb-8">
                                        {steps[currentStep].icon({ className: "w-6 h-6 text-neon-cyan" })}
                                        <h3 className="text-xl font-medium text-gray-200">{steps[currentStep].title}</h3>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
                                        {steps[currentStep].options.map((opt) => {
                                            const isActive = profile[steps[currentStep].id] === opt;
                                            return (
                                                <button
                                                    key={opt}
                                                    onClick={() => handleSelect(opt)}
                                                    className={`relative p-6 rounded-xl border transition-all duration-300 flex items-center justify-center text-sm font-medium ${isActive
                                                        ? 'border-neon-cyan bg-neon-cyan/10 text-white shadow-[0_0_20px_rgba(0,240,255,0.15)]'
                                                        : 'border-white/5 bg-white/[0.02] text-gray-400 hover:bg-white/[0.05] hover:border-white/20'
                                                        }`}
                                                >
                                                    {opt}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </>
                            ) : (
                                // Final Step: Capital Input
                                <div className="flex flex-col items-center w-full max-w-md">
                                    <div className="flex items-center gap-3 mb-8">
                                        <IndianRupee className="w-6 h-6 text-neon-cyan" />
                                        <h3 className="text-xl font-medium text-gray-200">Allocated Capital</h3>
                                    </div>
                                    <div className="relative w-full">
                                        <span className="absolute left-6 top-1/2 -translate-y-1/2 text-2xl text-gray-500 font-mono">₹</span>
                                        <input
                                            type="number"
                                            value={capital}
                                            onChange={(e) => setCapital(e.target.value)}
                                            className="w-full bg-obsidian-900 border border-white/10 rounded-xl py-6 pl-14 pr-6 text-3xl font-mono text-white outline-none focus:border-neon-cyan transition-colors shadow-inner"
                                        />
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    </AnimatePresence>
                </div>

                {/* Navigation */}
                <div className="mt-10 flex justify-between items-center w-full">
                    <button
                        onClick={() => setCurrentStep(curr => Math.max(0, curr - 1))}
                        className={`text-sm text-gray-500 hover:text-white transition-colors ${currentStep === 0 ? 'opacity-0 pointer-events-none' : ''}`}
                    >
                        Back
                    </button>

                    <button
                        onClick={() => {
                            if (currentStep === steps.length) navigate('/workspace');
                            else setCurrentStep(curr => curr + 1);
                        }}
                        disabled={currentStep < steps.length && !profile[steps[currentStep].id]}
                        className="flex items-center gap-2 px-6 py-3 bg-white text-obsidian-900 rounded-full font-medium hover:bg-neon-cyan transition-colors disabled:opacity-50 disabled:hover:bg-white"
                    >
                        {currentStep === steps.length ? 'Initialize Engine' : 'Next'}
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
            </motion.div>
        </div>
    );
}