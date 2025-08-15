# ============================================
# scenes/work_lane/recording_scene.py
# ============================================
"""Recording Scene - Work Lane의 첫 번째 씬"""

import pygame
import numpy as np
from scenes.base_scene import BaseScene
from audio.recorder import AudioRecorder
from utils.constants import PC, RC, RR_CW, RR_CCW, PDC, PLC, REC

class RecordingScene(BaseScene):
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.recorder = AudioRecorder()
        self.is_recording = False
        self.is_playing = False
        self.recorded_sample = None
        self.animation_frame = 0
        
        # UI 상태
        self.state = "PRE_RECORD"  # PRE_RECORD, RECORDING, POST_RECORD
    
    def enter(self, **kwargs):
        self.state = "PRE_RECORD"
        self.recorded_sample = None
        self.animation_frame = 0
    
    def update(self, dt, hw_state):
        if self.state == "PRE_RECORD":
            # P-C: Library로 이동
            if hw_state.get(PC):
                self.scene_manager.change_scene("library")
            
            # REC: 녹음 시작
            if hw_state.get(REC):
                self.start_recording()
        
        elif self.state == "RECORDING":
            # REC: 녹음 중지
            if hw_state.get(REC):
                self.stop_recording()
            
            # 애니메이션 업데이트
            self.animation_frame += dt * 10
        
        elif self.state == "POST_RECORD":
            if hw_state.get(RC):  self.proceed_to_next()
            if hw_state.get(PDC): self.toggle_playback()
            if hw_state.get(PLC): self.state = "PRE_RECORD"; self.recorded_sample = None
    
    def start_recording(self):
        self.state = "RECORDING"
        self.is_recording = True
        self.recorder.start()
    
    def stop_recording(self):
        self.state = "POST_RECORD"
        self.is_recording = False
        self.recorded_sample = self.recorder.stop()
    
    def toggle_playback(self):
        if self.is_playing:
            self.recorder.stop_playback()
        else:
            if self.recorded_sample:
                self.recorder.play(self.recorded_sample)
        self.is_playing = not self.is_playing
    
    def proceed_to_next(self):
        if self.recorded_sample:
            # 샘플을 다음 씬으로 전달
            self.scene_manager.change_scene("sound_crafting", 
                                           sample=self.recorded_sample)
    
    def draw(self):
        self.screen.fill((20, 25, 30))
        
        if self.state == "PRE_RECORD":
            self.draw_pre_record_ui()
        elif self.state == "RECORDING":
            self.draw_recording_ui()
        elif self.state == "POST_RECORD":
            self.draw_post_record_ui()
    
    def draw_pre_record_ui(self):
        # 타이틀
        self.draw_text("Recording Scene", 300, 50, (100, 150, 200))
        
        # REC 버튼 강조
        pygame.draw.circle(self.screen, (200, 50, 50), (400, 240), 60)
        self.draw_text("REC", 380, 230, (255, 255, 255))
        
        # 안내
        self.draw_text("Press REC to start recording", 250, 350, (150, 150, 150))
        self.draw_text("P-C: Go to Library", 300, 400, (100, 100, 100))
    
    def draw_recording_ui(self):
        # 녹음 중 애니메이션
        radius = 40 + np.sin(self.animation_frame) * 10
        color = (255, 100 + np.sin(self.animation_frame) * 50, 100)
        pygame.draw.circle(self.screen, color, (400, 240), int(radius))
        
        # 상태 표시
        self.draw_text("RECORDING...", 340, 320, (255, 100, 100))
        self.draw_text("Press REC to stop", 320, 380, (150, 150, 150))
    
    def draw_post_record_ui(self):
        # 녹음된 샘플 시각화
        pygame.draw.rect(self.screen, (50, 100, 150), (250, 150, 300, 100))
        self.draw_text("Sample Recorded", 310, 190, (255, 255, 255))
        
        # 컨트롤 옵션
        controls = [
            ("Play", 200, 300, self.is_playing),
            ("Next", 400, 300, False),
            ("Re-record", 600, 300, False)
        ]
        
        for text, x, y, active in controls:
            color = (255, 200, 100) if active else (150, 150, 150)
            self.draw_text(text, x, y, color)
        
        # 안내
        self.draw_text("P-DC: Play | R-C: Next | P-LC: Re-record", 200, 400, (100, 100, 100))
