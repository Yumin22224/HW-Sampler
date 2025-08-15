# ============================================
# config.py - 전역 설정
# ============================================

# Display
WIDTH = 800
HEIGHT = 480
FPS = 60
FULLSCREEN = True

USE_GPIO = False  # 지금은 키보드 테스트만

# 핀 매핑 (없는 핀은 None)
BUTTON_PINS = {
    "PUSH_BUTTON":    17,   # P-C/P-DC/P-LC
    "ROTARY_BUTTON":  27,   # R-C
    "REC_BUTTON":     22,   # REC
    "ROTARY_A":       23,   # 로터리 A (단일 채널이면 이 핀만)
    "ROTARY_B":       24,   # 로터리 B (단일 채널이면 None 가능)
}

# 디바운스/타이밍
DEBOUNCE_MS     = 30
DOUBLECLICK_MS  = 300
LONGPRESS_MS    = 600


# Audio Settings
SAMPLE_RATE = 44100
CHANNELS = 2  # Stereo
BUFFER_SIZE = 512

# Game Settings
MAX_LAYERS = 4
MAX_BARS = 8
DEFAULT_BPM = 120

# Colors (예시)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GHOST_BLUE = (100, 150, 200)
TAIL_ORANGE = (255, 150, 50)