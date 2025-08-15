# core/scene_manager.py
from typing import Dict, Type, Optional

class SceneManager:
    """
    씬 등록/전환/업데이트/그리기만 담당하는 순수 매니저.
    state_manager는 선택(없어도 동작).
    """
    def __init__(self, screen, state_manager: Optional[object] = None):
        self.screen = screen
        self.state_manager = state_manager
        self._registry: Dict[str, Type] = {}
        self.current = None
        self.current_name = None

    def register(self, name: str, scene_cls: Type):
        self._registry[name] = scene_cls

    def change_scene(self, name: str, **kwargs):
        if self.current and hasattr(self.current, "exit"):
            self.current.exit()

        cls = self._registry.get(name)
        if cls is None:
            raise ValueError(f"Scene '{name}' not registered")

        self.current = cls(self.screen, self)
        self.current_name = name
        if hasattr(self.current, "enter"):
            self.current.enter(**kwargs)

    def update(self, dt: float, hw_state: dict):
        if self.current is not None:
            # 씬이 개별 이벤트 루프를 쓰지 않는 설계이므로 hw_state만 전달
            if hasattr(self.current, "update"):
                self.current.update(dt, hw_state)

    def draw(self):
        if self.current is not None and hasattr(self.current, "draw"):
            self.current.draw()
