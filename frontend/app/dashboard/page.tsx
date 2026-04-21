import { redirect } from 'next/navigation'
import { createClient } from '../../utils/supabase/server'

export default async function DashboardPage() {
  const supabase = await createClient()

  // Verify authentication directly to supabase
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    return redirect('/login')
  }

  // Example database hit
  // const { data } = await supabase.from('user_profiles').select('*').single()

  return (
    <div className="min-h-screen p-8 text-foreground bg-background">
      <header className="flex items-center justify-between mb-8 pb-4 border-b border-border">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <form action={async () => {
          'use server'
          const supabase = await createClient()
          await supabase.auth.signOut()
          redirect('/')
        }}>
          <button className="text-sm border border-border px-4 py-2 rounded hover:bg-neutral-900 transition-colors">
            Sign Out
          </button>
        </form>
      </header>
      
      <main className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Welcome to the AI-Stock Dashboard.</h2>
          <p className="text-muted-foreground text-sm">You are successfully natively signed in with Supabase Auth!</p>
        </div>

        <div className="p-4 border border-border rounded-lg bg-card text-card-foreground">
          <h3 className="font-semibold mb-1">Your Context Data (Supabase user):</h3>
          <p className="text-sm font-mono tracking-tight break-all">
             ID: {user.id}
          </p>
          <p className="mt-2 text-sm text-green-600 dark:text-green-400 font-medium">
            Email: {user.email}
          </p>
        </div>
      </main>
    </div>
  )
}
