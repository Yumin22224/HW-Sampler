
# ============================================
# scenes/base_scene.py - 씬 베이스 클래스
# ============================================

import pygame

class BaseScene:
    def __init__(self, screen, scene_manager):
        self.screen = screen
        self.scene_manager = scene_manager
        self.font = pygame.font.SysFont(None, 32)
    
    def enter(self, **kwargs):
        \"\"\"씬 진입 시 호출\"\"\"
        pass
    
    def exit(self):
        \"\"\"씬 종료 시 호출\"\"\"
        pass
    
    def handle_event(self, event):
        \"\"\"이벤트 처리\"\"\"
        pass
    
    def update(self, dt, hw_state):
        \"\"\"로직 업데이트\"\"\"
        pass
    
    def draw(self):
        \"\"\"화면 그리기\"\"\"
        pass
    
    def draw_text(self, text, x, y, color=(255, 255, 255)):
        \"\"\"텍스트 그리기 헬퍼\"\"\"
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, (x, y))
