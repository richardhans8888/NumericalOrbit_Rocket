# rendering/renderer.py
import pygame
import config
from rendering.sprites import draw_rocket, draw_debris

class Renderer:
    def __init__(self, surface, camera):
        self.surface = surface
        self.camera = camera
        self.font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 48)
        
    def render(self, state_data):
        self.surface.fill(config.BG_COLOR)
        
        state_name = state_data["name"]
        world = state_data["world"]
        
        if state_name == "MENU":
            self._render_world_bg(world)
            self._draw_centered_rect_text("Press SPACE to Launch", config.SCREEN_WIDTH//2, config.SCREEN_HEIGHT//2, self.large_font)
        else:
            self._render_world(world)
            if state_name == "PAUSE":
                self._draw_centered_rect_text("PAUSED - Press P to Resume", config.SCREEN_WIDTH//2, config.SCREEN_HEIGHT//2, self.large_font)

    def _render_world_bg(self, world):
        """ Render just the background and rocket without updates for MENU state. """
        self._render_environment()
        rx, ry = self.camera.world_to_screen(world.rocket.x, world.rocket.y)
        remaining_stages = len(world.rocket.stages) - world.rocket.current_stage_index
        if remaining_stages > 0:
            draw_rocket(self.surface, rx, ry, False, remaining_stages)

    def _render_world(self, world):
        self.camera.update(world.rocket.y)
        
        # Ground
        self._render_environment()
        
        # Debris
        for d in world.debris:
            dx, dy = self.camera.world_to_screen(d["x"], d["y"])
            draw_debris(self.surface, dx, dy)
            
        # Main Rocket
        rx, ry = self.camera.world_to_screen(world.rocket.x, world.rocket.y)
        active = False
        if world.rocket.current_stage_index < len(world.rocket.stages):
            active = world.rocket.stages[world.rocket.current_stage_index].active
            
        remaining_stages = len(world.rocket.stages) - world.rocket.current_stage_index
        if remaining_stages > 0:
            draw_rocket(self.surface, rx, ry, active, remaining_stages)
            
        self._draw_ui(world)

    def _render_environment(self):
        ground_x, ground_y = self.camera.world_to_screen(0, 0)
        pygame.draw.rect(self.surface, (50, 150, 50), (0, ground_y, config.SCREEN_WIDTH, config.SCREEN_HEIGHT - ground_y))

    def _draw_ui(self, world):
        alt = f"Altitude: {world.rocket.y:,.0f} m"
        vel = f"Velocity: {world.rocket.vy:,.0f} m/s"
        mass = f"Mass: {world.rocket.get_total_mass():,.0f} kg"
        time = f"Time: {world.time_elapsed:.1f} s"
        
        self._draw_text(time, 10, 10)
        self._draw_text(alt, 10, 30)
        self._draw_text(vel, 10, 50)
        self._draw_text(mass, 10, 70)
        
        if world.rocket.current_stage_index < len(world.rocket.stages):
            st = world.rocket.stages[world.rocket.current_stage_index]
            self._draw_text(f"{st.name} Fuel: {st.fuel_system.fuel:,.0f} kg", 10, 100)
            
    def _draw_text(self, text, x, y, color=config.TEXT_COLOR):
        surface = self.font.render(text, True, color)
        self.surface.blit(surface, (x, y))
        
    def _draw_centered_rect_text(self, text, x, y, font, color=config.TEXT_COLOR):
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        rect.center = (x, y)
        self.surface.blit(surface, rect)
