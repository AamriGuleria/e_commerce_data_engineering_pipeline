from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return self.async_database_url

    database_url: str = "postgresql://admin:admin123@localhost:5435/ecommerce_db"
    async_database_url: str = "postgresql+asyncpg://admin:admin123@localhost:5435/ecommerce_db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    

config = Config()