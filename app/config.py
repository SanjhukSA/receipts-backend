from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    allowed_origins: str = "*"
    
    gemini_api_key: str
    
    
    gemini_model: str = "gemini-3.6-flash"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
