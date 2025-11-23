from fastapi import APIRouter
from src.services.hello_service import HelloService

router = APIRouter(tags=["hello"])

@router.get("/hello")
def hello(name: str = "World"):
    return HelloService.get_greeting(name)

