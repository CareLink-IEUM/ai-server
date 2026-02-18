from langchain_chroma import Chroma
from src.core.factories import Factories
from src.core.config import Config

class RAGEngine:
    def __init__(self):
        self.embeddings = Factories.get_embedding_model()
        self.llm = Factories.get_llm()
        
        self.vector_db = Chroma(
            persist_directory=Config.VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )

    def search_relevant_documents(self, query: str, coverage_ids: list = None):
        # Metadata filtering : 해당 coverage_id만 검색
        search_kwargs = {}
        if coverage_ids:
            search_kwargs["filter"] = {"coverage_id": {"$in": coverage_ids}}
            
        retriever = self.vector_db.as_retriever(search_kwargs=search_kwargs, search_type="similarity")
        return retriever.invoke(query)