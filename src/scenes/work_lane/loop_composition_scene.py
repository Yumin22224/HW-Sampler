# ============================================
# scenes/work_lane/loop_composition_scene.py
# ============================================
"""Loop Composition Scene - 루프 제작 (비즈공예 메타포)"""

import pygame
from scenes.base_scene import BaseScene

class LoopCompositionScene(BaseScene):
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.layers = []  # 최대 4개 레이어
        self.current_layer = 0
        self.current_bar = 0
        self.bpm = 120
        self.bars = 4  # 기본 4마디
        self.sound_stones = []  # 세공된 소리 원석들
        self.loop_state = "EDITING"  # EDITING, PLAYING
        self.focus_element = 0  # 0: Layer, 1: Bar position, 2: Sample select
    
    def enter(self, **kwargs):
        # 이전 씬에서 받은 sound_stone 추가
        if "sound_stone" in kwargs:
            self.sound_stones.append(kwargs["sound_stone"])
        
        # 레이어 초기화 (아직 없으면)
        if not self.layers:
            self.layers = [[] for _ in range(4)]
    
    def update(self, dt, hw_state):
        # P-C: 씬 이동 결정
        if hw_state.get("PUSH_CLICK"):
            if self.check_loop_complete():
                # 루프 완성 -> Bridge로
                self.complete_loop()
            else:
                # 추가 샘플 필요 -> 다시 Recording으로
                self.scene_manager.change_scene("recording")
        
        # R-C: 현재 위치에 샘플 배치/제거
        if hw_state.get("ROTARY_CLICK"):
            self.toggle_sample_at_position()
        
        # R-R: 네비게이션
        if hw_state.get("ROTARY_CW"):
            self.navigate_forward()
        elif hw_state.get("ROTARY_CCW"):
            self.navigate_backward()
        
        # P-DC: 재생/정지
        if hw_state.get("PUSH_DOUBLE_CLICK"):
            self.toggle_playback()
        
        # P-LC: BPM 조정 모드
        if hw_state.get("PUSH_LONG_CLICK"):
            self.enter_bpm_adjust_mode()
    
    def navigate_forward(self):
        if self.focus_element == 0:  # Layer navigation
            self.current_layer = (self.current_layer + 1) % 4
        elif self.focus_element == 1:  # Bar navigation
            self.current_bar = (self.current_bar + 1) % self.bars
        elif self.focus_element == 2:  # Sample selection
            # 다음 샘플 선택
            pass
    
    def navigate_backward(self):
        if self.focus_element == 0:
            self.current_layer = (self.current_layer - 1) % 4
        elif self.focus_element == 1:
            self.current_bar = (self.current_bar - 1) % self.bars
        elif self.focus_element == 2:
            # 이전 샘플 선택
            pass
    
    def toggle_sample_at_position(self):
        # 현재 레이어와 바 위치에 샘플 배치/제거
        if self.sound_stones:
            # 간단한 토글 로직
            position = (self.current_layer, self.current_bar)
            # TODO: 실제 샘플 배치 로직
    
    def check_loop_complete(self):
        # 최소 1개 레이어에 샘플이 있으면 완성 가능
        for layer in self.layers:
            if layer:
                return True
        return False
    
    def complete_loop(self):
        # 루프를 TailPack으로 변환하고 Bridge로
        tail_pack = {
            "layers": self.layers,
            "bpm": self.bpm,
            "bars": self.bars,
            "sound_stones": self.sound_stones
        }
        self.scene_manager.change_scene("bridge", 
                                       from_scene="loop_composition",
                                       tail_pack=tail_pack)
    
    def toggle_playback(self):
        self.loop_state = "PLAYING" if self.loop_state == "EDITING" else "EDITING"
        # TODO: 실제 루프 재생 로직
    
    def draw(self):
        self.screen.fill((20, 20, 25))
        
        # 타이틀
        self.draw_text("Loop Composition", 300, 20, (100, 150, 200))
        
        # BPM/Key/Bar 정보
        info_text = f"BPM: {self.bpm} | Bars: {self.bars}"
        self.draw_text(info_text, 280, 60, (150, 150, 150))
        
        # 레이어 시각화 (비즈공예 스타일)
        self.draw_loop_layers()
        
        # 샘플 팔레트
        self.draw_sample_palette()
        
        # 컨트롤 안내
        status = "PLAYING" if self.loop_state == "PLAYING" else "EDITING"
        self.draw_text(f"Status: {status}", 50, 420, (100, 200, 100))
        
        controls = "P-C: Next/Complete | R-R: Navigate | R-C: Place | P-DC: Play"
        self.draw_text(controls, 150, 450, (100, 100, 100))
    
    def draw_loop_layers(self):
        # 4개 레이어를 줄(string) 형태로 표현
        layer_y_start = 120
        layer_spacing = 60
        
        for i in range(4):
            y = layer_y_start + i * layer_spacing
            
            # 레이어 배경 (줄)
            color = (100, 150, 200) if i == self.current_layer else (50, 50, 60)
            pygame.draw.line(self.screen, color, (100, y), (700, y), 2)
            
            # 바 구분 (매듭)
            for bar in range(self.bars):
                x = 100 + (600 / self.bars) * bar
                
                # 매듭 그리기
                knot_color = (255, 200, 100) if (i == self.current_layer and bar == self.current_bar) else (80, 80, 80)
                pygame.draw.circle(self.screen, knot_color, (int(x), y), 8)
                
                # 샘플이 배치된 경우 시각화
                # TODO: 실제 샘플 표시
    
    def draw_sample_palette(self):
        # 하단에 사용 가능한 sound stone들 표시
        palette_y = 350
        
        self.draw_text("Sound Stones:", 50, palette_y - 30, (150, 150, 150))
        
        for i, stone in enumerate(self.sound_stones[:5]):  # 최대 5개 표시
            x = 50 + i * 80
            # 원석 모양으로 표현
            pygame.draw.polygon(self.screen, (150, 100, 200),
                              [(x, palette_y), (x+30, palette_y-15), 
                               (x+60, palette_y), (x+30, palette_y+15)])
