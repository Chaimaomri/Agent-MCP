from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    
    INFOBIP_API_KEY: str = ""
    INFOBIP_BASE_URL: str = "https://y4p6pg.api.infobip.com"
    INFOBIP_FROM_NAME: str = "NextGen Technologies"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" 
settings = Settings()