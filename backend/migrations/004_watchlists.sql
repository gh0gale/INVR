-- 004_watchlists.sql
-- Audit finding NEW-FE-15 (Low) - 2026-08-23
--
-- The workspace watchlist was React state. It started empty on every reload and
-- was lost on sign-out, which made the star button look broken rather than
-- ephemeral. This is the table behind it.
--
-- Unlike `algorithmic_ledger`, a watchlist IS personal data, so it carries a
-- user_id and the client is allowed to write its own rows directly. There is no
-- backend endpoint for it and none is needed: the row is (user, ticker) and
-- nothing about it is derived, so routing it through FastAPI would add a hop
-- and no validation the database is not already doing.

begin;

create table if not exists public.watchlists (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null references auth.users(id) on delete cascade,
    ticker     text not null,
    created_at timestamptz not null default now(),
    -- One row per user per ticker. The frontend toggle relies on this to make
    -- a double-click idempotent rather than producing duplicates.
    unique (user_id, ticker)
);

create index if not exists watchlists_user_idx
    on public.watchlists (user_id, created_at desc);

alter table public.watchlists enable row level security;

-- Table-level privileges. RLS decides WHICH rows a role may touch; it cannot
-- grant access that was never given in the first place, and a table created by
-- raw SQL does not necessarily inherit the default privileges that Supabase
-- applies to tables made through its dashboard. Without this the policy below
-- is correct and unreachable, and every client call returns
-- `42501 permission denied for table watchlists`.
--
-- `anon` is deliberately not granted: an unauthenticated client has no
-- auth.uid(), so the policy would deny it anyway and a grant would only widen
-- the surface for no benefit.
grant select, insert, update, delete on public.watchlists to authenticated;

-- Read, insert and delete are all scoped to the owner. `with check` is what
-- stops a client inserting a row attributed to somebody else; `using` alone
-- would leave that open.
drop policy if exists watchlists_own on public.watchlists;
create policy watchlists_own
  on public.watchlists
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

commit;

-- Verification, signed in as a normal user:
--   insert into public.watchlists (user_id, ticker)
--     values (auth.uid(), 'TEST.NS');            -- succeeds
--   insert into public.watchlists (user_id, ticker)
--     values (gen_random_uuid(), 'TEST.NS');     -- denied by with check
--   select count(*) from public.watchlists;      -- only your own
