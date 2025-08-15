# ============================================
# game.py - 게임 메인 클래스
# ============================================

import pygame
from core.scene_manager import SceneManager
from core.state_manager import StateManager
from inputs.hardware_input import HardwareInput
from config import *

class Game:
    def __init__(self):
        # 디스플레이 초기화
        flags = pygame.FULLSCREEN if FULLSCREEN else 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption("Deadcat Recorder")
        pygame.mouse.set_visible(False)
        
        # 시스템 초기화
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 매니저 초기화
        self.state_manager = StateManager()
        self.scene_manager = SceneManager(self.screen, self.state_manager)
        self.hardware_input = HardwareInput()
        
        # 초기 씬 설정 (Bridge에서 시작)
        self.scene_manager.change_scene("bridge")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # 개발용 키보드 매핑
                self.hardware_input.handle_keyboard(event)
            
            # 현재 씬에 이벤트 전달
            self.scene_manager.handle_event(event)
    
    def update(self, dt):
        # 하드웨어 입력 읽기
        hw_state = self.hardware_input.read()
        
        # 씬 업데이트
        self.scene_manager.update(dt, hw_state)
    
    def draw(self):
        self.screen.fill(BLACK)
        self.scene_manager.draw()
        pygame.display.flip()
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        self.hardware_input.cleanup()
