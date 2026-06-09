from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    #JWT
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    #DB
    DATABASE_URL: str
    
    #API
    GEMINI_API_KEY: str
    
    #others
    UPLOAD_DIR: str = "upload"

    #run on local or GCP
    ENVIRONMENT: str= "local"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")



settings = Settings()