-- 003_user_scoped_history.sql
-- Audit findings ISO-01 .. ISO-05 (Critical) - 2026-08-23
--
-- Reported symptom: two different accounts signed in and saw the same stocks
-- in the workspace sidebar.
--
-- Cause: `algorithmic_ledger` carries no user_id, and the workspace read it
-- directly with `select * order by created_at limit 50`. Every account was
-- therefore shown the same globally-most-recent rows.
--
-- The fix is NOT to add user_id to `algorithmic_ledger`. That table is
-- deliberately shared: it is deduplicated on (ticker, timeframe, date,
-- pipeline_version) so that one deterministic verdict is stored once and
-- graded once by the Engine Room. Copying a row per user would multiply the
-- grading cohort and corrupt the accuracy statistics.
--
-- Ownership belongs on `prediction_interactions`, which already exists for
-- exactly this purpose ("which user saw which prediction") and which, until
-- now, was written but never read by anything.

begin;

-- ---------------------------------------------------------------- ownership
alter table public.prediction_interactions
  add column if not exists user_id uuid references auth.users(id);

-- The workspace lists a user's recent runs newest-first, so the index matches
-- the query rather than the column.
create index if not exists prediction_interactions_user_created_idx
  on public.prediction_interactions (user_id, created_at desc);

-- Existing rows predate the column and cannot be attributed: their session_id
-- was a per-mount random UUID that was never persisted anywhere. They stay
-- NULL, which the owner-scoped policy below excludes from every user's view.
-- No history is lost, because no user could correctly claim it.

-- ----------------------------------------------------------------- policies
alter table public.prediction_interactions enable row level security;

drop policy if exists interactions_read_own on public.prediction_interactions;
create policy interactions_read_own
  on public.prediction_interactions
  for select
  using (auth.uid() = user_id);

-- Writes stay server-side. 001 revoked them; repeated here so this file is
-- correct whether or not 001 has been applied.
revoke insert, update, delete on public.prediction_interactions from anon, authenticated;

-- ------------------------------------------------- tables that hold real PII
-- Neither of these was covered by 001. Without RLS, PostgREST exposes them to
-- anyone holding the anon key, which ships in the browser bundle. chat_sessions
-- holds verbatim conversation text; user_profiles holds capital amounts and the
-- accumulated semantic profile.

alter table public.chat_sessions enable row level security;
drop policy if exists chat_sessions_own on public.chat_sessions;
create policy chat_sessions_own
  on public.chat_sessions
  for select
  using (auth.uid() = user_id);
revoke insert, update, delete on public.chat_sessions from anon, authenticated;

alter table public.user_profiles enable row level security;
drop policy if exists user_profiles_own on public.user_profiles;
create policy user_profiles_own
  on public.user_profiles
  for select
  using (auth.uid() = id);
revoke insert, update, delete on public.user_profiles from anon, authenticated;

-- The backend reads and writes all three with the service role key, which
-- bypasses RLS, so the pipeline, the tutor and the profile endpoints are
-- unaffected.

commit;

-- Verification, signed in as a normal user:
--   select count(*) from public.prediction_interactions;  -- only your own
--   select count(*) from public.chat_sessions;            -- only your own
--   select count(*) from public.user_profiles;            -- exactly 1
