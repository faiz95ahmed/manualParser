from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bridge Tech Test"
    openai_api_key: str
    mongo_uri: str
    model_config = SettingsConfigDict(env_file=".env")