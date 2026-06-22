from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    #JWT
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    #DB
    DATABASE_URL: str
    
    #Gemini
    GEMINI_API_KEY: str
    EMBEDDING_MODEL_NAME: str = "models/gemini-embedding-001"
    CHAT_MODEL_NAME: str = "gemini-3.1-flash-lite"
    OUTPUT_DEMENSIONALITY: int = 768
    ENABLE_MOCK_AI: bool = False
    
    #others
    UPLOAD_DIR: str = "upload"

    #run on local or GCP
    ENVIRONMENT: str= "local"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")



settings = Settings()