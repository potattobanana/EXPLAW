"""
Central place to load environment variables (.env). Import `settings`
from here rather than reading os.environ directly elsewhere.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    sso_base_url: str = "https://sso.agc.gov.sg"
    tracked_act_codes: str = "CoA1967,PDPA2012"  # comma-separated SSO short act codes to watch
    ai_provider: str = "anthropic"  # "anthropic" or "openai" (OpenAI-compatible, e.g. OpenRouter)
    ai_api_key: str = ""
    ai_base_url: str = ""  # empty -> provider default SDK endpoint; set for OpenAI-compatible gateways (OpenRouter, etc.)
    ai_model: str = ""  # empty -> provider-specific default (anthropic only)
    chroma_persist_dir: str = "./data/chroma"
    sg_statutes_mcp_command: str = "sg-eli-mcp"  # Singapore Statutes Online MCP connector executable
    sg_statutes_mcp_args: str = ""  # space-separated extra args, if any
    scrape_cron_hour: int = 0
    scrape_cron_minute: int = 0

    class Config:
        env_file = ".env"

    @property
    def tracked_act_codes_list(self) -> list[str]:
        return [code.strip() for code in self.tracked_act_codes.split(",") if code.strip()]


settings = Settings()
