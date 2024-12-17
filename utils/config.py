from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DISCORD_BOT_TOKEN: str
    LOSTARK_API_KEY: str
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
