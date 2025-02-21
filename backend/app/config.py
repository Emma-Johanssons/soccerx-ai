from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_BASE_URL: str = "https://v3.football.api-sports.io"

    # Database Settings
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    
    # API Settings
    FOOTBALL_API_KEY: str
    RAPIDAPI_HOST: str = "api-football-v1.p.rapidapi.com"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 