# scenes/base_scene.py
import pygame

class BaseScene:
    def __init__(self, screen, scene_manager):
        self.screen = screen
        self.scene_manager = scene_manager

        # pygame.font이 아직 초기화 안 되어 있어도 안전하게
        if not pygame.font.get_init():
            pygame.font.init()
        self.font = pygame.font.SysFont(None, 28)

    def enter(self, **kwargs):
        """씬 진입 시 호출"""
        # 자식 클래스에서 필요하면 override
        return

    def exit(self):
        """씬 종료 시 호출"""
        return

    def handle_event(self, event):
        """이벤트 처리 (옵션: 키/마우스 등)"""
        return

    def update(self, dt, hw_state):
        """로직 업데이트"""
        return

    def draw(self):
        """화면 그리기"""
        # 자식 씬에서 구현
        return

    def draw_text(self, text, x, y, color=(255, 255, 255)):
        """텍스트 그리기 헬퍼"""
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, (x, y))
