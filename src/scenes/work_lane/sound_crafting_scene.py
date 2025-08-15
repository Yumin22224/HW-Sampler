# scenes/work_lane/sound_crafting_scene.py
import pygame
from scenes.base_scene import BaseScene
from utils.constants import PC, RC, RR_CW, RR_CCW, PDC

TOOLS = ["Trim", "Reverse", "Speed", "EQ - Low Pass", "EQ - High Pass", "Next"]

class SoundCraftingScene(BaseScene):
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.sample = None
        self.sound_stone = None
        self.mode = "NAVIGATE"            # NAVIGATE | ADJUST
        self.current_tool = 0
        # 파라미터 상태
        self.params = {
            "Trim": {"begin": 0, "end": 100, "cursor": "begin"},   # cursor는 begin/end 토글
            "Reverse": {"on": False},
            "Speed": {"value": 100, "last_confirm": 100},           # %
            "EQ - Low Pass": {"cutoff": 20000, "last_confirm": 20000},
            "EQ - High Pass": {"cutoff": 20, "last_confirm": 20},
        }

    def enter(self, **kwargs):
        self.sample = kwargs.get("sample")
        self.generate_sound_stone()

    def generate_sound_stone(self):
        self.sound_stone = {"visual": "stone", "properties": {}, "processed_audio": self.sample}

    def update(self, dt, hw_state):
        # P-C: 언제나 상위로 (NAVIGATE로) 복귀
        if hw_state.get(PC):
            self.mode = "NAVIGATE"

        # R-R: NAVIGATE에선 툴 이동, ADJUST에선 값 조정
        if hw_state.get(RR_CW):
            if self.mode == "NAVIGATE":
                self.current_tool = (self.current_tool + 1) % len(TOOLS)
            else:
                self._adjust(+1)
        if hw_state.get(RR_CCW):
            if self.mode == "NAVIGATE":
                self.current_tool = (self.current_tool - 1) % len(TOOLS)
            else:
                self._adjust(-1)

        # R-C: NAVIGATE→ADJUST 진입 또는 Reverse 토글/컨펌
        if hw_state.get(RC):
            tool = TOOLS[self.current_tool]
            if self.mode == "NAVIGATE":
                if tool == "Next":
                    self.scene_manager.change_scene("loop_composition", sound_stone=self.sound_stone)
                else:
                    self.mode = "ADJUST"      # 들어가기
            else:
                if tool == "Reverse":
                    self.params["Reverse"]["on"] = not self.params["Reverse"]["on"]
                else:
                    # 컨펌하지만 ADJUST 유지(최근 컨펌값 갱신)
                    if tool == "Trim":
                        # begin/end는 cursor로 이동시키며 조정
                        pass
                    elif tool == "Speed":
                        self.params["Speed"]["last_confirm"] = self.params["Speed"]["value"]
                    elif tool == "EQ - Low Pass":
                        self.params["EQ - Low Pass"]["last_confirm"] = self.params["EQ - Low Pass"]["cutoff"]
                    elif tool == "EQ - High Pass":
                        self.params["EQ - High Pass"]["last_confirm"] = self.params["EQ - High Pass"]["cutoff"]
                # NAVIGATE로 자동 복귀하지 않음

        # P-DC: 프리뷰
        if hw_state.get(PDC):
            self._toggle_preview()

    # ---- 내부 로직 ----
    def _adjust(self, direction):
        tool = TOOLS[self.current_tool]
        if tool == "Trim":
            cur = self.params["Trim"]["cursor"]
            step = 1
            self.params["Trim"][cur] = max(0, min(100, self.params["Trim"][cur] + direction * step))
            # begin>end 방지
            b, e = self.params["Trim"]["begin"], self.params["Trim"]["end"]
            if b > e:
                if cur == "begin": self.params["Trim"]["end"] = b
                else: self.params["Trim"]["begin"] = e
        elif tool == "Speed":
            self.params["Speed"]["value"] = max(50, min(200, self.params["Speed"]["value"] + direction * 2))  # 50~200%
        elif tool == "EQ - Low Pass":
            self.params["EQ - Low Pass"]["cutoff"] = max(200, min(20000, self.params["EQ - Low Pass"]["cutoff"] + direction * 100))
        elif tool == "EQ - High Pass":
            self.params["EQ - High Pass"]["cutoff"] = max(20, min(5000, self.params["EQ - High Pass"]["cutoff"] + direction * 20))
        elif tool == "Reverse":
            # Reverse는 R-C 토글만
            pass

    def _toggle_preview(self):
        print("[SoundCrafting] preview toggle")

    # ---- 렌더 ----
    def draw(self):
        self.screen.fill((25,30,35))
        self.draw_text("Sound Crafting", 320, 24, (100,150,200))
        # 좌측: 스톤
        pygame.draw.rect(self.screen, (80,100,120), (40, 80, 260, 260))
        self.draw_text("Sound Stone", 96, 200, (255,255,255))
        # 우측: 툴 목록 + 파라미터
        y0 = 90
        for i, name in enumerate(TOOLS):
            y = y0 + i * 50
            sel = (i == self.current_tool)
            if sel:
                pygame.draw.rect(self.screen, (50,50,60), (360, y-10, 380, 40))
            self.draw_text(name, 380, y, (255,200,100) if sel else (140,140,140))

            if sel and self.mode == "ADJUST":
                self._draw_param(name, 380, y+20)

        self.draw_text(f"Mode: {self.mode}", 340, 380, (120,200,120) if self.mode=="ADJUST" else (200,120,120))
        self.draw_text("P-C: Back | R-R: Adjust/Move | R-C: Toggle/Confirm | P-DC: Preview", 120, 430, (110,110,110))

    def _draw_param(self, tool, x, y):
        if tool == "Trim":
            b = self.params["Trim"]["begin"]
            e = self.params["Trim"]["end"]
            cur = self.params["Trim"]["cursor"]
            # 바
            pygame.draw.rect(self.screen, (60,60,70), (x, y, 320, 8))
            # begin/end 마커
            bpx = x + int(320 * b / 100)
            epx = x + int(320 * e / 100)
            pygame.draw.circle(self.screen, (255,180,70) if cur=="begin" else (160,160,160), (bpx, y+4), 6)
            pygame.draw.circle(self.screen, (255,180,70) if cur=="end" else (160,160,160), (epx, y+4), 6)
            self.draw_text(f" {b}% ~ {e}%", x+330, y-6, (140,140,140))
        elif tool == "Reverse":
            on = self.params["Reverse"]["on"]
            self.draw_text(f" {'ON' if on else 'OFF'} (R-C toggle)", x+220, y-6, (180,220,180) if on else (180,120,120))
        elif tool == "Speed":
            val = self.params["Speed"]["value"]
            last = self.params["Speed"]["last_confirm"]
            self._draw_bar(x, y, val, show_last=last)
        elif tool == "EQ - Low Pass":
            cut = self.params["EQ - Low Pass"]["cutoff"]
            last = self.params["EQ - Low Pass"]["last_confirm"]
            self._draw_bar(x, y, int(cut/200), label=f"{cut} Hz", show_last=int(last/200))
        elif tool == "EQ - High Pass":
            cut = self.params["EQ - High Pass"]["cutoff"]
            last = self.params["EQ - High Pass"]["last_confirm"]
            self._draw_bar(x, y, int((cut-20)/20), label=f"{cut} Hz", show_last=int((last-20)/20))

    def _draw_bar(self, x, y, value_0to100, label=None, show_last=None):
        # value_0to100: 0~100
        pygame.draw.rect(self.screen, (60,60,70), (x, y, 320, 8))
        pygame.draw.rect(self.screen, (255,150,50), (x, y, int(320*value_0to100/100), 8))
        if show_last is not None:
            # 최근 컨펌 값(얇은 선)
            last_x = x + int(320*show_last/100)
            pygame.draw.line(self.screen, (255,220,160), (last_x, y-2), (last_x, y+10), 1)
        if label:
            self.draw_text(f" {label}", x+330, y-6, (140,140,140))
