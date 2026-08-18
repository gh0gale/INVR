import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './context/auth';
import Landing from './pages/Landing';
import Onboarding from './pages/Onboarding';
import Auth from './pages/Auth';

/*
  Split off the routes a first-time visitor does not need. The landing page is
  the entry point and stays in the main chunk; the workspace pulls in the whole
  analysis component tree, and the legal pages are rarely the first stop.
*/
const Workspace = lazy(() => import('./pages/Workspace'));
const Terms = lazy(() => import('./pages/Terms'));
const Privacy = lazy(() => import('./pages/Privacy'));
import { ErrorBoundary } from './components/ErrorBoundary';

/** Session check in progress. States what is happening rather than spinning. */
function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-term-950" role="status">
      <div className="flex flex-col items-center gap-3">
        <span className="text-2xl font-bold tracking-tight text-fg">INVR<span className="text-accent">.</span></span>
        <span className="label">Checking your session</span>
        <span className="skeleton h-px w-40" />
      </div>
    </div>
  );
}

function ProtectedRoute({
  children,
  requireProfile = true,
}: {
  children: React.ReactElement;
  requireProfile?: boolean;
}) {
  const { user, loading, profile } = useAuth();
  const location = useLocation();

  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/auth" state={{ from: location }} replace />;
  if (requireProfile && !profile) return <Navigate to="/onboarding" replace />;
  if (!requireProfile && profile) return <Navigate to="/workspace" replace />;

  return children;
}

/** Blocks /auth once a session exists. */
function PublicRoute({ children }: { children: React.ReactElement }) {
  const { user, loading, profile } = useAuth();

  if (loading) return <LoadingScreen />;
  if (user) return <Navigate to={profile ? '/workspace' : '/onboarding'} replace />;

  return children;
}

function AppRoutes() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />

      <Route
        path="/auth"
        element={
          <PublicRoute>
            <Auth />
          </PublicRoute>
        }
      />

      <Route
        path="/onboarding"
        element={
          <ProtectedRoute requireProfile={false}>
            <Onboarding />
          </ProtectedRoute>
        }
      />

      <Route
        path="/workspace"
        element={
          <ProtectedRoute requireProfile={true}>
            <Workspace />
          </ProtectedRoute>
        }
      />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ErrorBoundary>
  );
}
