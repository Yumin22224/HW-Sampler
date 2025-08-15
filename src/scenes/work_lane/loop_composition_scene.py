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
        self.loop_focus = 0          # 0: Loop / 1:BPM / 2:Key / 3:Bars / 4:Next
        self.loop_adj_submode = "FOCUS"  # "FOCUS" | "ADJUST"
        self.current_bar = 0
        self.layer_cursor = 0        # 레이어 선택(⊕ 포함)
        self.current_layer = 0       # 실제 편집 타겟(샘플 작업 시)
        self.tick = 0                # Sample Nav 커서 (0..FINE_STEPS-1)
        self.selected_sample = None  # Sample Adjust 타깃
        self.sa_submode = "FOCUS"   # "FOCUS" | "ADJUST" for Sample Adjust
        self._sa_focus_idx = 0      # index within focusable list [Toggle,(Pitch),Gain]

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
        # 포커스 항목 개수
        items = 5  # Loop, BPM, Key, Bars, Next

        if self.loop_adj_submode == "FOCUS":
            # 포커스 링 이동
            if hw.get(RR_CW):  self.loop_focus = (self.loop_focus + 1) % items
            if hw.get(RR_CCW): self.loop_focus = (self.loop_focus - 1) % items

            if hw.get(RC):
                if self.loop_focus == 0:
                    # 중앙 Loop 선택 → Bar Nav 진입
                    self.mode = "BAR_NAV"
                elif self.loop_focus in (1, 2, 3):
                    # BPM/Key/Bars 조정 모드로 진입 (값 즉시 변경 X)
                    self.loop_adj_submode = "ADJUST"
                elif self.loop_focus == 4:
                    # Next → Bridge
                    self.scene_manager.change_scene(
                        "bridge",
                        from_scene="loop_composition",
                        tail_pack=self._export_tail_pack()
                    )

            # 최상위라 P-C는 무시
            if hw.get(PC):
                pass

        else:  # ADJUST
            # 값 조정
            if hw.get(RR_CW) or hw.get(RR_CCW):
                d = 1 if hw.get(RR_CW) else -1
                if self.loop_focus == 1:       # BPM
                    self.bpm = clamp(self.bpm + d, 40, 220)
                elif self.loop_focus == 2:     # Key
                    self.key_idx = (self.key_idx + d) % len(KEYS)
                elif self.loop_focus == 3:     # Bars
                    old = self.bars
                    self.bars = clamp(self.bars + d, 1, 16)
                    if self.bars != old:
                        self._ensure_bars(self.bars)

            # 컨펌 → FOCUS 복귀
            if hw.get(RC):
                self.loop_adj_submode = "FOCUS"

            # 취소(원복)은 요구에 없어서 P-C는 무시 (필요시 여기서 처리)


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
    def _sa_focusable_list(self):
        """
        Sample Adjust 화면에서 포커스 가능한 항목 리스트를 반환.
        0: Toggle(Melody/Rhythm), 1: Pitch, 2: Gain
        Melody=False(=Rhythm)이면 Pitch(1)를 제외한다.
        """
        s = self.selected_sample
        if s is None:
            return [0, 2]  # 방어값
        return [0, 2] if not s.get("melody", True) else [0, 1, 2]

    def _update_sample_adjust(self, hw):
        s = self.selected_sample
        if s is None:
            self.mode = "SAMPLE_NAV"
            return

        # 현재 포커스 가능한 항목 계산 (Melody=False면 Pitch 제외)
        flist = self._sa_focusable_list()        # e.g., [0,1,2] or [0,2]
        if self._sa_focus_idx >= len(flist):
            self._sa_focus_idx = max(0, len(flist) - 1)
        cur = flist[self._sa_focus_idx]          # 0:Toggle, 1:Pitch, 2:Gain

        # --- P-C: Pitch 조정 시 크로매틱 모드(콤보) / 실패 시 Back ---
        if hw.get(PC):
            self._pc_combo_started = True
            self._pc_combo_deadline = pygame.time.get_ticks() + PC_COMBO_MS
            # 콤보 실패 시 Back은 상위 update()의 만료 처리에서 수행

        # --- R-R: FOCUS에선 항목 이동, ADJUST에선 값 변경 ---
        if hw.get(RR_CW) or hw.get(RR_CCW):
            d = 1 if hw.get(RR_CW) else -1

            if self.sa_submode == "FOCUS":
                # 포커스 이동 (flist 내부 인덱스를 회전)
                self._sa_focus_idx = (self._sa_focus_idx + d) % len(flist)

            else:  # ADJUST
                if cur == 1:  # Pitch
                    if not s.get("melody", True):
                        # Melody OFF이면 Pitch는 조정 대상이 아님 → FOCUS 복귀
                        self.sa_submode = "FOCUS"
                    else:
                        # Melody ON: 기본은 스케일 스텝, P-C 콤보면 크로매틱
                        if self._pc_combo_started:
                            s["pitch"] = clamp(s["pitch"] + d, -24, 24)
                            self._pc_combo_started = False  # 콤보 소비 → Back 취소
                        else:
                            s["pitch"] = self._pitch_step_in_scale(s["pitch"], d)

                elif cur == 2:  # Gain
                    s["gain"] = clamp(s["gain"] + d * 2, 0, 200)
                # cur == 0(Toggle)은 ADJUST 진입하지 않음

        # --- R-C: FOCUS→ADJUST 진입 or Toggle / ADJUST→Confirm ---
        if hw.get(RC):
            if self.sa_submode == "FOCUS":
                if cur == 0:
                    # Melody/Rhythm 토글
                    s["melody"] = not s["melody"]
                    # Melody가 OFF가 되면 Pitch는 포커스 대상에서 제외되므로 보정
                    if not s["melody"]:
                        flist = self._sa_focusable_list()
                        if 1 not in flist and cur == 1:
                            # (이론상 cur는 0이라 여기 안 걸리지만 방어)
                            pass
                        # 만약 Pitch를 보고 있었다면 Gain으로 이동
                        if self._sa_focus_idx >= len(flist):
                            self._sa_focus_idx = len(flist) - 1
                    # 토글은 여기서 끝(ADJUST 진입 없음)
                elif cur in (1, 2):
                    # Pitch/Gain 조정 시작
                    # (값은 R-R로 변경, Confirm 후에도 SAMPLE_ADJUST에 머무름)
                    self.sa_submode = "ADJUST"
            else:
                # ADJUST → Confirm 후 FOCUS로 복귀 (값은 이미 반영됨)
                self.sa_submode = "FOCUS"

        # --- P-DC: 샘플 프리뷰 ---
        if hw.get(PDC):
            self._preview_sample(s)

        # --- P-LC: 리셋 ---
        if hw.get(PLC):
            s["pitch"] = 0
            s["gain"] = 100
            s["melody"] = True
            # 포커스 가능한 항목 복구
            self.sa_submode = "FOCUS"
            self._sa_focus_idx = 0


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
        """
        Loop Adjust Mode 화면 그리기
        - 중앙 루프 미니맵이 실제 포커스 대상(Loop)
        - 상단 칩: BPM / Key / Bars / Next
        - ADJUST 서브모드일 때 칩에 상태 반영
        """
        # 색상 팔레트
        col_panel      = (50, 56, 68)
        col_grid_light = (90, 98, 112)
        col_chip_sel   = (60, 66, 78)
        col_chip_idle  = (36, 40, 48)
        col_focus      = (255, 200, 120)
        col_text_sel   = (255, 200, 120)
        col_text_idle  = (170, 170, 170)
        col_text_dim   = (115, 115, 120)

        # --- 중앙 루프 미니맵(Bar 분절 표시) ---
        x0, y0, W, H = 100, 120, 600, 100
        sel_loop = (self.loop_focus == 0)

        # 패널
        pygame.draw.rect(self.screen, col_panel, (x0, y0, W, H), 0, border_radius=12)

        # Bar 분절 라인 (루프 전체가 이미 바들로 분절돼 보이는 상태)
        if self.bars > 0:
            for b in range(self.bars + 1):
                x = x0 + int(W * b / self.bars)
                pygame.draw.line(self.screen, col_grid_light, (x, y0), (x, y0 + H), 1)

        # 포커스 링(Loop 선택 중일 때만)
        if sel_loop:
            pygame.draw.rect(self.screen, col_focus, (x0 - 3, y0 - 3, W + 6, H + 6), 2, border_radius=14)

        # 캡션
        self.draw_text("Loop (Drill with R-C)", x0 + 10, y0 - 24, (200, 200, 210))

        # --- 상단 칩: BPM / Key / Bars / Next (Loop는 중앙이므로 칩에서 제외) ---
        chips = ["BPM", "Key", "Bars", "Next"]
        values = [str(self.bpm), KEYS[self.key_idx], str(self.bars), ""]
        x = 110
        for i, name in enumerate(chips):
            idx = i + 1                      # Loop=0, 칩 인덱스는 1..4
            sel = (self.loop_focus == idx)
            rect = pygame.Rect(x, 60, 150, 36)

            # 선택/비선택 배경
            pygame.draw.rect(self.screen, col_chip_sel if sel else col_chip_idle, rect, 0, border_radius=8)

            # 라벨(ADJUST 상태 반영)
            label = name if name == "Next" else f"{name}: {values[i]}"
            if sel and self.loop_adj_submode == "ADJUST" and name != "Next":
                label += "  (Adjusting)"
            self.draw_text(label, rect.x + 10, rect.y + 8, col_text_sel if sel else col_text_idle)

            x += 160  # 칩 간 간격

        # --- 힌트 ---
        if self.loop_adj_submode == "FOCUS":
            hint = "R-R: Move focus  |  R-C: Drill/Adjust  |  P-DC: Preview"
        else:  # ADJUST
            hint = "R-R: Change value  |  R-C: Confirm (return to FOCUS)"
        self.draw_text(hint, 140, 420, col_text_dim)


    def _draw_bar_nav(self):
        self.draw_text("Select Bar", 120, 80, (200, 200, 210))

        x0, y0, W, H = 100, 120, 600, 120
        pygame.draw.rect(self.screen, (40, 46, 56), (x0, y0, W, H), border_radius=10)

        # Bar들을 가로로 배치하되, 각 카드 내부는 레이어를 세로 스택으로 미니맵 표시
        for b in range(self.bars):
            # 각 Bar의 카드 사각형
            bw = int(W / self.bars) - 6
            bx = x0 + 3 + b * (bw + 6)
            by = y0 + 8
            sel = (b == self.current_bar)
            pygame.draw.rect(self.screen, (80, 110, 170) if sel else (60, 66, 78),
                            (bx, by, bw, H - 16), 0, border_radius=8)
            self.draw_text(f"Bar {b}", bx + 8, by + 6, (250, 230, 200) if sel else (170, 170, 170))

            # 카드 내부: 레이어들을 세로 스택(행)으로 나열
            layers_here = self.grid[b]
            L = max(1, len(self.layers))
            row_h = (H - 40) // L          # 카드 내부 높이를 레이어 수로 나눔
            inner_x = bx + 8
            inner_y = by + 24
            inner_w = bw - 16

            for li in range(L):
                ly = inner_y + li * row_h
                # 해당 레이어에 샘플이 있으면 밝게, 없으면 어둡게
                has_any = len(layers_here[li]) > 0
                pygame.draw.rect(self.screen, (150, 110, 200) if has_any else (90, 96, 112),
                                (inner_x, ly + 4, inner_w, row_h - 8), 0, border_radius=4)

        self.draw_text("R-R: Move  |  R-C: Enter Layer  |  P-C: Back  |  P-LC: Reset Bar",
                    120, 420, (115, 115, 120))


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
        self.draw_text(f"Edit Sample  (Bar {self.current_bar}, Layer {self.current_layer})",
                    120, 72, (200, 200, 210))

        # 카드 UI
        x0, y0, W, H = 90, 120, 620, 220
        pygame.draw.rect(self.screen, (40, 46, 56), (x0, y0, W, H), 0, border_radius=12)

        # 포커스 가능한 항목과 현재 항목
        flist = self._sa_focusable_list()     # [0,1,2] or [0,2]
        cur = flist[self._sa_focus_idx]
        names = {0: "Melody/Rhythm", 1: "Pitch", 2: "Gain"}

        # 세 줄 고정 배치(비활성화/선택/조정 상태 반영)
        rows = [0, 1, 2]
        for row_i, item_id in enumerate(rows):
            y = y0 + 20 + row_i * 64
            selectable = (item_id in flist)
            selected   = (item_id == cur)
            adjusting  = selected and self.sa_submode == "ADJUST" and item_id in (1, 2)

            base_col = (60, 66, 78)
            sel_col  = (80, 110, 170)
            dis_col  = (52, 56, 64)

            # 배경
            bg = dis_col if not selectable else (sel_col if selected else base_col)
            pygame.draw.rect(self.screen, bg, (x0 + 20, y, W - 40, 44), 0, border_radius=8)

            # 라벨
            label_col = (140, 140, 140) if not selectable else ((250, 230, 200) if selected else (170, 170, 170))
            label = names[item_id]
            if adjusting:
                label += "  (Adjusting)"
            # Melody 상태 텍스트
            if item_id == 0:
                txt = "Melody (Pitch active)" if s and s.get("melody", True) else "Rhythm (Pitch disabled)"
                self.draw_text(label, x0 + 34, y + 12, label_col)
                self.draw_text(txt,   x0 + 280, y + 12,
                            (200, 220, 200) if s and s.get("melody", True) else (220, 180, 180))
            elif item_id == 1:  # Pitch
                self.draw_text(label, x0 + 34, y + 12, label_col)
                if selectable:
                    val = 0 if not s else s.get("pitch", 0)
                    self._draw_value_bar(x0 + 240, y + 12, 280, 20, (val + 24) / 48.0,
                                        f"{'+' if val>=0 else ''}{val} semitones")
                else:
                    self.draw_text(" — (disabled in Rhythm)", x0 + 240, y + 12, (130, 130, 130))
            elif item_id == 2:  # Gain
                self.draw_text(label, x0 + 34, y + 12, label_col)
                val = 100 if not s else s.get("gain", 100)
                self._draw_value_bar(x0 + 240, y + 12, 280, 20, val / 200.0, f"{val}%")

        # 힌트
        if self.sa_submode == "FOCUS":
            hint = "R-R: Move focus  |  R-C: Toggle/Enter Adjust  |  P-C: Back(hold) / Pitch Chromatic(mod)"
        else:
            hint = "R-R: Change value  |  R-C: Confirm (return to FOCUS)  |  P-C: Chromatic(mod, Pitch only)"
        self.draw_text(hint, 100, 420, (115, 115, 120))

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


    # --- Tail Pack Export ---
    def _export_tail_pack(self):
        """Bridge로 넘길 TailPack 생성"""
        return {
            "bpm": self.bpm,
            "key": KEYS[self.key_idx],
            "bars": self.bars,
            "layers": len(self.layers),
            "grid": [
                [
                    [
                        {
                            "start": s["start"],
                            "length": s["length"],
                            "melody": s["melody"],
                            "pitch": s["pitch"],
                            "gain": s["gain"],
                            "tpl_name": (s["tpl"]["name"] if s.get("tpl") else None),
                        }
                        for s in self.grid[b][l]
                    ]
                    for l in range(len(self.layers))
                ]
                for b in range(self.bars)
            ],
        }
