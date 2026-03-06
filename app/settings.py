from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "controlled-tool-orchestrator"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./cto.sqlite3"


settings = Settings()
