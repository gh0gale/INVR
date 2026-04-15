import Navbar from "./components/Navbar";
import DashboardMockup from "./components/DashboardMockup";
import Features from "./components/Features";
import HowItWorks from "./components/HowItWorks";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Hero Section */}
      <section id="hero" className="relative z-10 pt-[72px]">
        <div className="max-w-[1400px] mx-auto px-8 xl:px-12">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center min-h-[calc(100vh-72px)] py-16 lg:py-0">
            {/* Left: Text Content */}
            <div className="lg:col-span-5">
              {/* Eyebrow */}
              <div className="flex items-center gap-2.5 mb-6">
                <div className="h-px w-8 bg-amber/60" />
                <span className="text-xs font-mono font-medium tracking-[0.2em] uppercase text-amber">
                  AI-Powered Intelligence
                </span>
              </div>

              <h1
                id="hero-headline"
                className="text-4xl lg:text-5xl xl:text-[3.5rem] font-semibold leading-[1.1] tracking-tight text-fg mb-6"
              >
                Structured Intelligence for,{" "}
                <span className="text-fg-muted">Modern Investors.</span>
              </h1>

              <p
                id="hero-subheadline"
                className="text-base lg:text-lg text-fg-muted leading-relaxed mb-10 max-w-md"
              >
                Privacy-aware, personalized stock analysis and contextual
                financial education without linking your brokerage accounts.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <a
                  href="#"
                  id="cta-primary"
                  className="inline-flex items-center justify-center px-7 py-3.5 text-sm font-medium rounded-md bg-white text-black hover:bg-neutral-200 transition-all duration-200 group"
                >
                  Get Your Free Analysis
                  <svg
                    width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                    className="ml-2 group-hover:translate-x-0.5 transition-transform duration-200"
                  >
                    <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </a>
                <a
                  href="#how-it-works"
                  id="cta-secondary"
                  className="inline-flex items-center justify-center px-7 py-3.5 text-sm font-medium rounded-md border border-line-light text-fg-muted hover:text-fg hover:border-neutral-600 transition-all duration-200"
                >
                  See How It Works
                </a>
              </div>

              {/* Trust Metrics */}
              <div className="flex items-center gap-6 mt-10 pt-8 border-t border-line">
                <div>
                  <div className="text-lg font-semibold text-fg font-mono">12K+</div>
                  <div className="text-[11px] text-fg-faint uppercase tracking-wide mt-0.5">Analyses Run</div>
                </div>
                <div className="w-px h-8 bg-line" />
                <div>
                  <div className="text-lg font-semibold text-fg font-mono">500+</div>
                  <div className="text-[11px] text-fg-faint uppercase tracking-wide mt-0.5">Stocks Covered</div>
                </div>
                <div className="w-px h-8 bg-line" />
                <div>
                  <div className="text-lg font-semibold text-fg font-mono">4.8</div>
                  <div className="text-[11px] text-fg-faint uppercase tracking-wide mt-0.5">User Rating</div>
                </div>
              </div>
            </div>

            {/* Right: Dashboard Visual */}
            <div className="lg:col-span-7 flex justify-center lg:justify-end">
              <DashboardMockup />
            </div>
          </div>
        </div>

        {/* Subtle section divider */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-line-light to-transparent" />
      </section>

      {/* Divider */}
      <div className="h-px bg-gradient-to-r from-transparent via-line-light to-transparent" />

      <Features />

      {/* Divider */}
      <div className="h-px bg-gradient-to-r from-transparent via-line-light to-transparent" />

      <HowItWorks />

      <Footer />
    </div>
  );
}
