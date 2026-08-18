import React, { useEffect, useRef, useState } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase } from '../supabase';
import { apiUrl } from '../api';
import { AuthContext, type UserProfile } from './auth';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  // Which user the current profile belongs to, so repeat events are ignored.
  const lastUserId = useRef<string | null>(null);

  const fetchProfile = async (token: string): Promise<UserProfile | null> => {
    try {
      const response = await fetch(apiUrl('/api/v1/profiles/'), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        return data;
      } else if (response.status === 404) {
        setProfile(null);
        return null;
      }
    } catch (err) {
      console.error('Error fetching user profile:', err);
    }
    return null;
  };

  const setProfileState = (prof: UserProfile | null) => {
    setProfile(prof);
  };

  useEffect(() => {
    let active = true;

    /*
      Supabase re-emits SIGNED_IN and TOKEN_REFRESHED whenever the tab regains
      focus. The previous handler flipped `loading` back to true on every one of
      those, which unmounted the whole routed tree and re-rendered the loading
      screen. That is what made switching Chrome tabs look like a full page
      reload, and it also wiped the workspace transcript and the selected stock.

      So: resolve `loading` exactly once, and afterwards only refetch the
      profile when the signed-in user actually changes.
    */
    const resolveInitial = async () => {
      const {
        data: { session: initial },
      } = await supabase.auth.getSession();

      if (!active) return;

      setSession(initial);
      setUser(initial?.user ?? null);
      lastUserId.current = initial?.user?.id ?? null;

      if (initial) await fetchProfile(initial.access_token);
      if (active) setLoading(false);
    };

    void resolveInitial();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, nextSession) => {
      if (!active) return;

      // Keep the token fresh for outgoing requests, but do not disturb the tree.
      setSession(nextSession);
      setUser(nextSession?.user ?? null);

      if (event === 'SIGNED_OUT' || !nextSession) {
        lastUserId.current = null;
        setProfile(null);
        return;
      }

      // A token refresh or a focus-triggered replay of the same session needs
      // nothing more than the session update above.
      const nextUserId = nextSession.user?.id ?? null;
      if (nextUserId === lastUserId.current) return;

      lastUserId.current = nextUserId;
      void fetchProfile(nextSession.access_token);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  const logout = async () => {
    await supabase.auth.signOut();
    lastUserId.current = null;
    setUser(null);
    setSession(null);
    setProfile(null);
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, profile, fetchProfile, setProfileState, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
