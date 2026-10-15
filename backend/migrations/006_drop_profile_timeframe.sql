-- 006_drop_profile_timeframe.sql
-- 2026-10-15. The horizon is no longer asked for in onboarding or stored
-- anywhere: the workspace selector holds it for the current session and sends
-- it with each run.
--
-- 1. user_profiles.timeframe was NOT NULL. The backend no longer writes it, so
--    every profile save would fail until the constraint is dropped. The column
--    is kept (existing rows keep their old value, nothing reads it).
-- 2. stock_horizons (migration 005) is unused. On the live database it also
--    lacks the `timeframe` column ("Could not find the 'timeframe' column of
--    'stock_horizons' in the schema cache", PGRST204), so it never held data.

begin;

alter table public.user_profiles
    alter column timeframe drop not null;

drop table if exists public.stock_horizons;

commit;

-- PostgREST caches the schema; reload it so the change is seen at once.
notify pgrst, 'reload schema';
