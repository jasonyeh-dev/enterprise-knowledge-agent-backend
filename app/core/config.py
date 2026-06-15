from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    #JWT
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    #AUTH
    API_V1_STR: str = "/api"
    AUTH_TOKEN_URL: str = f"{API_V1_STR}/user/auth"
    
    #DB
    DATABASE_URL: str
    
    #Gemini
    GEMINI_API_KEY: str
    EMBEDDING_MODEL_NAME: str = "models/gemini-embedding-001"
    CHAT_MODEL_NAME: str = "gemini-3.1-flash-lite"
    OUTPUT_DIMENSIONALITY: int = 768
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int =100

    RETRIEVAL_TOP_K: int =3
    RETRIEVAL_SCORE_THRESHOLD: float=0.4 

    #others
    UPLOAD_DIR: str = "upload"

    #run on local or GCP
    ENVIRONMENT: str= "local"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")



settings = Settings()