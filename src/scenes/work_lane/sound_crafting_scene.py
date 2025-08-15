# scenes/work_lane/sound_crafting_scene.py
# Sound Crafting Scene — Navigation / Adjust 2-화면 체계 (요구사항 반영판)
# - Tools (카루셀): Trim - Beginning, Trim - End, Reverse, Speed, EQ - Low Pass, EQ - High Pass, Next
# - NAVIGATE: 중앙에 선택 툴이 수평 정렬된 카루셀(좌/우 이웃 포함)
# - ADJUST: 선택 툴 하나만 + Sound Stone + 전용 커서/슬라이더
#   * Trim: 절대 초 단위 (R-R=0.5s, P-C+R-R=0.05s), 핸들 스위치 없음, 핸들별 툴 분리
#   * Speed: 0.01x ~ 50x (로그 바 표시, 중앙 x1.0 라인), R-R으로 배율 변경, R-C로 Confirm
#   * LP/HP: 기존과 동일(Hz), R-R 변경, R-C Confirm
#   * Reverse: R-C 토글
#   * 모든 툴: ADJUST 재진입 시 커서/표시값을 latest confirm 기준으로 세팅
# - P-C: NAVIGATE로 복귀, P-DC: 프리뷰 토글

import math
import pygame
from scenes.base_scene import BaseScene
from utils.constants import PC, RC, RR_CW, RR_CCW, PDC

# -------------------------------
# 설정/상수
# -------------------------------
TOOLS = [
    "Trim - Beginning",
    "Trim - End",
    "Reverse",
    "Speed",
    "EQ - Low Pass",
    "EQ - High Pass",
    "Next",
]

PC_COMBO_MS = 350  # Trim 미세 조정(P-C + R-R) 콤보 타임아웃

SPEED_MIN = 0.01
SPEED_MAX = 50.0
SPEED_COARSE = 1.10   # R-R coarse 스텝: ×1.10
SPEED_FINE   = 1.01   # (옵션) Trim처럼 P-C 콤보를 쓰고 싶으면 ×1.01 (지금은 미사용)

LP_MIN, LP_MAX = 200, 20000
HP_MIN, HP_MAX = 20, 5000

# -------------------------------
# Scene 구현
# -------------------------------
class SoundCraftingScene(BaseScene):
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.sample = None
        self.sound_stone = None

        self.mode = "NAVIGATE"           # "NAVIGATE" | "ADJUST"
        self.current_tool = 0            # 카루셀 중심 툴 인덱스
        self.selected_tool = None        # ADJUST 대상 툴명

        # 미세조정 콤보(Trim 전용)
        self._pc_combo_started = False
        self._pc_combo_deadline = 0

        # 파라미터(현재값 + last_confirm)
        self.params = {
            "Trim - Beginning": {"sec": 0.00, "last_confirm": 0.00},
            "Trim - End":       {"sec": 0.00, "last_confirm": 0.00},
            "Reverse":          {"on": False},
            "Speed":            {"value": 1.00, "last_confirm": 1.00},     # 배율
            "EQ - Low Pass":    {"cutoff": 20000, "last_confirm": 20000},
            "EQ - High Pass":   {"cutoff": 20,    "last_confirm": 20},
        }
        self.preview_on = False

    # -------- lifecycle --------
    def enter(self, **kwargs):
        self.sample = kwargs.get("sample")
        self._generate_sound_stone()

    def _generate_sound_stone(self):
        # 실제 오디오 처리 대신 구조만 유지
        # duration_sec: 있으면 사용, 없으면 기본 10초
        duration = 10.0
        if isinstance(self.sample, dict):
            duration = float(self.sample.get("duration_sec", duration))
        self.sound_stone = {
            "visual": "stone",
            "properties": {"duration_sec": duration},
            "processed_audio": self.sample
        }
        # Trim End 기본값을 파일 길이(최근 컨펌도 동일)로 초기화
        self.params["Trim - End"]["sec"] = duration
        self.params["Trim - End"]["last_confirm"] = duration

    # -------- 공통 도우미 --------
    def _duration_sec(self):
        return float(self.sound_stone["properties"].get("duration_sec", 10.0)) if self.sound_stone else 10.0

    def _ensure_trim_bounds(self):
        """begin <= end, 0 <= (both) <= duration"""
        dur = self._duration_sec()
        b = self.params["Trim - Beginning"]["sec"]
        e = self.params["Trim - End"]["sec"]
        b = max(0.0, min(dur, b))
        e = max(0.0, min(dur, e))
        if b > e:
            # begin을 우선으로 두고 end를 따라오게
            e = b
        self.params["Trim - Beginning"]["sec"] = b
        self.params["Trim - End"]["sec"] = e

    # -------- update --------
    def update(self, dt, hw):
        # 공통: 프리뷰 토글
        if hw.get(PDC):
            self.preview_on = not self.preview_on
            # TODO: 실제 오디오 프리뷰 처리

        if self.mode == "NAVIGATE":
            self._update_navigate(hw)
        else:
            self._update_adjust(hw)

    def _update_navigate(self, hw):
        # 카루셀 이동
        if hw.get(RR_CW):  self.current_tool = (self.current_tool + 1) % len(TOOLS)
        if hw.get(RR_CCW): self.current_tool = (self.current_tool - 1) % len(TOOLS)

        # 선택
        if hw.get(RC):
            tool = TOOLS[self.current_tool]
            if tool == "Next":
                # 다음 씬으로
                self.scene_manager.change_scene("loop_composition", sound_stone=self.sound_stone)
                return
            self.selected_tool = tool
            self.mode = "ADJUST"
            # ADJUST 진입 시 커서를 latest confirm으로 세팅
            self._recall_last_confirm(tool)

        # NAVIGATE에선 P-C 의미 없음

    def _update_adjust(self, hw):
        tool = self.selected_tool

        # P-C: NAVIGATE 복귀
        if hw.get(PC):
            self.mode = "NAVIGATE"
            self.selected_tool = None
            self._pc_combo_started = False
            return

        # Trim 전용: P-C + R-R 콤보(미세 0.05s)
        if tool.startswith("Trim") and hw.get(PC):
            self._pc_combo_started = True
            self._pc_combo_deadline = pygame.time.get_ticks() + PC_COMBO_MS

        # 값 변경
        if hw.get(RR_CW) or hw.get(RR_CCW):
            d = 1 if hw.get(RR_CW) else -1
            if tool == "Trim - Beginning":
                step = 0.05 if self._is_pc_combo_alive() else 0.5
                self.params[tool]["sec"] += d * step
                self._ensure_trim_bounds()
                self._consume_pc_combo()
            elif tool == "Trim - End":
                step = 0.05 if self._is_pc_combo_alive() else 0.5
                self.params[tool]["sec"] += d * step
                self._ensure_trim_bounds()
                self._consume_pc_combo()
            elif tool == "Speed":
                # 배율은 곱셈 스텝(로그 감각): coarse ×1.10
                v = self.params["Speed"]["value"]
                v = v * (SPEED_COARSE if d > 0 else 1.0 / SPEED_COARSE)
                self.params["Speed"]["value"] = max(SPEED_MIN, min(SPEED_MAX, v))
            elif tool == "EQ - Low Pass":
                self.params[tool]["cutoff"] = max(LP_MIN, min(LP_MAX, self.params[tool]["cutoff"] + d * 100))
            elif tool == "EQ - High Pass":
                self.params[tool]["cutoff"] = max(HP_MIN, min(HP_MAX, self.params[tool]["cutoff"] + d * 20))
            # Reverse는 R-R 없음

        # Confirm / Toggle
        if hw.get(RC):
            if tool == "Reverse":
                self.params["Reverse"]["on"] = not self.params["Reverse"]["on"]
            elif tool == "Trim - Beginning":
                self.params[tool]["last_confirm"] = self.params[tool]["sec"]
            elif tool == "Trim - End":
                self.params[tool]["last_confirm"] = self.params[tool]["sec"]
            elif tool == "Speed":
                self.params["Speed"]["last_confirm"] = self.params["Speed"]["value"]
            elif tool == "EQ - Low Pass":
                self.params["EQ - Low Pass"]["last_confirm"] = self.params["EQ - Low Pass"]["cutoff"]
            elif tool == "EQ - High Pass":
                self.params["EQ - High Pass"]["last_confirm"] = self.params["EQ - High Pass"]["cutoff"]
            # 컨펌해도 ADJUST 유지

        # 콤보 타임아웃
        if self._pc_combo_started and pygame.time.get_ticks() > self._pc_combo_deadline:
            self._pc_combo_started = False

    def _recall_last_confirm(self, tool):
        """ADJUST 재진입 시 커서를 latest confirm 값으로 복원"""
        if tool in ("Trim - Beginning", "Trim - End"):
            self.params[tool]["sec"] = float(self.params[tool]["last_confirm"])
            self._ensure_trim_bounds()
        elif tool == "Speed":
            self.params["Speed"]["value"] = float(self.params["Speed"]["last_confirm"])
        elif tool == "EQ - Low Pass":
            self.params["EQ - Low Pass"]["cutoff"] = int(self.params["EQ - Low Pass"]["last_confirm"])
        elif tool == "EQ - High Pass":
            self.params["EQ - High Pass"]["cutoff"] = int(self.params["EQ - High Pass"]["last_confirm"])
        # Reverse는 on/off 그대로 보임

    def _is_pc_combo_alive(self):
        return self._pc_combo_started and pygame.time.get_ticks() <= self._pc_combo_deadline

    def _consume_pc_combo(self):
        if self._pc_combo_started:
            self._pc_combo_started = False

    # -------- draw --------
    def draw(self):
        self.screen.fill((25, 30, 35))
        self.draw_text("Sound Crafting", 320, 24, (100, 150, 200))

        if self.mode == "NAVIGATE":
            self._draw_navigate_carousel()
        else:
            self._draw_adjust_panel()

    # ------- NAVIGATE (카루셀) -------
    def _draw_navigate_carousel(self):
        # 좌: Sound Stone
        self._draw_stone_card(40, 80, 260, 260)

        # -------- 오른쪽 반원 카루셀 레이아웃 --------
        W, H = self.screen.get_width(), self.screen.get_height()
        cx = W + 140               # 원 중심: 화면 오른쪽 바깥 (반원만 보이게)
        cy = H // 2                # 수직 중앙
        R  = 260                   # 반지름(필요하면 조정)

        # 선택 툴은 각도 0(rad) 지점(=화면쪽, 좌향) — 항상 수평
        # 나머지는 각도 ±k*θ 간격으로 위/아래에 배치
        n = len(TOOLS)
        theta_step = math.radians(22)   # 툴 간 각도 간격 (시각적으로 20~24˚ 권장)
        max_visible = 4                 # 위/아래로 각 4개까지 그리기(성능/가독)

        center_idx = self.current_tool
        center_name = TOOLS[center_idx]
        center_pos  = (cx - R, cy)      # 각도 0에서의 포지션
        self._draw_tool_chip_arc(center_name, center_pos, selected=True, angle_rad=0.0)

        # 좌/우(위/아래) 이웃들
        for i in range(n):
            if i == center_idx:
                continue
            rel = self._relative_ring_index(i, center_idx, n)  # -N/2..+N/2 범위로 보정
            if abs(rel) > max_visible:
                continue
            ang = rel * theta_step
            x = cx - R * math.cos(ang)
            y = cy + R * math.sin(ang)
            self._draw_tool_chip_arc(TOOLS[i], (x, y), selected=False, angle_rad=ang)

        # 안내
        self.draw_text("R-R: Rotate toolbox  |  R-C: Select/Next  |  P-DC: Preview",
                    120, 430, (110, 110, 110))


    def _draw_tool_chip_arc(self, name, pos, selected=False, angle_rad=0.0):
        """
        반원 트랙 위에 툴 박스를 배치하여 그린다.
        - selected=True: 항상 수평(회전 없음), 크고 강조
        - selected=False: 호의 접선 방향으로 살짝 기울여 렌더링
        """
        # 박스 크기/색
        w, h = (210, 56) if selected else (160, 44)
        bg   = (50, 50, 60) if selected else (36, 40, 48)
        fg   = (255, 200, 100) if selected else (170, 170, 170)
        border_radius = 12 if selected else 10

        # 먼저 수평 박스를 그린 Surface 생성
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, bg, (0, 0, w, h), border_radius=border_radius)
        # 텍스트(수평 기준으로 그려놓고, 필요 시 전체 Surface를 회전시킴)
        self._blit_text_center(surf, name, fg)

        # 선택된 항목은 회전 없이, 나머지는 각도에 따라 약간 회전(접선 방향)
        if selected:
            rect = surf.get_rect(center=(int(pos[0]), int(pos[1])))
            self.screen.blit(surf, rect)
        else:
            tilt_deg = -math.degrees(angle_rad) * 0.55   # 기울기 계수(호 접선 느낌)
            rsurf = pygame.transform.rotate(surf, tilt_deg)
            rect = rsurf.get_rect(center=(int(pos[0]), int(pos[1])))
            self.screen.blit(rsurf, rect)


    def _draw_stone_card(self, x, y, w, h):
        pygame.draw.rect(self.screen, (80, 100, 120), (x, y, w, h), border_radius=8)
        self.draw_text("Sound Stone", x + 68, y + h // 2 - 10, (255, 255, 255))
        if self.preview_on:
            self.draw_text("Preview: ON", x + 64, y + h // 2 + 26, (180, 230, 180))

    # ------- ADJUST -------
    def _draw_adjust_panel(self):
        tool = self.selected_tool
        # 좌: Sound Stone
        self._draw_stone_card(40, 80, 260, 260)

        # 우: 선택 툴 패널
        panel = pygame.Rect(340, 80, 380, 260)
        pygame.draw.rect(self.screen, (40, 46, 56), panel, border_radius=12)
        self.draw_text(tool, panel.x + 16, panel.y - 26, (200, 200, 210))

        if tool == "Trim - Beginning":
            self._draw_trim_panel(panel, handle="begin")
        elif tool == "Trim - End":
            self._draw_trim_panel(panel, handle="end")
        elif tool == "Reverse":
            self._draw_reverse_panel(panel)
        elif tool == "Speed":
            self._draw_speed_panel(panel)
        elif tool == "EQ - Low Pass":
            self._draw_lowpass_panel(panel)
        elif tool == "EQ - High Pass":
            self._draw_highpass_panel(panel)

        self.draw_text("R-R: Adjust  |  R-C: Confirm/Toggle  |  P-C: Back  |  P-DC: Preview",
                       110, 430, (110, 110, 110))

    # ---- tool panels ----
    def _draw_trim_panel(self, panel, handle="begin"):
        dur = self._duration_sec()
        b = self.params["Trim - Beginning"]["sec"]
        e = self.params["Trim - End"]["sec"]
        cur_val = b if handle == "begin" else e
        last = self.params["Trim - Beginning"]["last_confirm"] if handle == "begin" \
               else self.params["Trim - End"]["last_confirm"]

        # 타임라인 바
        bar = pygame.Rect(panel.x + 20, panel.y + 110, panel.width - 40, 10)
        pygame.draw.rect(self.screen, (60, 66, 78), bar, border_radius=6)

        # 현재 트림 영역 하이라이트
        bx = bar.x + int(bar.width * (b / max(0.001, dur)))
        ex = bar.x + int(bar.width * (e / max(0.001, dur)))
        pygame.draw.rect(self.screen, (255, 150, 60), (bx, bar.y, max(2, ex - bx), bar.height), border_radius=6)

        # 현재 조정 핸들(노란색), 상대 핸들(회색)
        curx = bar.x + int(bar.width * (cur_val / max(0.001, dur)))
        othx = bar.x + int(bar.width * ((e if handle == "begin" else b) / max(0.001, dur)))
        pygame.draw.circle(self.screen, (255, 210, 140), (curx, bar.y + 5), 6)
        pygame.draw.circle(self.screen, (160, 160, 160), (othx, bar.y + 5), 6)

        # 최근 컨펌 값(얇은 금색 라인)
        lx = bar.x + int(bar.width * (last / max(0.001, dur)))
        pygame.draw.line(self.screen, (255, 220, 160), (lx, bar.y - 2), (lx, bar.y + bar.height + 2), 1)

        self.draw_text(f"{'Begin' if handle=='begin' else 'End'}: {cur_val:0.2f}s / {dur:0.2f}s"
                       "   (R-R=0.5s, P-C+R-R=0.05s, R-C=Confirm)",
                       panel.x + 20, panel.y + 70, (170, 170, 170))

    def _draw_reverse_panel(self, panel):
        on = self.params["Reverse"]["on"]
        pygame.draw.rect(self.screen, (60, 66, 78), (panel.x + 20, panel.y + 80, panel.width - 40, 60), border_radius=8)
        self.draw_text("Reverse", panel.x + 30, panel.y + 98, (250, 230, 200))
        self.draw_text("ON" if on else "OFF", panel.x + 260, panel.y + 98,
                       (180, 230, 180) if on else (230, 180, 180))
        self.draw_text("(R-C to toggle)", panel.x + 30, panel.y + 150, (140, 140, 140))

    def _draw_speed_panel(self, panel):
        v = self.params["Speed"]["value"]
        last = self.params["Speed"]["last_confirm"]

        # 로그 바 매핑: 0..1 ← log(v / 0.01) / log(50 / 0.01)
        def to_ratio(val):
            val = max(SPEED_MIN, min(SPEED_MAX, val))
            return (math.log10(val) - math.log10(SPEED_MIN)) / (math.log10(SPEED_MAX) - math.log10(SPEED_MIN))

        ratio = to_ratio(v)
        lastr = to_ratio(last)

        # 바
        x, y = panel.x + 20, panel.y + 120
        w, h = panel.width - 40, 10
        pygame.draw.rect(self.screen, (60, 66, 78), (x, y, w, h), border_radius=6)
        pygame.draw.rect(self.screen, (255, 150, 60), (x, y, int(w * ratio), h), border_radius=6)
        # 최근 컨펌 라인
        lx = x + int(w * lastr)
        pygame.draw.line(self.screen, (255, 220, 160), (lx, y - 2), (lx, y + h + 2), 1)
        # 중앙 x1.0 마커
        cxr = to_ratio(1.0)
        cx = x + int(w * cxr)
        pygame.draw.line(self.screen, (200, 210, 230), (cx, y - 6), (cx, y + h + 6), 1)

        # 레이블
        self.draw_text(f"x{v:0.2f}   (range x0.01 ~ x50)", x + w + 12, y - 4, (170, 170, 170))

    def _draw_lowpass_panel(self, panel):
        cut = self.params["EQ - Low Pass"]["cutoff"]
        last = self.params["EQ - Low Pass"]["last_confirm"]
        self._draw_linear_bar_with_confirm(panel, cut, last, LP_MIN, LP_MAX, label=lambda v: f"{v} Hz")

    def _draw_highpass_panel(self, panel):
        cut = self.params["EQ - High Pass"]["cutoff"]
        last = self.params["EQ - High Pass"]["last_confirm"]
        self._draw_linear_bar_with_confirm(panel, cut, last, HP_MIN, HP_MAX, label=lambda v: f"{v} Hz")

    # ---- draw helpers ----
    def _draw_linear_bar_with_confirm(self, panel, value, last, vmin, vmax, label=lambda v: str(v)):
        x, y = panel.x + 20, panel.y + 120
        w, h = panel.width - 40, 10
        ratio = (value - vmin) / float(vmax - vmin)
        lastr = (last - vmin) / float(vmax - vmin)
        pygame.draw.rect(self.screen, (60, 66, 78), (x, y, w, h), border_radius=6)
        pygame.draw.rect(self.screen, (255, 150, 60), (x, y, int(w * ratio), h), border_radius=6)
        lx = x + int(w * lastr)
        pygame.draw.line(self.screen, (255, 220, 160), (lx, y - 2), (lx, y + h + 2), 1)
        self.draw_text(f" {label(value)}", x + w + 12, y - 4, (170, 170, 170))

    def _relative_ring_index(self, i, cur, n):
        """
        원형 인덱스에서 i가 cur로부터 얼마나 떨어졌는지 -n/2..+n/2 범위로 반환
        (예: cur=3, i=0, n=7 -> rel=-3)
        """
        d = i - cur
        # 가장 가까운 방향으로 보정
        if d > n // 2:
            d -= n
        elif d < -n // 2:
            d += n
        return d

    def _blit_text_center(self, surf, text, color):
        # BaseScene의 폰트를 사용해 수평 중앙 정렬
        label = self.font.render(text, True, color)
        rect = label.get_rect(center=(surf.get_width() // 2, surf.get_height() // 2))
        surf.blit(label, rect)

