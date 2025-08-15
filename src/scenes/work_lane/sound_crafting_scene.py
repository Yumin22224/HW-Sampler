# ============================================
# scenes/work_lane/sound_crafting_scene.py
# ============================================
"""Sound Crafting Scene - 소리 세공"""

from scenes.base_scene import BaseScene
import pygame

class SoundCraftingScene(BaseScene):
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.sample = None
        self.sound_stone = None
        self.current_tool = 0
        self.tools = ["Trim", "Reverse", "Speed", "EQ"]
        self.navigation_mode = "ADJUST"  # ADJUST or NAVIGATE
        self.tool_cursor_position = 0
    
    def enter(self, **kwargs):
        self.sample = kwargs.get("sample")
        # AI 처리 (placeholder)
        self.generate_sound_stone()
    
    def generate_sound_stone(self):
        # TODO: AI 모델로 sound stone 생성
        self.sound_stone = {
            "visual": "placeholder_stone",
            "properties": {},
            "processed_audio": self.sample
        }
    
    def update(self, dt, hw_state):
        # P-C: 모드 전환
        if hw_state.get("PUSH_CLICK"):
            self.navigation_mode = "ADJUST" if self.navigation_mode == "NAVIGATE" else "NAVIGATE"
        
        # R-C: 툴 확정/적용
        if hw_state.get("ROTARY_CLICK"):
            if self.navigation_mode == "ADJUST":
                self.apply_tool()
            else:
                # 다음 씬으로
                self.scene_manager.change_scene("loop_composition",
                                              sound_stone=self.sound_stone)
        
        # R-R: 회전
        if hw_state.get("ROTARY_CW"):
            if self.navigation_mode == "NAVIGATE":
                self.current_tool = (self.current_tool + 1) % len(self.tools)
            else:
                self.adjust_tool_parameter(1)
        elif hw_state.get("ROTARY_CCW"):
            if self.navigation_mode == "NAVIGATE":
                self.current_tool = (self.current_tool - 1) % len(self.tools)
            else:
                self.adjust_tool_parameter(-1)
        
        # P-DC: 미리듣기 토글
        if hw_state.get("PUSH_DOUBLE_CLICK"):
            self.toggle_preview()
    
    def apply_tool(self):
        # 현재 선택된 툴 적용
        tool_name = self.tools[self.current_tool]
        # TODO: 실제 오디오 처리
        print(f"Applying {tool_name} to sound stone")
    
    def adjust_tool_parameter(self, direction):
        # 툴 파라미터 조정
        self.tool_cursor_position += direction * 10
        self.tool_cursor_position = max(0, min(100, self.tool_cursor_position))
    
    def toggle_preview(self):
        # 처리된 소리 미리듣기
        pass
    
    def draw(self):
        self.screen.fill((25, 30, 35))
        
        # 타이틀
        self.draw_text("Sound Crafting", 320, 30, (100, 150, 200))
        
        # Sound Stone 시각화 (왼쪽)
        pygame.draw.rect(self.screen, (80, 100, 120), (50, 100, 250, 250))
        self.draw_text("Sound Stone", 120, 200, (255, 255, 255))
        
        # 툴 선택 영역 (오른쪽)
        for i, tool in enumerate(self.tools):
            y = 120 + i * 60
            color = (255, 200, 100) if i == self.current_tool else (100, 100, 100)
            
            # 툴 배경
            if i == self.current_tool:
                pygame.draw.rect(self.screen, (50, 50, 60), (450, y - 10, 200, 50))
            
            self.draw_text(tool, 500, y, color)
            
            # Adjust 모드일 때 파라미터 바 표시
            if i == self.current_tool and self.navigation_mode == "ADJUST":
                pygame.draw.rect(self.screen, (60, 60, 70), (460, y + 25, 180, 10))
                pygame.draw.rect(self.screen, (255, 150, 50), 
                               (460, y + 25, int(180 * self.tool_cursor_position / 100), 10))
        
        # 모드 표시
        mode_text = f"Mode: {self.navigation_mode}"
        mode_color = (100, 200, 100) if self.navigation_mode == "ADJUST" else (200, 100, 100)
        self.draw_text(mode_text, 350, 380, mode_color)
        
        # 컨트롤 안내
        self.draw_text("P-C: Switch Mode | R-R: Navigate/Adjust | R-C: Apply/Next", 150, 430, (100, 100, 100))
