from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://pelotao:pelotao@localhost:5432/pelotao"
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173,http://localhost:80,https://1pelft.camppoia.com.br"
    admin_email: str | None = None
    admin_password: str | None = None
    admin_patente: str = "CEL"
    admin_nome_guerra: str = "Admin"


settings = Settings()
