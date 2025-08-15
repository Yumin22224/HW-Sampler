#!/usr/bin/env python3
"""
Deadcat Recorder - Main Starter
유령 고양이의 꼬리 하드웨어 샘플팩 메이커

이 파일을 src/main_starter.py로 저장하고 실행하세요.
필요한 모든 모듈이 없어도 기본 구조를 테스트할 수 있습니다.
"""

import pygame
import sys
import os
import math
import random

# 설정
WIDTH = 800
HEIGHT = 480
FPS = 60
FULLSCREEN = False  # 개발 중에는 False

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GHOST_BLUE = (100, 150, 200)
TAIL_ORANGE = (255, 150, 50)
DARK_BG = (20, 25, 30)
BUTTON_RED = (200, 50, 50)

class MockHardwareInput:
    """개발용 키보드 입력 매핑"""
    def __init__(self):
        self.states = {}
        self.prev_keys = {}
    
    def update(self, keys):
        self.states = {
            "PUSH_CLICK": keys[pygame.K_SPACE] and not self.prev_keys.get(pygame.K_SPACE, False),
            "PUSH_DOUBLE_CLICK": keys[pygame.K_d] and not self.prev_keys.get(pygame.K_d, False),
            "PUSH_LONG_CLICK": keys[pygame.K_l] and not self.prev_keys.get(pygame.K_l, False),
            "ROTARY_CLICK": keys[pygame.K_RETURN] and not self.prev_keys.get(pygame.K_RETURN, False),
            "ROTARY_CW": keys[pygame.K_RIGHT] and not self.prev_keys.get(pygame.K_RIGHT, False),
            "ROTARY_CCW": keys[pygame.K_LEFT] and not self.prev_keys.get(pygame.K_LEFT, False),
            "RECORD_CLICK": keys[pygame.K_r] and not self.prev_keys.get(pygame.K_r, False),
            "TOGGLE_SHORT": keys[pygame.K_t] and not self.prev_keys.get(pygame.K_t, False),
            "TOGGLE_LONG": keys[pygame.K_y] and not self.prev_keys.get(pygame.K_y, False),
        }
        self.prev_keys = {k: keys[k] for k in [
            pygame.K_SPACE, pygame.K_d, pygame.K_l, pygame.K_RETURN,
            pygame.K_RIGHT, pygame.K_LEFT, pygame.K_r, pygame.K_t, pygame.K_y
        ]}
    
    def get_states(self):
        return self.states

class BaseScene:
    """씬 베이스 클래스"""
    def __init__(self, screen, scene_manager):
        self.screen = screen
        self.scene_manager = scene_manager
        self.font = pygame.font.SysFont("monospace", 20)
        self.title_font = pygame.font.SysFont("monospace", 32, bold=True)
    
    def enter(self, **kwargs):
        pass
    
    def exit(self):
        pass
    
    def update(self, dt, hw_state):
        pass
    
    def draw(self):
        pass
    
    def draw_text(self, text, x, y, color=WHITE, font=None):
        if font is None:
            font = self.font
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(x, y))
        self.screen.blit(surface, rect)

class BridgeScene(BaseScene):
    """Bridge 씬 - 진입점"""
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.options = ["Start Work Lane", "Go to Library"]
        self.selected = 0
        self.animation_time = 0
        self.tail_given = False
    
    def enter(self, **kwargs):
        if kwargs.get("from_scene") == "loop_composition":
            self.tail_given = True
            self.animation_time = 0
    
    def update(self, dt, hw_state):
        self.animation_time += dt
        
        if hw_state.get("PUSH_CLICK"):
            if self.selected == 0:
                self.scene_manager.change_scene("recording")
            else:
                self.scene_manager.change_scene("library")
        
        if hw_state.get("ROTARY_CW"):
            self.selected = (self.selected + 1) % len(self.options)
        elif hw_state.get("ROTARY_CCW"):
            self.selected = (self.selected - 1) % len(self.options)
    
    def draw(self):
        self.screen.fill(DARK_BG)
        
        # 타이틀
        self.draw_text("[Bridge]", WIDTH//2, 80, GHOST_BLUE, self.title_font)
        
        # 고양이 애니메이션
        self.draw_ghost_cat()
        
        # 옵션
        for i, option in enumerate(self.options):
            color = TAIL_ORANGE if i == self.selected else (100, 100, 100)
            y = 300 + i * 60
            self.draw_text(option, WIDTH//2, y, color)
        
        # 컨트롤 안내
        self.draw_text("SPACE: Select | ←→: Navigate | ESC: Exit", WIDTH//2, 440, (80, 80, 80))
        
        # 꼬리 애니메이션
        if self.tail_given:
            self.draw_tail_animation()
    
    def draw_ghost_cat(self):
        """유령 고양이 그리기"""
        x = WIDTH // 2
        y = 180
        
        # 몸통 (투명한 느낌)
        body_alpha = 100 + int(30 * math.sin(self.animation_time * 2))
        pygame.draw.ellipse(self.screen, (*GHOST_BLUE, body_alpha), 
                           (x - 60, y - 30, 120, 60))
        
        # 머리
        pygame.draw.circle(self.screen, GHOST_BLUE, (x - 40, y), 25)
        
        # 눈
        eye_glow = 150 + int(50 * math.sin(self.animation_time * 3))
        pygame.draw.circle(self.screen, (eye_glow, eye_glow, 255), (x - 45, y - 5), 4)
        pygame.draw.circle(self.screen, (eye_glow, eye_glow, 255), (x - 35, y - 5), 4)
    
    def draw_tail_animation(self):
        """꼬리 달아주기 애니메이션"""
        if self.animation_time < 2:
            alpha = int(255 * (self.animation_time / 2))
            x = WIDTH // 2 + 60
            y = 180
            
            # 꼬리 그리기
            for i in range(5):
                segment_x = x + i * 15 + int(10 * math.sin(self.animation_time * 5 + i))
                segment_y = y + int(5 * math.sin(self.animation_time * 3 + i * 0.5))
                pygame.draw.circle(self.screen, (*TAIL_ORANGE, alpha), 
                                 (segment_x, segment_y), 8 - i)

class RecordingScene(BaseScene):
    """녹음 씬"""
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.state = "PRE_RECORD"
        self.animation_time = 0
        self.waveform_data = []
    
    def update(self, dt, hw_state):
        self.animation_time += dt
        
        if self.state == "PRE_RECORD":
            if hw_state.get("PUSH_CLICK"):
                self.scene_manager.change_scene("library")
            if hw_state.get("RECORD_CLICK"):
                self.state = "RECORDING"
                self.animation_time = 0
        
        elif self.state == "RECORDING":
            # 가짜 웨이브폼 데이터 생성
            self.waveform_data.append(random.uniform(-1, 1))
            if len(self.waveform_data) > 100:
                self.waveform_data.pop(0)
            
            if hw_state.get("RECORD_CLICK"):
                self.state = "POST_RECORD"
        
        elif self.state == "POST_RECORD":
            if hw_state.get("ROTARY_CLICK"):
                self.scene_manager.change_scene("sound_crafting")
            if hw_state.get("PUSH_LONG_CLICK"):
                self.state = "PRE_RECORD"
                self.waveform_data = []
    
    def draw(self):
        self.screen.fill(DARK_BG)
        
        self.draw_text("Recording Scene", WIDTH//2, 50, GHOST_BLUE, self.title_font)
        
        if self.state == "PRE_RECORD":
            # REC 버튼
            color = (200 + int(50 * math.sin(self.animation_time * 3)), 50, 50)
            pygame.draw.circle(self.screen, color, (WIDTH//2, HEIGHT//2), 60)
            self.draw_text("REC", WIDTH//2, HEIGHT//2, WHITE, self.title_font)
            self.draw_text("Press R to start recording", WIDTH//2, 350, (150, 150, 150))
        
        elif self.state == "RECORDING":
            # 녹음 중 애니메이션
            radius = 40 + int(20 * math.sin(self.animation_time * 5))
            pygame.draw.circle(self.screen, BUTTON_RED, (WIDTH//2, HEIGHT//2), radius)
            self.draw_text("RECORDING", WIDTH//2, HEIGHT//2 + 100, BUTTON_RED)
            
            # 웨이브폼 표시
            if len(self.waveform_data) > 1:
                points = []
                for i, val in enumerate(self.waveform_data):
                    x = 100 + i * 6
                    y = HEIGHT//2 + int(val * 50)
                    points.append((x, y))
                pygame.draw.lines(self.screen, TAIL_ORANGE, False, points, 2)
        
        elif self.state == "POST_RECORD":
            # 녹음 완료
            pygame.draw.rect(self.screen, (50, 100, 150), (WIDTH//2 - 150, HEIGHT//2 - 50, 300, 100))
            self.draw_text("Sample Recorded!", WIDTH//2, HEIGHT//2, WHITE)
            self.draw_text("Enter: Next | L: Re-record", WIDTH//2, 350, (150, 150, 150))

class SoundCraftingScene(BaseScene):
    """소리 세공 씬"""
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.tools = ["Trim", "Reverse", "Speed", "EQ"]
        self.current_tool = 0
        self.stone_rotation = 0
        self.tool_value = 50
    
    def update(self, dt, hw_state):
        self.stone_rotation += dt * 30  # 회전 애니메이션
        
        if hw_state.get("ROTARY_CW"):
            self.current_tool = (self.current_tool + 1) % len(self.tools)
        elif hw_state.get("ROTARY_CCW"):
            self.current_tool = (self.current_tool - 1) % len(self.tools)
        
        if hw_state.get("ROTARY_CLICK"):
            self.scene_manager.change_scene("loop_composition")
        
        # 툴 값 조정 (상/하 키)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.tool_value = min(100, self.tool_value + 1)
        elif keys[pygame.K_DOWN]:
            self.tool_value = max(0, self.tool_value - 1)
    
    def draw(self):
        self.screen.fill(DARK_BG)
        
        self.draw_text("Sound Crafting", WIDTH//2, 50, GHOST_BLUE, self.title_font)
        
        # Sound Stone 시각화
        self.draw_sound_stone()
        
        # 툴 선택
        for i, tool in enumerate(self.tools):
            y = 150 + i * 50
            color = TAIL_ORANGE if i == self.current_tool else (100, 100, 100)
            
            if i == self.current_tool:
                pygame.draw.rect(self.screen, (40, 40, 50), (500, y - 15, 250, 40))
            
            self.draw_text(tool, 550, y, color)
            
            # 현재 툴의 값 표시
            if i == self.current_tool:
                # 프로그레스 바
                pygame.draw.rect(self.screen, (60, 60, 70), (580, y + 10, 150, 8))
                pygame.draw.rect(self.screen, TAIL_ORANGE, 
                               (580, y + 10, int(150 * self.tool_value / 100), 8))
        
        self.draw_text("←→: Select Tool | ↑↓: Adjust | Enter: Next", WIDTH//2, 440, (80, 80, 80))
    
    def draw_sound_stone(self):
        """소리 원석 그리기"""
        cx, cy = 250, HEIGHT//2
        
        # 회전하는 다각형 원석
        angles = []
        for i in range(6):
            angle = self.stone_rotation + i * 60
            angles.append(angle * math.pi / 180)
        
        points = []
        for i, angle in enumerate(angles):
            # 불규칙한 반지름
            radius = 80 + 20 * math.sin(i * 1.5)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))
        
        # 원석 그리기
        pygame.draw.polygon(self.screen, (100, 120, 180), points)
        pygame.draw.polygon(self.screen, GHOST_BLUE, points, 3)
        
        # 중심에 빛나는 효과
        glow = 100 + int(50 * math.sin(self.stone_rotation * 0.05))
        pygame.draw.circle(self.screen, (glow, glow, 255), (int(cx), int(cy)), 15)

class LoopCompositionScene(BaseScene):
    """루프 제작 씬"""
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.layers = [[] for _ in range(4)]
        self.current_layer = 0
        self.current_bar = 0
        self.bars = 4
        self.bpm = 120
        self.animation_time = 0
    
    def update(self, dt, hw_state):
        self.animation_time += dt
        
        if hw_state.get("ROTARY_CW"):
            self.current_bar = (self.current_bar + 1) % self.bars
        elif hw_state.get("ROTARY_CCW"):
            self.current_bar = (self.current_bar - 1) % self.bars
        
        if hw_state.get("ROTARY_CLICK"):
            # 현재 위치에 샘플 배치 (토글)
            pos = (self.current_layer, self.current_bar)
            if pos not in self.layers[self.current_layer]:
                self.layers[self.current_layer].append(self.current_bar)
            else:
                self.layers[self.current_layer].remove(self.current_bar)
        
        if hw_state.get("PUSH_CLICK"):
            # 완성 체크
            has_content = any(layer for layer in self.layers)
            if has_content:
                self.scene_manager.change_scene("bridge", from_scene="loop_composition")
            else:
                self.scene_manager.change_scene("recording")
        
        # 레이어 변경 (위/아래 키)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.current_layer = max(0, self.current_layer - 1)
        elif keys[pygame.K_DOWN]:
            self.current_layer = min(3, self.current_layer + 1)
    
    def draw(self):
        self.screen.fill(DARK_BG)
        
        self.draw_text("Loop Composition", WIDTH//2, 50, GHOST_BLUE, self.title_font)
        self.draw_text(f"BPM: {self.bpm} | Bars: {self.bars}", WIDTH//2, 90, (150, 150, 150))
        
        # 레이어 (비즈공예 스타일)
        self.draw_bead_layers()
        
        # 컨트롤
        self.draw_text("←→: Move | Enter: Place | Space: Complete/Next", WIDTH//2, 440, (80, 80, 80))
        self.draw_text("↑↓: Change Layer", WIDTH//2, 460, (80, 80, 80))
    
    def draw_bead_layers(self):
        """비즈공예 스타일 레이어"""
        start_y = 150
        layer_height = 60
        
        for layer_idx in range(4):
            y = start_y + layer_idx * layer_height
            
            # 레이어 줄
            color = GHOST_BLUE if layer_idx == self.current_layer else (50, 50, 60)
            pygame.draw.line(self.screen, color, (100, y), (700, y), 2)
            
            # 레이어 번호
            self.draw_text(f"L{layer_idx + 1}", 70, y, color)
            
            # 바 매듭
            for bar in range(self.bars):
                x = 150 + (500 / self.bars) * bar
                
                # 매듭 (빈 위치)
                is_current = (layer_idx == self.current_layer and bar == self.current_bar)
                knot_color = TAIL_ORANGE if is_current else (60, 60, 60)
                pygame.draw.circle(self.screen, knot_color, (int(x), y), 10, 2)
                
                # 배치된 샘플 (비즈)
                if bar in self.layers[layer_idx]:
                    # 빛나는 비즈
                    glow = 150 + int(50 * math.sin(self.animation_time * 2 + bar))
                    bead_color = (glow, 100, 200)
                    pygame.draw.circle(self.screen, bead_color, (int(x), y), 8)
                    
                    # 연결선 (다음 비즈까지)
                    next_bar = (bar + 1) % self.bars
                    if next_bar in self.layers[layer_idx]:
                        next_x = 150 + (500 / self.bars) * next_bar
                        pygame.draw.line(self.screen, bead_color, (int(x), y), (int(next_x), y), 1)

class LibraryScene(BaseScene):
    """라이브러리 씬"""
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.focus_distance = 50
        self.tail_packs = [
            {"name": "Mystic Tail #1", "age": 10},
            {"name": "Shadow Tail #2", "age": 30},
            {"name": "Crystal Tail #3", "age": 50},
            {"name": "Ancient Tail #4", "age": 80},
        ]
        self.selected = 0
        self.telescope_wobble = 0
    
    def update(self, dt, hw_state):
        self.telescope_wobble += dt * 2
        
        if hw_state.get("PUSH_CLICK"):
            self.scene_manager.change_scene("bridge")
        
        if hw_state.get("ROTARY_CW"):
            self.focus_distance = min(100, self.focus_distance + 10)
        elif hw_state.get("ROTARY_CCW"):
            self.focus_distance = max(0, self.focus_distance - 10)
        
        # 위/아래로 선택
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.selected = max(0, self.selected - 1)
        elif keys[pygame.K_DOWN]:
            self.selected = min(len(self.get_visible_packs()) - 1, self.selected + 1)
        
        if hw_state.get("ROTARY_CLICK"):
            # Export (훔치기) 애니메이션
            self.steal_animation()
    
    def get_visible_packs(self):
        """초점 거리에 따라 보이는 팩"""
        # 거리가 멀수록 오래된 것
        return [p for p in self.tail_packs if abs(p["age"] - self.focus_distance) < 30]
    
    def steal_animation(self):
        """훔치기 애니메이션 (간단한 표시)"""
        print(f"Stealing {self.tail_packs[self.selected]['name']}...")
    
    def draw(self):
        self.screen.fill((10, 10, 15))
        
        self.draw_text("Hunter's Warehouse", WIDTH//2, 50, (150, 100, 200), self.title_font)
        
        # 망원경 프레임
        self.draw_telescope_view()
        
        # 꼬리 목록
        visible = self.get_visible_packs()
        list_y = 200
        for i, pack in enumerate(visible):
            color = TAIL_ORANGE if i == self.selected else (100, 100, 100)
            self.draw_text(pack["name"], WIDTH//2, list_y + i * 40, color)
        
        # 초점 표시
        self.draw_text(f"Focus: {self.focus_distance}m", WIDTH//2, 380, (100, 100, 100))
        self.draw_text("←→: Focus | Enter: Steal | Space: Back", WIDTH//2, 440, (80, 80, 80))
    
    def draw_telescope_view(self):
        """망원경 뷰"""
        cx, cy = WIDTH//2, HEIGHT//2 - 50
        
        # 망원경 렌즈 (흔들림 효과)
        wobble_x = int(3 * math.sin(self.telescope_wobble))
        wobble_y = int(2 * math.sin(self.telescope_wobble * 1.3))
        
        # 외부 원
        pygame.draw.circle(self.screen, (40, 40, 50), (cx + wobble_x, cy + wobble_y), 150, 3)
        
        # 십자선
        pygame.draw.line(self.screen, (60, 60, 70), 
                        (cx - 150 + wobble_x, cy + wobble_y), 
                        (cx + 150 + wobble_x, cy + wobble_y), 1)
        pygame.draw.line(self.screen, (60, 60, 70), 
                        (cx + wobble_x, cy - 150 + wobble_y), 
                        (cx + wobble_x, cy + 150 + wobble_y), 1)
        
        # 초점 링
        focus_radius = int(30 + self.focus_distance * 0.5)
        pygame.draw.circle(self.screen, (80, 80, 100), (cx, cy), focus_radius, 1)

class SceneManager:
    """씬 매니저"""
    def __init__(self, screen):
        self.screen = screen
        self.scenes = {}
        self.current_scene = None
        
        # 씬 등록
        self.register_scenes()
    
    def register_scenes(self):
        self.scenes["bridge"] = BridgeScene(self.screen, self)
        self.scenes["recording"] = RecordingScene(self.screen, self)
        self.scenes["sound_crafting"] = SoundCraftingScene(self.screen, self)
        self.scenes["loop_composition"] = LoopCompositionScene(self.screen, self)
        self.scenes["library"] = LibraryScene(self.screen, self)
    
    def change_scene(self, scene_name, **kwargs):
        if scene_name in self.scenes:
            if self.current_scene:
                self.current_scene.exit()
            
            self.current_scene = self.scenes[scene_name]
            self.current_scene.enter(**kwargs)
    
    def update(self, dt, hw_state):
        if self.current_scene:
            self.current_scene.update(dt, hw_state)
    
    def draw(self):
        if self.current_scene:
            self.current_scene.draw()

class DeadcatRecorder:
    """메인 게임 클래스"""
    def __init__(self):
        pygame.init()
        
        # 디스플레이
        flags = pygame.FULLSCREEN if FULLSCREEN else 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption("Deadcat Recorder - 유령 고양이의 꼬리")
        
        # 시스템
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.SysFont("monospace", 14)
        
        # 매니저
        self.scene_manager = SceneManager(self.screen)
        self.hardware_input = MockHardwareInput()
        
        # 초기 씬
        self.scene_manager.change_scene("bridge")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.hardware_input.update(keys)
        hw_state = self.hardware_input.get_states()
        
        self.scene_manager.update(dt, hw_state)
    
    def draw(self):
        self.scene_manager.draw()
        
        # FPS 표시
        fps_text = f"FPS: {self.clock.get_fps():.0f}"
        fps_surface = self.font.render(fps_text, True, (80, 80, 80))
        self.screen.blit(fps_surface, (10, 10))
        
        # 컨트롤 가이드 (개발용)
        controls = [
            "R: Record | Space: Push | Enter: Rotary Click",
            "←→: Rotary | D: Double Click | L: Long Click",
            "↑↓: Navigate | ESC: Exit"
        ]
        y = HEIGHT - 60
        for line in controls:
            surface = self.font.render(line, True, (60, 60, 60))
            self.screen.blit(surface, (10, y))
            y += 15
        
        pygame.display.flip()
    
    def run(self):
        """메인 게임 루프"""
        print("=" * 50)
        print("DEADCAT RECORDER - 유령 고양이의 꼬리")
        print("=" * 50)
        print("하드웨어 샘플팩 메이커 프로토타입")
        print("음악가를 위한 게임적 도구")
        print("-" * 50)
        print("조작법:")
        print("  R: 녹음")
        print("  Space: Push Button")
        print("  Enter: Rotary Click")
        print("  ←→: Rotary 회전")
        print("  ↑↓: 네비게이션")
        print("  D: Double Click")
        print("  L: Long Click")
        print("  ESC: 종료")
        print("=" * 50)
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        print("\n프로그램을 종료합니다. 고양이가 당신을 기억할 것입니다...\n")

def main():
    """진입점"""
    game = DeadcatRecorder()
    game.run()

if __name__ == "__main__":
    main()