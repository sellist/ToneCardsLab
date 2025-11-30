from typing import Optional
from pydantic import BaseModel, model_validator


class CardSide(BaseModel):
    abc_js_content: Optional[str] = None
    text: Optional[str] = None

    @model_validator(mode="before")
    def require_one_field(self, values):
        if not (values.get("text") or values.get("abc_js_content")):
            raise ValueError("Either 'text' or 'abc_js_content' must be provided")
        return values

    def get_render_content(self) -> str:
        return self.abc_js_content or self.text or ""

class Card(BaseModel):
    id: int
    front: CardSide
    back: CardSide

    def get_render_pair(self) -> tuple[str, str]:
        return self.front.get_render_content(), self.back.get_render_content()