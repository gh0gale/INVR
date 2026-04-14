from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Query(BaseModel):
    query: str

@router.post("/chat")
def chat(query: Query):
    return {"response": "This is a mocked response."}
