-- 001_ledger_rls.sql
-- Audit finding NEW-FE-02 (Critical) — 2026-08-18
--
-- The browser talks to `algorithmic_ledger` directly with the anon key. Before
-- this migration, a permissive policy meant any client could DELETE any row.
-- That table is the shared evaluation record the Engine Room grades against,
-- so a delete does not remove "my analysis": it destroys the evidence the whole
-- accuracy loop is built on.
--
-- Rows describe securities, not people. There is no user_id column and no PII,
-- so reading is safe to allow. Writing is not.
--
-- Apply with:  supabase db execute -f backend/migrations/001_ledger_rls.sql
-- or paste into the Supabase SQL editor.

begin;

alter table public.algorithmic_ledger enable row level security;

-- Reads: open. The public overview renders the most recent run, and the
-- workspace lists recent runs. Neither exposes anything user-identifying.
drop policy if exists ledger_read on public.algorithmic_ledger;
create policy ledger_read
  on public.algorithmic_ledger
  for select
  using (true);

-- Writes: server only. The backend uses the service role key, which bypasses
-- RLS, so the pipeline keeps writing normally. No policy is created for
-- insert/update/delete, which means every client attempt is denied.
revoke insert, update, delete on public.algorithmic_ledger from anon, authenticated;

-- Interaction rows reference the ledger and are written server-side too.
alter table public.prediction_interactions enable row level security;
revoke insert, update, delete on public.prediction_interactions from anon, authenticated;

commit;

-- Verification (expect: select succeeds, delete is denied)
--   select count(*) from public.algorithmic_ledger;
--   delete from public.algorithmic_ledger where false;
