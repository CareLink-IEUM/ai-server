import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    EMBEDDING_MODEL_NAME = "jhgan/ko-sroberta-multitask"
    VECTOR_DB_PATH = "./chroma_db"