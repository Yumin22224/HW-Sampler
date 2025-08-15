# main.py
import os, sys, pygame
from core.scene_manager import SceneManager
from inputs.hardware_input import HardwareInput

# 씬들
from scenes.work_lane.recording_scene import RecordingScene
from scenes.work_lane.sound_crafting_scene import SoundCraftingScene
from scenes.work_lane.loop_composition_scene import LoopCompositionScene
from scenes.bridge_scene import BridgeScene
from scenes.library_lane.library_scene import LibraryScene

WIDTH, HEIGHT = 800, 480
FPS = 60

def main():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Deadcat Recorder")

    clock = pygame.time.Clock()
    hw = HardwareInput()

    sm = SceneManager(screen)  # ← state_manager 인자 불필요
    sm.register("recording", RecordingScene)
    sm.register("sound_crafting", SoundCraftingScene)
    sm.register("loop_composition", LoopCompositionScene)
    sm.register("bridge", BridgeScene)
    sm.register("library", LibraryScene)

    # 항상 Pre-record부터
    sm.change_scene("recording")

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            hw.feed_event(event)

        hw_state = hw.read()
        sm.update(dt, hw_state)
        sm.draw()
        pygame.display.flip()
        hw.post_frame_reset()

    hw.cleanup()
    pygame.quit()

if __name__ == "__main__":
    main()
