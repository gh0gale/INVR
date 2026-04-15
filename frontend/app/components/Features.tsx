export default function Features() {
  const features = [
    {
      id: "feature-privacy",
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
      ),
      title: "Privacy-First Profiling",
      description: "Get tailored advice using only approximate sector allocations. No exact holdings required.",
    },
    {
      id: "feature-analysis",
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 3v18h18" />
          <path d="M7 16l4-8 4 4 5-9" />
        </svg>
      ),
      title: "Professional-Grade Analysis",
      description: "Multi-dimensional scoring across macro, fundamental, technical, and risk metrics.",
    },
    {
      id: "feature-education",
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          <path d="M8 7h8" />
          <path d="M8 11h6" />
        </svg>
      ),
      title: "Contextual Education",
      description: "Learn the 'why' behind every recommendation with our integrated knowledge engine.",
    },
  ];

  return (
    <section id="features" className="relative z-10 py-24 lg:py-32">
      <div className="max-w-[1400px] mx-auto px-8 xl:px-12">
        {/* Section Header */}
        <div className="text-center mb-16 lg:mb-20">
          <span className="inline-block text-xs font-mono font-medium tracking-[0.2em] uppercase text-amber mb-4">
            Platform Capabilities
          </span>
          <h2 className="text-3xl lg:text-4xl font-semibold tracking-tight text-fg max-w-xl mx-auto mb-4">
            Smarter Investing, Zero Compromises.
          </h2>
          <p className="text-sm lg:text-base text-fg-muted max-w-2xl mx-auto leading-relaxed">
            We bridge the gap between institutional-grade stock analysis and retail investing, providing clear, actionable insights powered by cutting-edge AI.
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {features.map((feature) => (
            <div
              key={feature.id}
              id={feature.id}
              className="group relative rounded-lg border border-line bg-bg-surface p-6 lg:p-8 transition-all duration-300 hover:border-amber/30 hover:shadow-[0_0_24px_-6px_rgba(245,158,11,0.15)] hover:-translate-y-0.5"
            >
              {/* Icon */}
              <div className="w-10 h-10 rounded-md bg-amber/10 flex items-center justify-center text-amber mb-5">
                {feature.icon}
              </div>

              {/* Content */}
              <h3 className="text-base font-semibold text-fg mb-2.5 tracking-tight">
                {feature.title}
              </h3>
              <p className="text-sm leading-relaxed text-fg-muted">
                {feature.description}
              </p>

              {/* Subtle hover accent line at bottom */}
              <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-amber/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-b-lg" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
