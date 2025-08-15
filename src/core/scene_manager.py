# ============================================
# core/scene_manager.py - 씬 관리
# ============================================

from scenes.bridge_scene import BridgeScene
from scenes.work_lane.recording_scene import RecordingScene
from scenes.work_lane.sound_crafting_scene import SoundCraftingScene
from scenes.work_lane.loop_composition_scene import LoopCompositionScene
from scenes.library_lane.library_scene import LibraryScene

class SceneManager:
    def __init__(self, screen, state_manager):
        self.screen = screen
        self.state_manager = state_manager
        self.scenes = {}
        self.current_scene = None
        
        # 씬 등록
        self.register_scenes()
    
    def register_scenes(self):
        self.scenes["bridge"] = BridgeScene(self.screen, self)
        self.scenes["recording"] = RecordingScene(self.screen, self)
        self.scenes["sound_crafting"] = SoundCraftingScene(self.screen, self)
        self.scenes["loop_composition"] = LoopCompositionScene(self.screen, self)
        self.scenes["library"] = LibraryScene(self.screen, self)
    
    def change_scene(self, scene_name, **kwargs):
        if scene_name in self.scenes:
            if self.current_scene:
                self.current_scene.exit()
            
            self.current_scene = self.scenes[scene_name]
            self.current_scene.enter(**kwargs)
    
    def handle_event(self, event):
        if self.current_scene:
            self.current_scene.handle_event(event)
    
    def update(self, dt, hw_state):
        if self.current_scene:
            self.current_scene.update(dt, hw_state)
    
    def draw(self):
        if self.current_scene:
            self.current_scene.draw()
