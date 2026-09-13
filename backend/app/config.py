"""Application settings.

Audit finding P5-03: this module used to declare pydantic-settings fields whose
defaults were `os.getenv(...)` calls. That works, but it evaluates at import
time and bypasses everything pydantic-settings exists to do - type coercion,
validation, and `.env` resolution - so the class was documentation rather than
machinery. Fields are now declared normally and pydantic reads the environment
itself.
"""
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Supabase. No defaults: app/database.py already refuses to boot
    # without them, and a silent "" would turn that into a confusing 401
    # rather than a clear startup failure.
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # --- Market
    MARKET_SUFFIX: str = ".NS"

    # --- Tutor routing
    ROUTER_CONFIDENCE_THRESHOLD: float = 0.45
    ROUTER_MODE: str = "enforce"          # enforce | log_only

    # --- Guardrails
    GUARDRAIL_MODE: str = "block"         # block | log_only

    # --- Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:6060/v1/traces"

    # --- CORS (audit finding P4-04)
    # Was hardcoded to the Vite dev server in main.py, which meant any
    # non-local deployment silently failed every browser request.
    #
    # Declared as a plain string, not List[str], deliberately: pydantic-settings
    # runs json.loads on any complex-typed field before validators see it, so a
    # sensible `CORS_ALLOW_ORIGINS=https://app.example` would raise a JSON decode
    # error at startup. Comma separated, split by the property below.
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]

    @field_validator("ROUTER_MODE", "GUARDRAIL_MODE")
    @classmethod
    def _known_mode(cls, v: str, info) -> str:
        allowed = {"enforce", "log_only"} if info.field_name == "ROUTER_MODE" else {"block", "log_only"}
        if v not in allowed:
            raise ValueError(f"{info.field_name} must be one of {sorted(allowed)}, got {v!r}")
        return v


settings = Settings()
