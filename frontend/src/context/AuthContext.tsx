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
  // Set when the profile could not be loaded, as distinct from not existing.
  const [profileError, setProfileError] = useState<string | null>(null);
  // Which user the current profile belongs to, so repeat events are ignored.
  const lastUserId = useRef<string | null>(null);

  /*
    Resolves to the profile, or null when the user genuinely has none (404).
    Any other outcome throws and sets profileError. It used to resolve null on
    a network failure too, and the router read that null as "new user": an
    existing account whose request was blocked (a CORS mismatch on the first
    deploy) was sent to onboarding, whose save then failed the same way
    (audit FE-AUTH-01).
  */
  const fetchProfile = async (token: string): Promise<UserProfile | null> => {
    let response: Response;
    try {
      response = await fetch(apiUrl('/api/v1/profiles/'), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    } catch (err) {
      console.error('Error fetching user profile:', err);
      const message =
        'Could not reach the INVR server, so your profile could not be loaded. Your account is unchanged. Try again in a moment.';
      setProfileError(message);
      throw new Error(message, { cause: err });
    }

    if (response.ok) {
      const data = await response.json();
      setProfile(data);
      setProfileError(null);
      return data;
    }
    if (response.status === 404) {
      setProfile(null);
      setProfileError(null);
      return null;
    }

    const message = `The server could not load your profile (error ${response.status}). Your account is unchanged. Try again in a moment.`;
    setProfileError(message);
    throw new Error(message);
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

      // A failure is recorded in profileError; the routes render it.
      if (initial) await fetchProfile(initial.access_token).catch(() => undefined);
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
        setProfileError(null);
        return;
      }

      // A token refresh or a focus-triggered replay of the same session needs
      // nothing more than the session update above.
      const nextUserId = nextSession.user?.id ?? null;
      if (nextUserId === lastUserId.current) return;

      lastUserId.current = nextUserId;
      void fetchProfile(nextSession.access_token).catch(() => undefined);
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
    setProfileError(null);
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, profile, profileError, fetchProfile, setProfileState, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
