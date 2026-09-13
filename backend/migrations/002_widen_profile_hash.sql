-- 002_widen_profile_hash.sql
-- Optional. Reconciles schema drift found on 2026-08-18.
--
-- Appendix B of master_documentation.md declares:
--     profile_version_hash TEXT
-- but at least one live deployment has:
--     profile_version_hash VARCHAR(32)
-- sized back when the value was an MD5 digest.
--
-- That drift is what let a 64-char SHA-256 digest ship: the documented DDL
-- said it would fit. Postgres rejected every profile upsert with
--     22001  value too long for type character varying(32)
-- which reached the user as a database error while entering their capital.
--
-- The application code is the real fix and is already deployed: it truncates to
-- HASH_LENGTH (32) in app/schemas/profile.py, so it is correct against BOTH
-- column definitions and this migration is not required.
--
-- Run it only to make every deployment match the documented schema. Doing so
-- does not change behaviour on its own; raising HASH_LENGTH afterwards would,
-- and would invalidate existing hashes (they are change-detection values, so
-- the only effect is that every profile reads as "changed" once).
--
-- Apply with:  supabase db execute -f backend/migrations/002_widen_profile_hash.sql

begin;

alter table public.user_profiles
  alter column profile_version_hash type text;

commit;

-- Verification (expect: text)
--   select data_type, character_maximum_length
--   from information_schema.columns
--   where table_name = 'user_profiles' and column_name = 'profile_version_hash';
