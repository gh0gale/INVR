-- 005_horizons_and_tour.sql
-- 2026-09-28. Workspace features (docs/workspace_features_plan.md).
--
-- 1. user_profiles.tour_completed_at: the first-login workspace tour is shown
--    while this is null and stamped when the user finishes or skips it. Kept on
--    the server so a second device does not replay it.
-- 2. stock_horizons: the horizon a user last ran a ticker on. The horizons are
--    the engine's own four (intraday, swing, positional, long_term); a ticker
--    with no row uses user_profiles.timeframe, the onboarding choice.
--
-- Rows are written by the backend (PUT /api/v1/horizons/stock/{ticker}) through
-- the service role after auth. RLS and the grant below still let a signed-in
-- client read its own rows.

begin;

alter table public.user_profiles
    add column if not exists tour_completed_at timestamptz;

create table if not exists public.stock_horizons (
    user_id    uuid not null references auth.users(id) on delete cascade,
    ticker     text not null,
    timeframe  text not null check (timeframe in ('intraday', 'swing', 'positional', 'long_term')),
    updated_at timestamptz not null default now(),
    primary key (user_id, ticker)
);

alter table public.stock_horizons enable row level security;

grant select on public.stock_horizons to authenticated;

drop policy if exists stock_horizons_own_read on public.stock_horizons;
create policy stock_horizons_own_read on public.stock_horizons
    for select using (auth.uid() = user_id);

commit;
