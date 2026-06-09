from supabase import create_client, Client
from app.config import settings

if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY or not settings.SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing Supabase configuration credentials.")

# Standard client (used for verifying JWTs)
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

# Admin client (bypasses RLS - ONLY use this after verifying the user)
supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)