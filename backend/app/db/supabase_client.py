import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# We prioritize the Service Role key for backend operations to bypass RLS
url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))

supabase_client: Client = create_client(url, key)
