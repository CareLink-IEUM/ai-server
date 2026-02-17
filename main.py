from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class QuestionRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "AI Server is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)