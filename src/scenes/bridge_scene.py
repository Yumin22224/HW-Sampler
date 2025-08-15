# ============================================
# scenes/bridge_scene.py - Bridge 씬 구현
# ============================================

from scenes.base_scene import BaseScene
import pygame

class BridgeScene(BaseScene):
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.options = ["Start Work Lane", "Go to Library"]
        self.selected = 0
    
    def enter(self, **kwargs):
        # Bridge 진입 시 처리
        if kwargs.get("from_scene") == "loop_composition":
            # 루프 완성 후 진입한 경우
            self.show_tail_given_animation()
    
    def update(self, dt, hw_state):
        # Push Button으로 선택
        if hw_state.get("PUSH_CLICK"):
            if self.selected == 0:
                self.scene_manager.change_scene("recording")
            else:
                self.scene_manager.change_scene("library")
        
        # Rotary로 선택 변경
        if hw_state.get("ROTARY_CW"):
            self.selected = (self.selected + 1) % len(self.options)
        elif hw_state.get("ROTARY_CCW"):
            self.selected = (self.selected - 1) % len(self.options)
    
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
        
        # 안내 텍스트
        self.draw_text("P-C: Select | R-R: Navigate", 250, 400, (100, 100, 100))
    
    def show_tail_given_animation(self):
        # 고양이에게 꼬리를 달아주는 애니메이션
        # TODO: 구현
        pass