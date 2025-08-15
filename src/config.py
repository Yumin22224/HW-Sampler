# ============================================
# config.py - 전역 설정
# ============================================

# Display
WIDTH = 800
HEIGHT = 480
FPS = 60
FULLSCREEN = True

# Hardware Pins
BUTTON_PINS = {
    "PUSH": None,           # P-C, P-DC, P-LC
    "ROTARY_BUTTON": None,  # R-C
    "ROTARY_A": None,       # R-R (A phase)
    "ROTARY_B": None,       # R-R (B phase)
    "TOGGLE_SHORT": None,   # STB
    "TOGGLE_LONG": None,    # LTB
    "RECORD": None,         # REC
}

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