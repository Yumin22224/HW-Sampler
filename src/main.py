import os, sys
import pygame
from config import WIDTH, HEIGHT, FPS, FULLSCREEN
from inputs import Input

# 콘솔 부팅에서도 잘 뜨도록(안 되면 자동 폴백)
os.environ.setdefault("SDL_AUDIODRIVER", "alsa")     # 오디오(ALSAl)
# os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm") # 필요시 활성화

def create_screen():
    flags = pygame.FULLSCREEN if FULLSCREEN else 0
    try:
        return pygame.display.set_mode((WIDTH, HEIGHT), flags)
    except Exception:
        # 폴백: 윈도우 모드
        return pygame.display.set_mode((WIDTH, HEIGHT))

def main():
    pygame.init()
    screen = create_screen()
    print("SDL video driver =", pygame.display.get_driver())
    pygame.mouse.set_visible(False)
    pygame.display.set_caption("HW-Sampler")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    inp = Input()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 안전장치
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False  # 개발용 종료키

        keys = pygame.key.get_pressed()
        a_pressed = keys[pygame.K_SPACE] or inp.read().get("A", False)

        screen.fill((0,0,0))
        info = [
            "HW-Sampler Starter",
            f"FPS: {clock.get_fps():.0f}",
            "ESC=Quit (dev only)",
            "SPACE=A (keyboard stub)",
            f"A pressed: {a_pressed}"
        ]
        y = 20
        for line in info:
            surf = font.render(line, True, (200,200,200))
            screen.blit(surf, (20, y)); y += 34

        pygame.display.flip()
        clock.tick(FPS)

    inp.cleanup()
    pygame.quit()

if __name__ == "__main__":
    main()