# ============================================
# inputs/hardware_input.py - 키보드 전용(우선) + GPIO(나중) 호환
# ============================================

import pygame
from utils.constants import PC, RC, RR_CW, RR_CCW, PDC, PLC, REC

try:
    from config import BUTTON_PINS, USE_GPIO  # USE_GPIO = False 권장(키보드 테스트)
except Exception:
    # config가 없거나 키가 없으면 기본값
    BUTTON_PINS, USE_GPIO = {}, False

class HardwareInput:
    def __init__(self):
        # 1프레임 펄스 상태 (씬들이 읽는 키)
        self.state = {PC: False, RC: False, RR_CW: False, RR_CCW: False, PDC: False, PLC: False, REC: False}

        # GPIO는 기본 비활성(키보드 테스트 우선)
        self.gpio_available = False
        self.GPIO = None

        if USE_GPIO:
            try:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO
                self._init_gpio()
                self.gpio_available = True
            except ImportError:
                print("[HardwareInput] RPi.GPIO not found — keyboard-only mode")

    # ---------- 키보드 에뮬 ----------
    def feed_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Back/Meta
            if event.key == pygame.K_ESCAPE:   self.state[PC] = True
            # Confirm/Enter
            elif event.key == pygame.K_RETURN: self.state[RC] = True
            # Rotary CW/CCW
            elif event.key == pygame.K_RIGHT:  self.state[RR_CW] = True
            elif event.key == pygame.K_LEFT:   self.state[RR_CCW] = True
            # Preview (double-click 역할)
            elif event.key == pygame.K_SPACE:  self.state[PDC] = True
            # Long-click
            elif event.key == pygame.K_l:      self.state[PLC] = True
            # Record button
            elif event.key == pygame.K_r:      self.state[REC] = True

    # ---------- 프레임별 입력 읽기 ----------
    def read(self):
        """
        현재 프레임에서 감지된 입력을 반환.
        키보드 입력을 그대로 내보내고,
        USE_GPIO=True인 경우엔 GPIO 이벤트를 OR 병합.
        """
        out = self.state.copy()

        if self.gpio_available and self.GPIO is not None:
            gpio_out = self._read_gpio_once()
            for k, v in gpio_out.items():
                out[k] = out.get(k, False) or v

        return out

    def post_frame_reset(self):
        # 엣지 트리거 보장을 위해 1프레임 후 리셋
        for k in self.state:
            self.state[k] = False

    # ---------- (옵션) GPIO 지원: 나중에 실제 하드웨어 연결 시 사용 ----------
    def _init_gpio(self):
        G = self.GPIO
        G.setmode(G.BCM)

        # 버튼들 (풀업 입력)
        for name, pin in (BUTTON_PINS or {}).items():
            if pin is None:
                continue
            G.setup(pin, G.IN, pull_up_down=G.PUD_UP)

        # 간단 상태 저장
        self._gpio_last = {
            "PUSH": 1, "ROTARY_BUTTON": 1, "REC_BUTTON": 1,
            "ROTARY_A": 1, "ROTARY_B": 1,
        }

    def _read_gpio_once(self):
        """
        최소 동작: falling edge에서 펄스 발생.
        (정교한 더블/롱 클릭/쿼드러처는 실제 연결 시 보강)
        """
        out = {PC: False, RC: False, RR_CW: False, RR_CCW: False, PDC: False, PLC: False, REC: False}
        G = self.GPIO
        get = lambda key: (BUTTON_PINS.get(key), key)

        def falling(pin_key, emit_key):
            pin, key = get(pin_key)
            if pin is None: return
            cur = G.input(pin)
            last = self._gpio_last.get(key, 1)
            if last == 1 and cur == 0:  # pull-up 기준 눌림 엣지
                out[emit_key] = True
            self._gpio_last[key] = cur

        # 매핑: 필요시 config에서 바꿔 사용
        falling("PUSH_BUTTON", PC)
        falling("ROTARY_BUTTON", RC)
        falling("REC_BUTTON", REC)

        # 로터리 (아주 단순: A 하강엣지에서 B 상태로 방향 판정)
        a_pin = BUTTON_PINS.get("ROTARY_A")
        b_pin = BUTTON_PINS.get("ROTARY_B")
        if a_pin is not None and b_pin is not None:
            a = G.input(a_pin); b = G.input(b_pin)
            la = self._gpio_last.get("ROTARY_A", 1)
            if la == 1 and a == 0:  # A falling
                if b == 1: out[RR_CW] = True
                else:      out[RR_CCW] = True
            self._gpio_last["ROTARY_A"] = a
            self._gpio_last["ROTARY_B"] = b

        return out

    def cleanup(self):
        if self.gpio_available and self.GPIO is not None:
            self.GPIO.cleanup()
