import pygame
import sys
import config
from simulation.state_manager import StateManager
from rendering.renderer import Renderer
from rendering.camera import Camera

def main():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption(config.TITLE)
    clock = pygame.time.Clock()

    camera = Camera(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    renderer = Renderer(screen, camera)
    state_manager = StateManager()

    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000.0  # Real time delta

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            state_manager.handle_event(event)
        
        state_manager.update(config.SIM_TIME_STEP)

        # Render
        renderer.render(state_manager.get_current_state())

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
