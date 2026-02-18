from pydantic import BaseModel, Field
from typing import List, Optional

class QuestionRequest(BaseModel):
    member_id: int  # 누구의 보험 정보를 조회할지 식별자 필요
    query: str      # "화재 사고 시 보상 범위 알려줘" 등

class SourceDocument(BaseModel):
    content: str
    metadata: dict

class ChatResponse(BaseModel):
    answer: str = Field(..., description="LLM이 생성한 답변")
    sources: List[SourceDocument] = Field([], description="답변의 근거가 된 약관 조각들")