from fastapi import APIRouter, Depends
from src.services.chatbot.services import ChatbotService

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# chatbot에게 질문
# 예시 : {"member_id": 1, "message": "불나면 보상 돼?"}
@router.post("/ask")
async def ask_insurance(request: dict, service: ChatbotService = Depends()):
    answer = await service.get_insurance_answer(
        member_id=request.get("member_id"),
        user_message=request.get("message")
    )
    return {"answer": answer}