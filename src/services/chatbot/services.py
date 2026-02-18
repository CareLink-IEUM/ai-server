import httpx
from typing import List
from src.services.chatbot.rag_engine import RAGEngine
from langchain_core.prompts import ChatPromptTemplate
from src.core.factories import Factories

class ChatbotService:
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.llm = Factories.get_llm()
        self.backend_url = "http://localhost:8080/api"

    async def _fetch_user_coverage_ids(self, member_id: int) -> List[int]:
        """백엔드에서 유저의 활성화된 가입 담보 ID 리스트만 추출합니다."""
        url = f"{self.backend_url}/members/{member_id}/personal-insurances?status=ACTIVE"
        
        # TODO: 따로 빼
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                res_data = response.json()
                
                coverage_ids = []
                if res_data.get("success") and res_data.get("data"):
                    for contract in res_data["data"]:
                        for cov in contract.get("coverages", []):
                            coverage_ids.append(cov["coverageId"])
                
                return list(set(coverage_ids))
            except Exception as e:
                print(f"❌ 백엔드 연동 실패 (member_id: {member_id}): {e}")
                return []
            
    async def get_insurance_answer(self, member_id: int, user_message: str):
        user_coverages = await self._fetch_user_coverage_ids(member_id)
        
        docs = self.rag_engine.search_relevant_documents(user_message, user_coverages)
        
        if not docs:
            return "죄송합니다. 현재 가입하신 보험 정보 내에서는 해당 질문에 대한 답변을 찾을 수 없습니다."

        context = "\n".join([doc.page_content for doc in docs])

        # 3. 프롬프트 (TODO: 컴플라이언스!!!!!!)
        prompt = ChatPromptTemplate.from_template("""
        당신은 한화 손해보험의 스마트 금융 비서 'Bridge AI'입니다. 
        제공된 [약관 내용]을 바탕으로 고객님의 질문에 신뢰감 있고 친절하게 답변해 주세요.

        [답변 규칙]
        1. 반드시 제공된 [약관 내용]에 근거하여 답변하세요.
        2. 고객님이 가입하지 않은 담보(coverage_id 필터 밖의 내용)에 대해서는 "가입 정보가 확인되지 않아 안내가 어렵습니다"라고 정중히 답하세요.
        3. 보장 금액이나 지급 조건은 약관에 명시된 대로 정확하게 설명하세요.
        
        [약관 내용]
        {context}
        
        질문: {question}
        """)
        
        chain = prompt | self.llm
        response = chain.invoke({"context": context, "question": user_message})
        
        return response.content