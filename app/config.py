from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://prefrio:prefrio@localhost:5432/prefrio"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
