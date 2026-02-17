from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import Config

class ModelFactory:
    @staticmethod
    def get_embedding_model():
        print(f"📥 로컬 임베딩 모델({Config.EMBEDDING_MODEL_NAME}) 로딩 중...")
        return HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'}, # GPU 있으면 'cuda'
            encode_kwargs={'normalize_embeddings': True}
        )

    @staticmethod
    def get_llm():
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            google_api_key=Config.GOOGLE_API_KEY
        )