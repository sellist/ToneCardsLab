from typing import Dict, Any


class HelloService:
    @staticmethod
    def get_greeting(name: str = "World") -> Dict[str, Any]:
        return {
            "message": f"Hello, {name}!",
            "name": name,
        }

