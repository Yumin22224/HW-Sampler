import pygame
from utils.constants import PC, RC, RR_CW, RR_CCW, PDC, PLC, REC
from core.scene_manager import SceneManager
from inputs.hardware_input import HardwareInput

# 씬 import
from scenes.work_lane.recording_scene import RecordingScene
from scenes.work_lane.sound_crafting_scene import SoundCraftingScene
from scenes.work_lane.loop_composition_scene import LoopCompositionScene
from scenes.bridge_scene import BridgeScene
from scenes.library_lane.library_scene import LibraryScene

WIDTH, HEIGHT = 800, 480
FPS = 60

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Deadcat Recorder")

    clock = pygame.time.Clock()
    hw = HardwareInput()

    # 씬 매니저 초기화
    scene_manager = SceneManager(screen)
    scene_manager.register("recording", RecordingScene)
    scene_manager.register("sound_crafting", SoundCraftingScene)
    scene_manager.register("loop_composition", LoopCompositionScene)
    scene_manager.register("bridge", BridgeScene)
    scene_manager.register("library", LibraryScene)

    # 시작 씬은 항상 Pre-record
    scene_manager.change_scene("recording")

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            hw.feed_event(event)

        hw_state = hw.read()
        scene_manager.update(dt, hw_state)
        scene_manager.draw()
        pygame.display.flip()
        hw.post_frame_reset()

    pygame.quit()

if __name__ == "__main__":
    main()
