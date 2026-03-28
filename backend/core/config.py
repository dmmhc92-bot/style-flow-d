import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    # MongoDB
    MONGO_URL: str = os.environ['MONGO_URL']
    DB_NAME: str = os.environ['DB_NAME']
    
    # JWT
    JWT_SECRET: str = os.environ['JWT_SECRET_KEY']
    JWT_ALGORITHM: str = os.environ['JWT_ALGORITHM']
    JWT_EXPIRATION_MINUTES: int = int(os.environ['JWT_EXPIRATION_MINUTES'])
    
    # External Services
    EMERGENT_LLM_KEY: str = os.environ.get('EMERGENT_LLM_KEY', '')
    RESEND_API_KEY: str = os.environ.get('RESEND_API_KEY', '')
    
    # Cloudinary CDN
    CLOUDINARY_CLOUD_NAME: str = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY: str = os.environ.get('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET: str = os.environ.get('CLOUDINARY_API_SECRET', '')
    
    # App Config
    APP_SCHEME: str = "styleflow"
    APP_DOMAIN: str = os.environ.get('APP_DOMAIN', 'homestyleflowapp.com')
    APP_BUNDLE_ID: str = "com.styleflow.app"
    APP_TEAM_ID: str = os.environ.get('APPLE_TEAM_ID', 'NTZB3ZFKXK')

settings = Settings()
