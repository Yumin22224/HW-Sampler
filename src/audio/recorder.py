# ============================================
# audio/recorder.py - 오디오 녹음 기능
# ============================================
"""오디오 녹음 및 재생"""

import pygame
import numpy as np
import wave
import io
from config import SAMPLE_RATE, CHANNELS

class AudioRecorder:
    def __init__(self):
        pygame.mixer.init(frequency=SAMPLE_RATE, channels=CHANNELS)
        self.recording = False
        self.recorded_data = []
        self.sample_rate = SAMPLE_RATE
    
    def start(self):
        """녹음 시작"""
        self.recording = True
        self.recorded_data = []
        # TODO: 실제 마이크 입력 구현
        # 현재는 더미 데이터 생성
        print("Recording started...")
    
    def stop(self):
        """녹음 중지 및 샘플 반환"""
        self.recording = False
        print("Recording stopped")
        
        # TODO: 실제 오디오 데이터 반환
        # 더미 샘플 생성
        duration = 2.0  # 2초
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
        frequency = 440  # A4
        sample = np.sin(2 * np.pi * frequency * t) * 0.3
        
        return {
            "data": sample,
            "sample_rate": self.sample_rate,
            "duration": duration
        }
    
    def play(self, sample):
        """샘플 재생"""
        # TODO: 실제 재생 구현
        print(f"Playing sample with duration: {sample.get('duration', 0)}s")
    
    def stop_playback(self):
        """재생 중지"""
        pygame.mixer.stop()