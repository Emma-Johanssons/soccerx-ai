from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    API_BASE_URL: str
    FOOTBALL_API_KEY: str
    RAPIDAPI_HOST: str

    # Database Settings
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    
    # Redis Settings
    REDIS_URL: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 