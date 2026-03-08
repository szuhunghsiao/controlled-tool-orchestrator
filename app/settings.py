from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "controlled-tool-orchestrator"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./cto.sqlite3"

    # Phase 3: platform hard limits
    max_input_bytes: int = 10_000  # 10 KB
    max_stdout_bytes: int = 100_000  # 100 KB
    max_stderr_bytes: int = 100_000  # 100 KB


settings = Settings()
