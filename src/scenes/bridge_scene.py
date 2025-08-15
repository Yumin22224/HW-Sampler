# scenes/bridge_scene.py (핵심 부분만)
from scenes.base_scene import BaseScene
from utils.constants import PC, RC, RR_CW, RR_CCW
import pygame

class BridgeScene(BaseScene):
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.options = ["Repeat [Work Lane]", "Give Cat a Tail [Library]"]
        self.selected = 0

    def enter(self, **kwargs):
        if kwargs.get("from_scene") == "loop_composition":
            # 꼬리 달아주기 애니메이션 (placeholder)
            pass

    def update(self, dt, hw_state):
        if hw_state.get(RR_CW):  self.selected = (self.selected + 1) % len(self.options)
        if hw_state.get(RR_CCW): self.selected = (self.selected - 1) % len(self.options)
        if hw_state.get(RC):
            if self.selected == 0:
                self.scene_manager.change_scene("recording")   # Pre-record로
            else:
                self.scene_manager.change_scene("library")
        # PC는 메타(팁 표시 등)로 사용하거나 무시

    def draw(self):
        self.screen.fill((30, 30, 40))
        self.draw_text("[Bridge]", 340, 50, (100, 150, 200))
        for i, option in enumerate(self.options):
            color = (255, 200, 100) if i == self.selected else (150, 150, 150)
            self.draw_text(option, 280, 200 + i*80, color)
        self.draw_text("R-R: Navigate  |  R-C: Select", 250, 420, (110, 110, 110))
