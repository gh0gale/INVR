import { createContext, useContext } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import type { JsonObject } from '../types';

export interface UserProfile {
  id: string;
  experience: string;
  goal: string;
  timeframe: string;
  risk: string;
  portfolio: Record<string, number>;
  capital: number;
  profile_version_hash?: string;
  contradictions_flagged?: string[];
  semantic_profile?: JsonObject;
  created_at?: string;
}

export interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  profile: UserProfile | null;
  fetchProfile: (token: string) => Promise<UserProfile | null>;
  setProfileState: (profile: UserProfile | null) => void;
  logout: () => Promise<void>;
}

/**
 * Kept in a plain module rather than beside the provider so that the provider
 * file exports only a component, which is what fast refresh needs.
 */
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
