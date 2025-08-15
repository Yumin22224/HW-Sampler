# ============================================
# inputs/hardware_input.py - 하드웨어 입력 처리
# ============================================

import pygame
from config import BUTTON_PINS

class HardwareInput:
    def __init__(self):
        self.gpio_available = False
        self.last_rotary_state = (0, 0)
        self.button_states = {}
        self.button_timers = {}
        
        # GPIO 초기화 시도
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.setup_gpio()
            self.gpio_available = True
        except ImportError:
            print("GPIO not available, using keyboard fallback")
    
    def setup_gpio(self):
        if not self.gpio_available:
            return
        
        self.GPIO.setmode(self.GPIO.BCM)
        for name, pin in BUTTON_PINS.items():
            if pin is not None:
                if "ROTARY" in name and name != "ROTARY_BUTTON":
                    # 로터리 엔코더 A, B 상
                    self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
                else:
                    # 일반 버튼
                    self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
    
    def read(self):
        \"\"\"현재 하드웨어 상태 읽기\"\"\"
        state = {}
        
        if self.gpio_available:
            # GPIO 읽기
            state = self.read_gpio()
        
        # 클릭 타입 판별 (single, double, long)
        state.update(self.process_click_types())
        
        # 로터리 회전 감지
        state.update(self.process_rotary())
        
        return state
    
    def read_gpio(self):
        # TODO: GPIO 읽기 구현
        return {}
    
    def process_click_types(self):
        \"\"\"클릭 타입 처리 (P-C, P-DC, P-LC)\"\"\"
        # TODO: 타이밍 기반 클릭 타입 판별
        return {}
    
    def process_rotary(self):
        \"\"\"로터리 엔코더 회전 감지\"\"\"
        # TODO: 쿼드러처 디코딩
        return {}
    
    def handle_keyboard(self, event):
        \"\"\"개발용 키보드 매핑\"\"\"
        # Space: Push Button
        # Left/Right: Rotary
        # R: Record Button
        # T: Toggle Buttons
        pass
    
    def cleanup(self):
        if self.gpio_available:
            self.GPIO.cleanup()