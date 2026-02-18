from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from src.routers.chatbot.router import router as chatbot_router

app = FastAPI()

app.include_router(chatbot_router)

class QuestionRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "AI Server is running"}

@app.get("/chatbot")
async def root():
    return {"message": "Welcome to Hanwha Bridge AI Server"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)