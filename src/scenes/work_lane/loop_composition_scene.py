# ============================================
# scenes/work_lane/loop_composition_scene.py
# ============================================
"""Loop Composition Scene - 루프 제작 (비즈공예 메타포)"""

import pygame
from scenes.base_scene import BaseScene
from utils.constants import PC, RC, RR_CW, RR_CCW, PDC, PLC

class LoopCompositionScene(BaseScene):
    MODES = ["LOOP_ADJUST","BAR_NAV","LAYER_NAV","SAMPLE_NAV","SAMPLE_ADJUST"]

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
        self.mode = "LOOP_ADJUST"
        self.current_layer = 0
        self.current_bar = 0
        self.current_sample_idx = 0
    
    def enter(self, **kwargs):
        # 이전 씬에서 받은 sound_stone 추가
        if "sound_stone" in kwargs:
            self.sound_stones.append(kwargs["sound_stone"])
        
        # 레이어 초기화 (아직 없으면)
        if not self.layers:
            self.layers = [[] for _ in range(4)]
    
    def update(self, dt, hw_state):
        # R-R: 현재 모드에서 이동
        if hw_state.get(RR_CW):  self.move(+1)
        if hw_state.get(RR_CCW): self.move(-1)

        # R-C: 하위로 들어가기 / 배치/확정
        if hw_state.get(RC):  self.enter_or_confirm()

        # P-C: 상위로 나오기
        if hw_state.get(PC):  self.back_or_cancel()

        # P-DC: Play/Pause
        if hw_state.get(PDC): self.toggle_playback()

        # PLC: (옵션) 전체 리셋 or BPM 모드 전환 등
    
    def move(self, d):
        if self.mode == "LOOP_ADJUST":
            # 예: BPM/Key/Bars 중 포커스 이동
            self.current_bar = (self.current_bar + d) % self.bars
        elif self.mode == "BAR_NAV":
            self.current_bar = (self.current_bar + d) % self.bars
        elif self.mode == "LAYER_NAV":
            self.current_layer = (self.current_layer + d) % 4
        elif self.mode == "SAMPLE_NAV":
            self.current_sample_idx = (self.current_sample_idx + d) % len(self.sound_stones)

    def enter_or_confirm(self):
        if self.mode == "LOOP_ADJUST":
            # 최상단에서 'Complete' 선택 시만 완료
            if self.check_loop_complete():
                self.complete_loop()
            else:
                self.mode = "BAR_NAV"
        elif self.mode == "BAR_NAV":
            self.mode = "LAYER_NAV"
        elif self.mode == "LAYER_NAV":
            self.mode = "SAMPLE_NAV"
        elif self.mode == "SAMPLE_NAV":
            self.place_or_toggle_sample()
            # 배치 후 SAMPLE_NAV 유지
        elif self.mode == "SAMPLE_ADJUST":
            # 파라미터 확정 등
            pass

    def back_or_cancel(self):
        order = self.MODES
        idx = order.index(self.mode)
        if idx > 0: self.mode = order[idx-1]
        else:
            # 최상위에서 Back은 Recording으로 (메타)
            self.scene_manager.change_scene("recording")

    def place_or_toggle_sample(self):
        if not self.sound_stones: return
        pos = (self.current_layer, self.current_bar)
        # TODO: layers 구조에 현재 샘플 인덱스 토글 삽입/삭제


    
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
