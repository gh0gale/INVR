import { login, signup, signInWithGoogle } from './actions'
import Link from 'next/link'

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  const resolvedParams = await searchParams;
  const error = resolvedParams?.error as string;
  const message = resolvedParams?.message as string;
  const isSignUp = resolvedParams?.mode === 'signup';

  return (
    <div className="flex h-screen w-full items-center justify-center p-4">
      {/* Decorative Grid is already natively in globals.css applied to the body! */}
      
      <div className="relative animate-in flex-1 flex flex-col w-full justify-center max-w-sm border border-line bg-bg/60 backdrop-blur-xl rounded-2xl shadow-xl z-10 transition-all">
        {/* Glow behind the form */}
        <div className="absolute inset-0 z-0 bg-gradient-to-b from-amber/5 to-transparent rounded-2xl blur-3xl pointer-events-none"></div>
        
        <div className="relative z-10 p-8 text-fg">
          <div className="text-center mb-8">
            <Link href="/" className="inline-flex items-center justify-center gap-1 group mb-4">
              <span className="text-2xl font-bold tracking-tight text-fg">
                INVR<span className="text-amber">.</span>
              </span>
            </Link>
            <h2 className="text-xl font-semibold tracking-tight">
              {isSignUp ? 'Create your account' : 'Welcome back'}
            </h2>
            <p className="text-sm text-fg-muted mt-1">
              {isSignUp ? 'Enter your details to get started.' : 'Log in to your account.'}
            </p>
          </div>

          {error && (
             <div className="bg-loss/10 border border-loss/20 text-loss text-sm px-4 py-3 rounded-lg mb-6 backdrop-blur-sm">
               {error}
             </div>
          )}

          {message && (
             <div className="bg-gain/10 border border-gain/20 text-gain text-sm px-4 py-3 rounded-lg mb-6 backdrop-blur-sm">
               {message}
             </div>
          )}

          <form className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-fg-muted" htmlFor="email">
                Email address
              </label>
              <input
                className="rounded-lg px-4 py-2.5 border border-line bg-bg focus:border-amber focus:ring-1 focus:ring-amber/50 focus:outline-none text-fg placeholder:text-fg-faint transition-all"
                name="email"
                type="email"
                placeholder="you@example.com"
                required
              />
            </div>
            
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-fg-muted" htmlFor="password">
                Password
              </label>
              <input
                className="rounded-lg px-4 py-2.5 border border-line bg-bg focus:border-amber focus:ring-1 focus:ring-amber/50 focus:outline-none text-fg placeholder:text-fg-faint transition-all"
                type="password"
                name="password"
                placeholder="••••••••"
                required
                minLength={6}
              />
            </div>
            
            <div className="flex flex-col gap-3 mt-4">
              {isSignUp ? (
                <button formAction={signup} className="w-full bg-amber text-black rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-amber/90 transition-all duration-200 shadow-[0_0_15px_rgba(245,158,11,0.2)] active:scale-[0.98]">
                  Sign Up
                </button>
              ) : (
                <button formAction={login} className="w-full bg-white text-black rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-neutral-200 transition-all duration-200 shadow-[0_0_15px_rgba(255,255,255,0.05)] active:scale-[0.98]">
                  Sign In
                </button>
              )}
            </div>
          </form>

          <div className="mt-6 text-center text-sm text-fg-muted">
            {isSignUp ? (
              <>
                Already have an account?{' '}
                <Link href="/login" className="text-amber hover:underline underline-offset-4">
                  Sign in
                </Link>
              </>
            ) : (
              <>
                Don&apos;t have an account?{' '}
                <Link href="/login?mode=signup" className="text-amber hover:underline underline-offset-4">
                  Sign up
                </Link>
              </>
            )}
          </div>

          <div className="mt-8 mb-6 flex items-center justify-center overflow-visible">
             <div className="w-full h-px bg-line"></div>
             <span className="absolute px-4 text-xs font-semibold text-fg-faint bg-bg tracking-wider uppercase">OR</span>
          </div>

          <form action={signInWithGoogle}>
             <button className="w-full flex items-center justify-center gap-3 bg-bg-surface border border-line py-2.5 rounded-lg text-sm font-medium text-fg hover:bg-[#1a1a1a] transition-all active:scale-[0.98]">
               <svg xmlns="http://www.w3.org/2000/svg" height="18" viewBox="0 0 24 24" width="18">
                 <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                 <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                 <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                 <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                 <path d="M1 1h22v22H1z" fill="none"/>
               </svg>
               Continue with Google
             </button>
          </form>

        </div>
      </div>
    </div>
  )
}
