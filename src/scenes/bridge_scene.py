# ============================================
# scenes/bridge_scene.py - Bridge 씬 구현
# ============================================

from scenes.base_scene import BaseScene
from utils.constants import PC, RC, RR_CW, RR_CCW
import pygame

class BridgeScene(BaseScene):
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.options = ["Repeat [Work Lane]", "Give Cat a Tail [Library Lane]"]
        self.selected = 0
    
    def update(self, dt, hw_state):
        # R-R: 선택 변경
        if hw_state.get(RR_CW):   self.selected = (self.selected + 1) % len(self.options)
        if hw_state.get(RR_CCW):  self.selected = (self.selected - 1) % len(self.options)

        # R-C: 확정
        if hw_state.get(RC):
            if self.selected == 0:
                self.scene_manager.change_scene("recording")  # Pre-record로
            else:
                self.scene_manager.change_scene("library")
    
    def draw(self):
        # 배경
        self.screen.fill((30, 30, 40))
        
        # 타이틀
        self.draw_text("[Bridge]", 350, 50, (100, 150, 200))
        
        # 옵션 표시
        for i, option in enumerate(self.options):
            color = (255, 200, 100) if i == self.selected else (150, 150, 150)
            y = 200 + i * 80
            self.draw_text(option, 300, y, color)
        
    
    def show_tail_given_animation(self):
        # 고양이에게 꼬리를 달아주는 애니메이션
        # TODO: 구현
        pass