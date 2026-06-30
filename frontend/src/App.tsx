import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Landing from './pages/Landing';
import Onboarding from './pages/Onboarding';
import Workspace from './pages/Workspace';
import Auth from './pages/Auth';
import { motion } from 'framer-motion';

// Premium loading screen keeping with liquid glass theme
function LoadingScreen() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#030508] text-white">
      <div className="relative w-24 h-24 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 rounded-[1rem] border-2 border-emerald-500/20 border-t-emerald-500"
        />
        <motion.span
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-400"
        >
          INVR
        </motion.span>
      </div>
    </div>
  );
}

// Protected Route Guard
function ProtectedRoute({ children, requireProfile = true }: { children: React.ReactElement; requireProfile?: boolean }) {
  const { user, loading, profile } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!user) {
    // Redirect to login page but save current location
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  if (requireProfile && !profile) {
    // Force onboarding if they don't have a profile
    return <Navigate to="/onboarding" replace />;
  }

  if (!requireProfile && profile) {
    // Already has profile, skip onboarding and go straight to workspace
    return <Navigate to="/workspace" replace />;
  }

  return children;
}

// Public Route Guard (blocks /auth if user is logged in)
function PublicRoute({ children }: { children: React.ReactElement }) {
  const { user, loading, profile } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (user) {
    if (profile) {
      return <Navigate to="/workspace" replace />;
    } else {
      return <Navigate to="/onboarding" replace />;
    }
  }

  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      
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

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;