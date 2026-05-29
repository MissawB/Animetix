from typing import Any, Dict
from core.ports.game_state_port import GameStatePort

class DjangoSessionStateAdapter(GameStatePort):
    """
    Infrastructure adapter using Django's request.session for state storage.
    """
    def __init__(self, session):
        self.session = session

    def get(self, key: str, default: Any = None) -> Any:
        return self.session.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.session[key] = value
        self.session.modified = True

    def update(self, data: Dict[str, Any]) -> None:
        self.session.update(data)
        self.session.modified = True

    def delete(self, key: str) -> None:
        if key in self.session:
            del self.session[key]
            self.session.modified = True
