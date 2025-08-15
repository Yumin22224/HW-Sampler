# ============================================
# Loop Composition Scene — 5단계 드릴다운 상태머신 (MVP)
# 설계 반영:
#   1) Loop Adjust  2) Bar Nav  3) Layer Nav  4) Sample Nav  5) Sample Adjust
#   - R-C: 하위로 / P-C: 상위로 / R-R: 현재 레벨 탐색/조정
#   - P-DC: 프리뷰 / P-LC: 리셋(맥락별)
#   - Sample Nav: 16th grid + P-C+R-R = 32nd 미세 이동(콤보 타임아웃)
#   - 충돌 시 덮어쓰기, Bar 경계 자동 클리핑
#   - Sample Adjust: Melody/Rhythm, Pitch(스케일/크로매틱), Gain
# ============================================

import pygame
from scenes.base_scene import BaseScene
from utils.constants import PC, RC, RR_CW, RR_CCW, PDC, PLC

# --- 기본 파라미터(없으면 이 값 사용) ---
GRID_STEPS = 16          # 1 bar = 16분음표 그리드
FINE_STEPS = 32          # P-C+R-R 콤보 시 32분음표 정밀도
MAX_LAYERS = 8
PC_COMBO_MS = 350        # P-C 누른 뒤 이 시간 내 R-R이 오면 '콤보'로 간주

MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]  # 장음계(반음 오프셋)
KEYS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

def clamp(v, lo, hi): return max(lo, min(hi, v))

class LoopCompositionScene(BaseScene):
    MODES = ("LOOP_ADJUST","BAR_NAV","LAYER_NAV","SAMPLE_NAV","SAMPLE_ADJUST")

    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)

        # 전역/루프 상태
        self.mode = "LOOP_ADJUST"
        self.bpm = 120
        self.key_idx = 0  # index in KEYS
        self.bars = 4

        # 데이터 구조: bars × layers × samples
        # layers는 가변. 각 bar에서 layer별로 samples 리스트를 가짐
        self.layers = []              # 레이어 이름/메타
        self.grid = []                # [bar][layer] = [sample, ...]
        self._ensure_min_layers(1)
        self._ensure_bars(self.bars)

        # 포커스/커서
        self.loop_focus = 0          # 0: Loop / 1:BPM / 2:Key / 3:Bars
        self.current_bar = 0
        self.layer_cursor = 0        # 레이어 선택(⊕ 포함)
        self.current_layer = 0       # 실제 편집 타겟(샘플 작업 시)
        self.tick = 0                # Sample Nav 커서 (0..FINE_STEPS-1)
        self.selected_sample = None  # Sample Adjust 타깃

        # 샘플 팔레트(Work Lane에서 넘어온 최신 sound_stone)
        self.palette = []            # [{id, name, length_ticks, data...}]
        self.palette_idx = 0

        # P-C + R-R 콤보 처리(Modifier)
        self._pc_combo_started = False
        self._pc_combo_deadline = 0

        # 재생 상태(프리뷰)
        self.playing = False

    # ---------- Scene lifecycle ----------
    def enter(self, **kwargs):
        if "sound_stone" in kwargs and kwargs["sound_stone"] is not None:
            self._ingest_sound_stone(kwargs["sound_stone"])

    def exit(self): pass

    # ---------- Helpers ----------
    def _ingest_sound_stone(self, stone):
        # 데모용 length: 4 * 32nd = 1/8 note (원하면 조정)
        item = {
            "id": len(self.palette),
            "name": "Stone {}".format(len(self.palette)),
            "length": max(1, FINE_STEPS // 8),   # ticks (32분 기준)
            "data": stone
        }
        self.palette.append(item)
        self.palette_idx = len(self.palette) - 1

    def _ensure_min_layers(self, n):
        while len(self.layers) < n:
            self.layers.append({"name": f"Layer {len(self.layers)}"})
        # grid 확장도 bar 생성 때 수행

    def _ensure_bars(self, n):
        # grid 크기를 bars × layers로 맞추기
        if not self.grid:
            self.grid = [[[] for _ in range(len(self.layers))] for _ in range(n)]
        else:
            cur_bars = len(self.grid)
            if n > cur_bars:
                for _ in range(n - cur_bars):
                    self.grid.append([[] for _ in range(len(self.layers))])
            elif n < cur_bars:
                self.grid = self.grid[:n]

    def _ensure_layers_in_grid(self):
        # layers 길이가 바뀌었으면 grid의 각 bar에 layer 슬롯 맞추기
        L = len(self.layers)
        for b in range(len(self.grid)):
            cur = len(self.grid[b])
            if L > cur:
                self.grid[b].extend([[] for _ in range(L - cur)])
            elif L < cur:
                self.grid[b] = self.grid[b][:L]

    def _bar_layers(self, bar_idx):
        return self.grid[bar_idx]

    # ---------- Update ----------
    def update(self, dt, hw):
        # 콤보 만료 처리
        if self._pc_combo_started and pygame.time.get_ticks() > self._pc_combo_deadline:
            # 콤보 시간 내 R-R이 없었다면 "Back"으로 처리
            self._pc_combo_started = False
            self._back_action()

        # 공통 입력
        if hw.get(PDC):
            self._toggle_preview()

        if hw.get(PLC):
            self._long_press_reset()

        # 모드 별 처리
        if self.mode == "LOOP_ADJUST":
            self._update_loop_adjust(hw)
        elif self.mode == "BAR_NAV":
            self._update_bar_nav(hw)
        elif self.mode == "LAYER_NAV":
            self._update_layer_nav(hw)
        elif self.mode == "SAMPLE_NAV":
            self._update_sample_nav(hw)
        elif self.mode == "SAMPLE_ADJUST":
            self._update_sample_adjust(hw)

    # ----- Mode 1: Loop Adjust -----
    def _update_loop_adjust(self, hw):
        if hw.get(RR_CW):  self.loop_focus = (self.loop_focus + 1) % 4
        if hw.get(RR_CCW): self.loop_focus = (self.loop_focus - 1) % 4

        if hw.get(RC):
            if self.loop_focus == 0:  # Loop → Bar Nav
                self.mode = "BAR_NAV"
            elif self.loop_focus == 1:  # BPM 값 조정 (R-C로 '확정' 개념만)
                self.bpm = clamp(self.bpm + 1, 40, 220)
            elif self.loop_focus == 2:  # Key
                self.key_idx = (self.key_idx + 1) % len(KEYS)
            elif self.loop_focus == 3:  # Bars
                self.bars = clamp(self.bars + 1, 1, 16)
                self._ensure_bars(self.bars)

        if hw.get(PC):
            # 최상위라 Back 없음(무시)
            pass

    # ----- Mode 2: Bar Navigation -----
    def _update_bar_nav(self, hw):
        if hw.get(RR_CW):  self.current_bar = (self.current_bar + 1) % self.bars
        if hw.get(RR_CCW): self.current_bar = (self.current_bar - 1) % self.bars

        if hw.get(RC):     self.mode = "LAYER_NAV"
        if hw.get(PC):     self.mode = "LOOP_ADJUST"
        if hw.get(PLC):    self._reset_bar(self.current_bar)

    def _reset_bar(self, b):
        for l in range(len(self.layers)):
            self.grid[b][l].clear()

    # ----- Mode 3: Layer Navigation -----
    def _update_layer_nav(self, hw):
        # 레이어 목록 + ⊕ (추가)
        total_slots = len(self.layers) + 1
        if hw.get(RR_CW):  self.layer_cursor = (self.layer_cursor + 1) % total_slots
        if hw.get(RR_CCW): self.layer_cursor = (self.layer_cursor - 1) % total_slots

        if hw.get(RC):
            if self.layer_cursor == len(self.layers):
                # ⊕ 추가
                if len(self.layers) < MAX_LAYERS:
                    self.layers.append({"name": f"Layer {len(self.layers)}"})
                    self._ensure_layers_in_grid()
                    self.current_layer = len(self.layers) - 1
                    self.mode = "SAMPLE_NAV"
            else:
                self.current_layer = self.layer_cursor
                self.mode = "SAMPLE_NAV"

        if hw.get(PC):
            self.mode = "BAR_NAV"

        if hw.get(PLC):
            # 포커스 레이어 삭제(⊕는 삭제 불가)
            if self.layer_cursor < len(self.layers):
                del_layer = self.layer_cursor
                # grid에서 해당 레이어 제거
                for b in range(self.bars):
                    del self.grid[b][del_layer]
                # layers에서 제거 후 이름 재정렬
                del self.layers[del_layer]
                for i, info in enumerate(self.layers):
                    info["name"] = f"Layer {i}"
                self._ensure_layers_in_grid()
                # 커서 보정
                self.layer_cursor = min(self.layer_cursor, len(self.layers))

    # ----- Mode 4: Sample Navigation -----
    def _update_sample_nav(self, hw):
        # P-C 콤보 관문
        if hw.get(PC):
            self._pc_combo_started = True
            self._pc_combo_deadline = pygame.time.get_ticks() + PC_COMBO_MS
            # Back은 콤보가 실패했을 때 실행됨(위 update()에서)

        step = FINE_STEPS // 1  # 기본: 32분음표 단위
        if hw.get(RR_CW) or hw.get(RR_CCW):
            d = 1 if hw.get(RR_CW) else -1
            if self._pc_combo_started:
                # P-C + R-R = 미세(32nd) — 이미 fine 이므로 속도만 다르게 하고 Back 취소
                self.tick = (self.tick + d) % FINE_STEPS
                self._pc_combo_started = False  # 콤보 소비: Back 취소
            else:
                # 일반 회전: 16th grid에 스냅
                coarse = FINE_STEPS // (FINE_STEPS // GRID_STEPS)  # =2
                self.tick = int((self.tick + d * coarse) % FINE_STEPS)

        # R-C: 비어있으면 배치, 있으면 Adjust로
        if hw.get(RC):
            samples = self.grid[self.current_bar][self.current_layer]
            hit = self._find_sample_at_tick(samples, self.tick)
            if hit is None:
                self._place_sample(self.current_bar, self.current_layer, self.tick)
            else:
                self.selected_sample = hit
                self.mode = "SAMPLE_ADJUST"

        # P-DC: 레이어 프리뷰
        if hw.get(PDC):
            self._preview_layer(self.current_bar, self.current_layer)

    def _find_sample_at_tick(self, samples, tick):
        for s in samples:
            if s["start"] <= tick < s["start"] + s["length"]:
                return s
        return None

    def _place_sample(self, bar, layer, tick):
        if not self.palette:
            return
        tpl = self.palette[self.palette_idx]
        length = tpl["length"]
        start = tick
        end = min(FINE_STEPS, start + length)  # bar 경계 클리핑
        length = end - start
        if length <= 0:  # bar 끝이라면 배치 불가
            return

        samples = self.grid[bar][layer]

        # 충돌은 덮어쓰기: 겹치는 기존 샘플 제거
        samples[:] = [s for s in samples
                      if not (max(s["start"], start) < min(s["start"] + s["length"], end))]

        # 배치
        samples.append({
            "start": start,
            "length": length,
            "tpl": tpl,            # 팔레트 참조
            "melody": True,        # Melody/Rhythm 토글
            "pitch": 0,            # semitone
            "gain": 100            # %
        })
        # 시작 위치 기준 정렬
        samples.sort(key=lambda s: s["start"])

    # ----- Mode 5: Sample Adjust -----
    def _update_sample_adjust(self, hw):
        s = self.selected_sample
        if s is None:
            self.mode = "SAMPLE_NAV"
            return

        # 포커스: 0:Toggle, 1:Pitch, 2:Gain
        if not hasattr(self, "_sa_focus"):
            self._sa_focus = 0
        if hw.get(RR_CW):  self._sa_focus = (self._sa_focus + 1) % 3
        if hw.get(RR_CCW): self._sa_focus = (self._sa_focus - 1) % 3

        if hw.get(RC):
            # Pitch/Gain은 R-C로 '컨펌' 개념만 두고 값은 R-R에서 이미 적용
            if self._sa_focus == 0:
                s["melody"] = not s["melody"]   # Melody/Rhythm 토글
            # 1,2는 컨펌해도 머무름

        if hw.get(PC):
            # Pitch에서 P-C + R-R을 지원해야 함 → 콤보 모드로 전환
            self._pc_combo_started = True
            self._pc_combo_deadline = pygame.time.get_ticks() + PC_COMBO_MS
            # Back은 콤보 실패 시 동작(최상위 update에서 처리)

        # 값 조정
        if hw.get(RR_CW) or hw.get(RR_CCW):
            d = 1 if hw.get(RR_CW) else -1
            if self._sa_focus == 1:  # Pitch
                if s["melody"]:
                    # Melody 모드: 기본은 스케일 스텝, P-C 콤보면 크로매틱
                    if self._pc_combo_started:
                        s["pitch"] = clamp(s["pitch"] + d, -24, 24)
                        self._pc_combo_started = False  # 콤보 소비 → Back 취소
                    else:
                        # 스케일 스텝 이동
                        s["pitch"] = self._pitch_step_in_scale(s["pitch"], d)
                else:
                    # Rhythm 모드에선 pitch 조정 무시
                    pass
            elif self._sa_focus == 2:  # Gain
                s["gain"] = clamp(s["gain"] + d * 2, 0, 200)

        if hw.get(PDC):
            self._preview_sample(s)

        if hw.get(PLC):
            s["pitch"] = 0
            s["gain"] = 100
            s["melody"] = True

        # Back 처리: 콤보가 아니면 상위로
        # (콤보는 update()에서 타이머 만료 시 Back 실행)
        # 여기서는 별도 처리 없이 둔다.

    def _pitch_step_in_scale(self, cur_semi, dir_):
        """
        현재 키/스케일 기준으로 다음 스케일 음으로 이동.
        cur_semi: 현재 반음 오프셋
        dir_: +1 / -1
        """
        # 스케일에서 상대 반음 표를 만들고, 가까운 다음/이전 음 찾기
        # 간단 구현: 반음 범위(-24~24)에서 스케일 음들을 생성해 탐색
        base = MAJOR_SCALE
        # 현재 키의 0~12 범위 스케일 음들
        key_offset = self.key_idx  # C->0, C#->1 ...
        allowed = set()
        for o in range(-3, 4):  # 약 7옥타브 커버
            for deg in base:
                allowed.add(o*12 + ((deg + key_offset) % 12))
        # 가장 가까운 다음/이전 허용 반음
        nxt = cur_semi + 1
        prv = cur_semi - 1
        while nxt <= 24 and nxt not in allowed: nxt += 1
        while prv >= -24 and prv not in allowed: prv -= 1
        return clamp(nxt if dir_ > 0 else prv, -24, 24)

    # ----- 공통 Back/Preview/Reset 동작 -----
    def _back_action(self):
        if self.mode == "BAR_NAV":
            self.mode = "LOOP_ADJUST"
        elif self.mode == "LAYER_NAV":
            self.mode = "BAR_NAV"
        elif self.mode == "SAMPLE_NAV":
            self.mode = "LAYER_NAV"
        elif self.mode == "SAMPLE_ADJUST":
            self.mode = "SAMPLE_NAV"

    def _long_press_reset(self):
        if self.mode == "BAR_NAV":
            self._reset_bar(self.current_bar)
        elif self.mode == "LAYER_NAV":
            # 현재 포커스 레이어 삭제
            if self.layer_cursor < len(self.layers):
                # 위와 동일 로직
                del_layer = self.layer_cursor
                for b in range(self.bars):
                    del self.grid[b][del_layer]
                del self.layers[del_layer]
                for i, info in enumerate(self.layers):
                    info["name"] = f"Layer {i}"
                self._ensure_layers_in_grid()
                self.layer_cursor = min(self.layer_cursor, len(self.layers))
        elif self.mode == "SAMPLE_ADJUST" and self.selected_sample is not None:
            s = self.selected_sample
            s["pitch"] = 0; s["gain"] = 100; s["melody"] = True

    def _toggle_preview(self):
        self.playing = not self.playing
        # TODO: 실제 오디오 루프 미리듣기

    def _preview_layer(self, bar, layer):
        # TODO: 해당 레이어만 프리뷰
        print(f"[Preview] Bar {bar}, Layer {layer}")

    def _preview_sample(self, sample):
        # TODO: 개별 샘플 프리뷰
        print(f"[Preview] Sample gain={sample['gain']} pitch={sample['pitch']}")

    # ---------- Draw ----------
    def draw(self):
        self.screen.fill((20, 22, 26))
        # 상단 글로벌 정보
        top = f"BPM {self.bpm} | Key {KEYS[self.key_idx]} | Bars {self.bars}"
        self.draw_text(top, 20, 20, (160, 160, 170))
        mode_txt = f"[{self.mode}]"
        self.draw_text(mode_txt, 680, 20, (120, 170, 220))

        if self.mode == "LOOP_ADJUST":
            self._draw_loop_adjust()
        elif self.mode == "BAR_NAV":
            self._draw_bar_nav()
        elif self.mode == "LAYER_NAV":
            self._draw_layer_nav()
        elif self.mode == "SAMPLE_NAV":
            self._draw_sample_nav()
        elif self.mode == "SAMPLE_ADJUST":
            self._draw_sample_adjust()

    # ---- Draw helpers ----
    def _draw_loop_adjust(self):
        # 중앙 루프 미니맵
        pygame.draw.rect(self.screen, (40, 46, 56), (100, 120, 600, 80), border_radius=8)
        self.draw_text("Loop  [ Bar 0 | Bar 1 | Bar 2 | ... ]", 140, 150, (230, 230, 230))

        # 상단 툴 버튼군 (Loop/BPM/Key/Bars)
        items = ["Loop", "BPM", "Key", "Bars"]
        x0 = 120
        for i, name in enumerate(items):
            x = x0 + i * 150
            sel = (i == self.loop_focus)
            pygame.draw.rect(self.screen, (55, 60, 72) if sel else (36, 40, 48),
                             (x, 60, 120, 34), 0, border_radius=6)
            col = (255, 200, 120) if sel else (160, 160, 160)
            label = name
            if name == "BPM": label += f": {self.bpm}"
            if name == "Key": label += f": {KEYS[self.key_idx]}"
            if name == "Bars": label += f": {self.bars}"
            self.draw_text(label, x + 10, 68, col)

        # 안내
        self.draw_text("R-R: Move focus  |  R-C: Drill/Confirm  |  P-DC: Preview", 160, 420, (115, 115, 120))

    def _draw_bar_nav(self):
        # 바 리스트
        self.draw_text("Select Bar", 120, 80, (200, 200, 210))
        x0, y0, w, h = 100, 120, 600, 80
        pygame.draw.rect(self.screen, (40, 46, 56), (x0, y0, w, h), border_radius=8)

        for b in range(self.bars):
            bx = x0 + int(w * b / self.bars)
            bw = int(w / self.bars) - 4
            rect = (bx + 2, y0 + 8, bw, h - 16)
            sel = (b == self.current_bar)
            pygame.draw.rect(self.screen, (80, 110, 170) if sel else (60, 66, 78), rect, 0, border_radius=6)
            self.draw_text(f"Bar {b}", bx + 10, y0 + 38, (250, 230, 200) if sel else (160, 160, 160))

        self.draw_text("R-R: Move  |  R-C: Enter Layer  |  P-C: Back  |  P-LC: Reset Bar", 120, 420, (115, 115, 120))

    def _draw_layer_nav(self):
        self.draw_text(f"Bar {self.current_bar} - Select Layer", 120, 80, (200, 200, 210))

        # 레이어 슬롯 + ⊕
        x0, y0 = 100, 120
        slot_w, slot_h, gap = 160, 56, 12
        total = len(self.layers) + 1
        for i in range(total):
            row = i // 4
            col = i % 4
            x = x0 + col * (slot_w + gap)
            y = y0 + row * (slot_h + gap)
            sel = (i == self.layer_cursor)
            pygame.draw.rect(self.screen, (60, 66, 78) if not sel else (80, 110, 170),
                             (x, y, slot_w, slot_h), 0, border_radius=8)
            label = self.layers[i]["name"] if i < len(self.layers) else "⊕  Add Layer"
            self.draw_text(label, x + 12, y + 18, (250, 230, 200) if sel else (170, 170, 170))

        self.draw_text("R-R: Move  |  R-C: Enter/Append  |  P-C: Back  |  P-LC: Delete Layer", 120, 420, (115, 115, 120))

    def _draw_sample_nav(self):
        # 헤더
        self.draw_text(f"Bar {self.current_bar} | Layer {self.current_layer}", 120, 72, (200, 200, 210))

        # 타임라인(그리드: 16th) + 32nd 커서
        x0, y0, W, H = 80, 150, 640, 120
        pygame.draw.rect(self.screen, (40, 46, 56), (x0, y0, W, H), 0, border_radius=8)

        # 16th grid
        step_px = W / GRID_STEPS
        for i in range(GRID_STEPS + 1):
            x = int(x0 + i * step_px)
            col = (70, 76, 90) if i % 4 else (90, 96, 112)  # 4분마다 강조
            pygame.draw.line(self.screen, col, (x, y0), (x, y0 + H), 1)

        # 배치된 샘플들
        samples = self.grid[self.current_bar][self.current_layer]
        for s in samples:
            sx = x0 + int(W * (s["start"] / FINE_STEPS))
            ex = x0 + int(W * ((s["start"] + s["length"]) / FINE_STEPS))
            rect = pygame.Rect(sx + 1, y0 + 16, max(6, ex - sx - 2), H - 32)
            pygame.draw.rect(self.screen, (150, 110, 200), rect, 0, border_radius=6)
            # 미니 헤드 마커
            pygame.draw.rect(self.screen, (230, 210, 250), (sx + 1, y0 + 16, 2, H - 32))

        # 커서(32nd 정밀)
        cx = x0 + int(W * (self.tick / FINE_STEPS))
        pygame.draw.line(self.screen, (255, 210, 120), (cx, y0), (cx, y0 + H), 2)

        # 팔레트/컨트롤
        if self.palette:
            name = self.palette[self.palette_idx]["name"]
            self.draw_text(f"Current Sample: {name}", 120, 292, (170, 170, 170))
        self.draw_text("R-R: Move (16th)  |  P-C + R-R: Fine (32nd)  |  R-C: Place/Edit  |  P-DC: Preview Layer", 
                       80, 420, (115, 115, 120))

    def _draw_sample_adjust(self):
        s = self.selected_sample
        self.draw_text(f"Edit Sample  (Bar {self.current_bar}, Layer {self.current_layer})", 120, 72, (200, 200, 210))

        # 카드 UI
        x0, y0, W, H = 90, 120, 620, 220
        pygame.draw.rect(self.screen, (40, 46, 56), (x0, y0, W, H), 0, border_radius=12)

        # 파라미터 3종: Toggle, Pitch, Gain
        items = ["Melody/Rhythm", "Pitch", "Gain"]
        for i, name in enumerate(items):
            y = y0 + 20 + i * 64
            sel = (getattr(self, "_sa_focus", 0) == i)
            pygame.draw.rect(self.screen, (60, 66, 78) if not sel else (80, 110, 170),
                             (x0 + 20, y, W - 40, 44), 0, border_radius=8)
            self.draw_text(name, x0 + 34, y + 12, (250, 230, 200) if sel else (170, 170, 170))

            if name == "Melody/Rhythm":
                txt = "Melody (Pitch active)" if s and s["melody"] else "Rhythm (Pitch ignored)"
                self.draw_text(txt, x0 + 240, y + 12, (200, 220, 200) if s and s["melody"] else (220, 180, 180))
            elif name == "Pitch":
                val = 0 if not s else s["pitch"]
                self._draw_value_bar(x0 + 240, y + 12, 280, 20, (val + 24) / 48.0,
                                     f"{'+' if val>=0 else ''}{val} semitones")
            elif name == "Gain":
                val = 100 if not s else s["gain"]
                self._draw_value_bar(x0 + 240, y + 12, 280, 20, val / 200.0, f"{val}%")

        self.draw_text("R-R: Move/Adjust  |  R-C: Toggle/Confirm  |  P-C: Back  |  P-DC: Preview  |  P-LC: Reset", 
                       100, 420, (115, 115, 120))

        # 하단 샘플 타임미니맵(선택영역 표시)
        xg, yg, Wg, Hg = 100, 360, 600, 10
        pygame.draw.rect(self.screen, (60, 66, 78), (xg, yg, Wg, Hg), 0, border_radius=5)
        if s:
            sx = xg + int(Wg * (s["start"] / FINE_STEPS))
            ex = xg + int(Wg * ((s["start"] + s["length"]) / FINE_STEPS))
            pygame.draw.rect(self.screen, (255, 210, 120), (sx, yg, max(2, ex - sx), Hg), 0, border_radius=5)

    # --- draw helpers ---
    def _draw_value_bar(self, x, y, w, h, ratio, label):
        ratio = clamp(ratio, 0.0, 1.0)
        pygame.draw.rect(self.screen, (70, 76, 92), (x, y, w, h), 0, border_radius=6)
        pygame.draw.rect(self.screen, (255, 150, 60), (x, y, int(w * ratio), h), 0, border_radius=6)
        self.draw_text(f" {label}", x + w + 10, y - 2, (170, 170, 170))
