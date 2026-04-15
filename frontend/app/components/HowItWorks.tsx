export default function HowItWorks() {
  const steps = [
    {
      number: "01",
      title: "Define Your Profile",
      description:
        "Tell us your risk appetite and timeline. We use anonymized sector allocations — never your exact holdings.",
      tag: "Setup",
    },
    {
      number: "02",
      title: "Query the AI Agent",
      description:
        "Ask about a specific stock or sector. Get institutional-quality research in seconds.",
      tag: "Analyze",
    },
    {
      number: "03",
      title: "Receive Actionable Intelligence",
      description:
        "Get Entry, Target, and Stop Loss levels with detailed educational breakdowns.",
      tag: "Execute",
    },
  ];

  const cardBase =
    "rounded-xl border border-line bg-bg-surface p-5 w-full transition-all duration-300 hover:border-amber/30 hover:shadow-[0_0_24px_-6px_rgba(245,158,11,0.15)] group";

  return (
    <section id="how-it-works" className="relative py-24 lg:py-32">
      <div className="relative z-10 max-w-[1400px] mx-auto px-8 xl:px-12">
        {/* Section Header */}
        <div className="text-center mb-16 lg:mb-20">
          <span className="inline-block text-xs font-mono font-medium tracking-[0.2em] uppercase text-amber mb-4">
            How It Works
          </span>
          <h2 className="text-3xl lg:text-4xl font-semibold tracking-tight text-fg mb-4">
            Three Simple Steps
          </h2>
          <p className="text-sm lg:text-base text-fg-muted max-w-2xl mx-auto leading-relaxed">
            Get started in minutes. Our minimalist approach keeps things fast and easy, letting the AI do the heavy lifting of complex market analysis.
          </p>
        </div>

        {/* Mobile: stacked layout */}
        <div className="md:hidden space-y-8">
          {steps.map((step) => (
            <div key={step.number} className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-bg-surface border-2 border-amber/40 flex items-center justify-center shrink-0">
                <span className="text-xs font-mono font-bold text-amber">{step.number}</span>
              </div>
              <div>
                <span className="text-[10px] font-mono font-semibold uppercase tracking-[0.15em] text-amber/70 bg-amber/[0.07] px-2 py-0.5 rounded-md inline-block mb-2">{step.tag}</span>
                <h3 className="text-base font-semibold text-fg mb-1.5">{step.title}</h3>
                <p className="text-sm text-fg-muted leading-relaxed">{step.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Desktop: zigzag horizontal layout */}
        <div className="hidden md:block relative mx-auto">

          {/* Zigzag SVG connectors */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
            <line x1="16.67%" y1="32%" x2="33%" y2="50%" stroke="#F59E0B" strokeOpacity="0.25" strokeWidth="1" strokeDasharray="4 4" />
            <line x1="33%" y1="50%" x2="50%" y2="68%" stroke="#F59E0B" strokeOpacity="0.25" strokeWidth="1" strokeDasharray="4 4" />
            <line x1="50%" y1="68%" x2="67%" y2="50%" stroke="#F59E0B" strokeOpacity="0.25" strokeWidth="1" strokeDasharray="4 4" />
            <line x1="67%" y1="50%" x2="83.33%" y2="32%" stroke="#F59E0B" strokeOpacity="0.25" strokeWidth="1" strokeDasharray="4 4" />
          </svg>

          <div className="grid grid-cols-3 gap-8 relative z-10">
            {/* Step 01 — top */}
            <div className="flex flex-col items-center pb-24">
              <div className={cardBase}>
                <span className="text-[10px] font-mono font-semibold uppercase tracking-[0.15em] text-amber/70 bg-amber/[0.07] px-2.5 py-1 rounded-md inline-block mb-3">{steps[0].tag}</span>
                <h3 className="text-[15px] font-semibold text-fg mb-2 tracking-tight group-hover:text-amber transition-colors duration-300">{steps[0].title}</h3>
                <p className="text-sm text-fg-muted leading-relaxed">{steps[0].description}</p>
              </div>
              <div className="w-px h-5 bg-gradient-to-b from-amber/30 to-transparent" />
              <div className="w-10 h-10 rounded-full bg-bg border-2 border-amber/40 flex items-center justify-center">
                <span className="text-xs font-mono font-bold text-amber">{steps[0].number}</span>
              </div>
            </div>

            {/* Step 02 — bottom (shifted down) */}
            <div className="flex flex-col items-center pt-24">
              <div className="w-10 h-10 rounded-full bg-bg border-2 border-amber/40 flex items-center justify-center">
                <span className="text-xs font-mono font-bold text-amber">{steps[1].number}</span>
              </div>
              <div className="w-px h-5 bg-gradient-to-b from-amber/30 to-transparent" />
              <div className={cardBase}>
                <span className="text-[10px] font-mono font-semibold uppercase tracking-[0.15em] text-amber/70 bg-amber/[0.07] px-2.5 py-1 rounded-md inline-block mb-3">{steps[1].tag}</span>
                <h3 className="text-[15px] font-semibold text-fg mb-2 tracking-tight group-hover:text-amber transition-colors duration-300">{steps[1].title}</h3>
                <p className="text-sm text-fg-muted leading-relaxed">{steps[1].description}</p>
              </div>
            </div>

            {/* Step 03 — top */}
            <div className="flex flex-col items-center pb-24">
              <div className={cardBase}>
                <span className="text-[10px] font-mono font-semibold uppercase tracking-[0.15em] text-amber/70 bg-amber/[0.07] px-2.5 py-1 rounded-md inline-block mb-3">{steps[2].tag}</span>
                <h3 className="text-[15px] font-semibold text-fg mb-2 tracking-tight group-hover:text-amber transition-colors duration-300">{steps[2].title}</h3>
                <p className="text-sm text-fg-muted leading-relaxed">{steps[2].description}</p>
              </div>
              <div className="w-px h-5 bg-gradient-to-b from-amber/30 to-transparent" />
              <div className="w-10 h-10 rounded-full bg-bg border-2 border-amber/40 flex items-center justify-center">
                <span className="text-xs font-mono font-bold text-amber">{steps[2].number}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
