"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { createClient } from "../../utils/supabase/client";
import { User } from "@supabase/supabase-js";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const supabase = createClient();
    
    // Initial fetch
    supabase.auth.getUser().then(({ data: { user } }) => setUser(user));

    // Listen for auth events
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      id="navbar"
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled
          ? "bg-bg/80 backdrop-blur-xl border-b border-line"
          : "bg-transparent"
        }`}
    >
      <div className="max-w-[1400px] mx-auto px-8 xl:px-12">
        <div className="flex items-center justify-between h-[72px]">
          {/* Logo */}
          <a href="#" id="logo" className="flex items-center group">
            <span className="text-xl font-bold tracking-tight text-fg">
              INVR<span className="text-amber">.</span>
            </span>
          </a>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-10">
            <a
              href="#features"
              id="nav-features"
              className="relative text-sm text-fg-muted hover:text-fg transition-colors duration-200 after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-px after:bg-amber after:transition-all after:duration-300 hover:after:w-full"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              id="nav-how-it-works"
              className="relative text-sm text-fg-muted hover:text-fg transition-colors duration-200 after:absolute after:bottom-[-4px] after:left-0 after:w-0 after:h-px after:bg-amber after:transition-all after:duration-300 hover:after:w-full"
            >
              How it Works
            </a>
            
            {!user ? (
               <Link
                 href="/login"
                 id="nav-cta"
                 className="text-sm font-medium px-5 py-2.5 rounded-md bg-white text-black hover:bg-neutral-200 transition-all duration-200"
               >
                 Client Login
               </Link>
            ) : (
               <Link
                 href="/dashboard"
                 id="nav-cta-dash"
                 className="text-sm font-medium px-5 py-2.5 rounded-md bg-white text-black hover:bg-neutral-200 transition-all duration-200"
               >
                 Dashboard
               </Link>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            id="mobile-menu-toggle"
            className="md:hidden p-2 text-fg-muted hover:text-fg transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle mobile menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              {mobileOpen ? (
                <>
                  <path d="M6 6L18 18" strokeLinecap="round" />
                  <path d="M18 6L6 18" strokeLinecap="round" />
                </>
              ) : (
                <>
                  <path d="M4 7H20" strokeLinecap="round" />
                  <path d="M4 12H20" strokeLinecap="round" />
                  <path d="M4 17H20" strokeLinecap="round" />
                </>
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        <div
          className={`md:hidden overflow-hidden transition-all duration-300 ${mobileOpen ? "max-h-60 pb-6" : "max-h-0"
            }`}
        >
          <div className="flex flex-col gap-4 pt-2 border-t border-line">
            <a href="#features" className="text-sm text-fg-muted hover:text-fg transition-colors py-2" onClick={() => setMobileOpen(false)}>
              Features
            </a>
            <a href="#how-it-works" className="text-sm text-fg-muted hover:text-fg transition-colors py-2" onClick={() => setMobileOpen(false)}>
              How it Works
            </a>
            {!user ? (
               <Link href="/login" className="text-sm font-medium px-5 py-2.5 rounded-md bg-white text-black text-center hover:bg-neutral-200 transition-all duration-200" onClick={() => setMobileOpen(false)}>
                 Login / Start Analyzing
               </Link>
            ) : (
               <Link href="/dashboard" className="text-sm font-medium px-5 py-2.5 rounded-md bg-white text-black text-center hover:bg-neutral-200 transition-all duration-200" onClick={() => setMobileOpen(false)}>
                 Dashboard
               </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
