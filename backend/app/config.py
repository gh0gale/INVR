import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    MARKET_SUFFIX: str = os.getenv("MARKET_SUFFIX", ".NS")
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    USE_RETRIEVAL_RAG: bool = os.getenv("USE_RETRIEVAL_RAG", "True").lower() in ("true", "1", "t", "yes")
    ROUTER_CONFIDENCE_THRESHOLD: float = float(os.getenv("ROUTER_CONFIDENCE_THRESHOLD", "0.45"))

settings = Settings()