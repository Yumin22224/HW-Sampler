# ============================================
# scenes/library_lane/library_scene.py
# ============================================
"""Library Scene - 사냥꾼의 창고"""

import pygame
from scenes.base_scene import BaseScene
from utils.constants import PC, RC, RR_CW, RR_CCW, PDC

class LibraryScene(BaseScene):
    def __init__(self, screen, scene_manager):
        super().__init__(screen, scene_manager)
        self.tail_packs = []  # 저장된 꼬리들
        self.focus_distance = 50  # 망원경 초점 거리
        self.selected_pack = 0
        self.view_mode = "TELESCOPE"  # TELESCOPE or DETAIL
    
    def enter(self, **kwargs):
        # 라이브러리 로드
        self.load_library()
        self.focus_distance = 50
    
    def load_library(self):
        # TODO: 실제 파일에서 tail_packs 로드
        # 더미 데이터
        self.tail_packs = [
            {"name": "Mystic Tail #1", "date": "2024-01-15", "layers": 3},
            {"name": "Shadow Tail #2", "date": "2024-01-14", "layers": 2},
        ]
    
    def update(self, dt, hw_state):
        # P-C: 뒤로 (Bridge로)
        if hw_state.get(PC):
            self.scene_manager.change_scene("bridge")
        
        # R-R: 망원경 초점 조절
        if hw_state.get(RR_CW):
            self.focus_distance = min(100, self.focus_distance + 5)
            self.update_view()
        elif hw_state.get(RR_CCW):
            self.focus_distance = max(0, self.focus_distance - 5)
            self.update_view()
        
        # R-C: 선택/훔치기
        if hw_state.get(RC):
            if self.view_mode == "TELESCOPE":
                self.view_mode = "DETAIL"
            else:
                self.steal_tail_pack()
        
        # P-DC: 미리듣기
        if hw_state.get(PDC):
            self.preview_pack()
    
    def update_view(self):
        # 초점 거리에 따라 다른 콘텐츠 표시
        # 멀리: 오래된 꼬리들
        # 가까이: 최근 꼬리들
        pass
    
    def steal_tail_pack(self):
        # 꼬리 훔치기 (Export)
        if self.tail_packs and self.selected_pack < len(self.tail_packs):
            pack = self.tail_packs[self.selected_pack]
            # TODO: 실제 export 로직
            print(f"Stealing {pack['name']}...")
            # 훔치기 애니메이션
            self.show_steal_animation()
    
    def preview_pack(self):
        # 선택된 팩 미리듣기
        pass
    
    def show_steal_animation(self):
        # TODO: 훔치기 애니메이션
        pass
    
    def draw(self):
        self.screen.fill((15, 15, 20))
        
        if self.view_mode == "TELESCOPE":
            self.draw_telescope_view()
        else:
            self.draw_detail_view()
    
    def draw_telescope_view(self):
        # 망원경 뷰
        self.draw_text("Hunter's Warehouse", 280, 30, (150, 100, 200))
        
        # 망원경 프레임 (원형)
        pygame.draw.circle(self.screen, (60, 60, 70), (400, 240), 180, 3)
        
        # 초점 표시
        focus_text = f"Focus: {self.focus_distance}m"
        self.draw_text(focus_text, 340, 80, (100, 100, 100))
        
        # 꼬리들 표시 (거리에 따라)
        visible_packs = self.get_visible_packs()
        for i, pack in enumerate(visible_packs[:5]):
            y = 150 + i * 40
            color = (200, 150, 100) if i == self.selected_pack else (100, 100, 100)
            self.draw_text(pack["name"], 320, y, color)
        
        # 컨트롤
        self.draw_text("R-R: Focus | R-C: Select | P-C: Back", 220, 430, (80, 80, 80))
    
    def draw_detail_view(self):
        # 상세 뷰
        if self.selected_pack < len(self.tail_packs):
            pack = self.tail_packs[self.selected_pack]
            
            # 꼬리 상세 정보
            self.draw_text(pack["name"], 300, 100, (255, 200, 100))
            self.draw_text(f"Created: {pack['date']}", 300, 140, (150, 150, 150))
            self.draw_text(f"Layers: {pack['layers']}", 300, 180, (150, 150, 150))
            
            # 꼬리 시각화
            self.draw_tail_visualization(pack)
            
            # 컨트롤
            self.draw_text("R-C: Steal (Export) | P-DC: Preview | P-C: Back", 200, 430, (80, 80, 80))
    
    def draw_tail_visualization(self, pack):
        # 꼬리 모양 시각화
        # TODO: 실제 꼬리 데이터 기반 시각화
        pygame.draw.rect(self.screen, (100, 150, 200), (250, 250, 300, 100))
        self.draw_text("Tail Visualization", 350, 290, (255, 255, 255))
    
    def get_visible_packs(self):
        # 초점 거리에 따라 보이는 팩 필터링
        # 가까울수록 최신, 멀수록 오래된 것
        return self.tail_packs