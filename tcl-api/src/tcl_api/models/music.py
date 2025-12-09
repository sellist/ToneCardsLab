from pydantic import BaseModel

class Note(BaseModel):
    content: str = "This is a sample note."
