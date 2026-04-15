export default function Footer() {
  return (
    <footer id="footer" className="mt-8">
      {/* Disclaimer Banner */}
      <div className="bg-bg-card border-t border-line">
        <div className="max-w-[1400px] mx-auto px-8 xl:px-12 py-8">
          <div className="flex items-start gap-3">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-fg-faint shrink-0 mt-0.5">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4" strokeLinecap="round" />
              <path d="M12 16h.01" strokeLinecap="round" />
            </svg>
            <p className="text-xs leading-relaxed text-fg-faint">
              Educational and informational purposes only. Not SEBI-registered
              financial advice. AI Stock does not provide guarantees of any kind
              regarding the accuracy, completeness, or reliability of any
              analysis. Past performance is not indicative of future results.
              Always consult a qualified financial advisor before making
              investment decisions.
            </p>
          </div>
        </div>
      </div>

      {/* Footer Bottom */}
      <div className="bg-[#0E0E0E] border-t border-line">
        <div className="max-w-[1400px] mx-auto px-8 xl:px-12 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-fg-faint">© 2026 <span className="text-amber">INVR</span>. All rights reserved.</span>
            </div>
            <div className="flex items-center gap-6">
              <a href="#" className="text-xs text-fg-faint hover:text-fg-muted transition-colors duration-200">Privacy Policy</a>
              <a href="#" className="text-xs text-fg-faint hover:text-fg-muted transition-colors duration-200">Terms of Service</a>
              <a href="#" className="text-xs text-fg-faint hover:text-fg-muted transition-colors duration-200">Contact</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
