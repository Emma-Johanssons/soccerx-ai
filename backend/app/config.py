from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_BASE_URL: str = "https://v3.football.api-sports.io"

# Database Settings
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    DATABASE_URL: str
    FOOTBALL_API_KEY: str
    RAPIDAPI_HOST: str = "api-football-v1.p.rapidapi.com"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 