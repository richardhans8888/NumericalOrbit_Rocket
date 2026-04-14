# rendering/renderer.py
import pygame
import config
import math
from physics.constants import EARTH_RADIUS
from rendering.sprites import draw_rocket, draw_debris
from mission.telemetry import format_time
from mission.flight_phases import FlightPhase, PHASE_NAMES

class Renderer:
    def __init__(self, surface, camera):
        self.surface = surface
        self.camera = camera
        self.font = pygame.font.SysFont("Courier", 14)
        self.large_font = pygame.font.SysFont("Courier", 28)
        
    def render(self, state_data):
        self.surface.fill((0, 0, 5))
        
        state_name = state_data["name"]
        
        if state_name == "MENU":
            self._render_menu(state_data["menu_data"])
        else:
            world = state_data["world"]
            self.camera.update(world.rocket.x, world.rocket.y, world.rocket.get_altitude())
            self._render_background(world)
            self._render_earth()
            self._render_world(world)
            
            if state_name == "PAUSE":
                self._draw_centered_text("PAUSED", config.SCREEN_WIDTH//2, config.SCREEN_HEIGHT//2, self.large_font, (255, 200, 0))

    def _render_menu(self, menu_data):
        self._draw_centered_text("MISSION CONTROL", config.SCREEN_WIDTH//2, config.SCREEN_HEIGHT//2 - 60, self.large_font, (200,200,200))
        self._draw_centered_text(f"Vehicle: {menu_data['vehicle']}", config.SCREEN_WIDTH//2, config.SCREEN_HEIGHT//2 - 20, self.font, (0, 255, 0))
        self._draw_centered_text(f"Orbit Target: {menu_data['orbit']}", config.SCREEN_WIDTH//2, config.SCREEN_HEIGHT//2, self.font, (0, 255, 0))
        self._draw_centered_text("[PRESS ENTER TO LAUNCH]", config.SCREEN_WIDTH//2, config.SCREEN_HEIGHT//2 + 50, self.font, (255, 255, 0))

    def _render_background(self, world):
        alt = world.rocket.get_altitude()
        ratio = max(0.0, 1.0 - (alt / 100000.0))
        bg_col = (int(10 * ratio), int(30 * ratio), int(80 * ratio))
        self.surface.fill(bg_col)
        
    def _render_earth(self):
        cx, cy = self.camera.world_to_screen(0, 0)
        r = self.camera.get_screen_radius(EARTH_RADIUS)
        
        if r < 80000:
            pygame.draw.circle(self.surface, (10, 40, 15), (cx, cy), r)
            halo_r = self.camera.get_screen_radius(EARTH_RADIUS + 100000)
            pygame.draw.circle(self.surface, (30, 80, 150), (cx, cy), halo_r, width=max(1, int(100000/self.camera.zoom)))
        else:
            # Fallback for extreme zoom to avoid SDL limit crashes
            # Compute intersection with the view relative to the rocket
            surface_y = EARTH_RADIUS
            sx, sy = self.camera.world_to_screen(0, surface_y)
            # A wide rectangle at sy
            pygame.draw.rect(self.surface, (10, 40, 15), (0, sy, config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def _render_world(self, world):
        # Draw Debris
        for d in world.debris:
            dx, dy = self.camera.world_to_screen(d["x"], d["y"])
            draw_debris(self.surface, dx, dy)
            
        # Draw Trajectory Prediction
        rx, ry = self.camera.world_to_screen(world.rocket.x, world.rocket.y)
        tx, ty = self.camera.world_to_screen(world.rocket.x + world.rocket.vx * 100, world.rocket.y + world.rocket.vy * 100)
        pygame.draw.line(self.surface, (0, 255, 100), (rx, ry), (tx, ty), 1)
            
        active = False
        if world.rocket.current_stage_index < len(world.rocket.stages):
            active = world.rocket.stages[world.rocket.current_stage_index].active
            
        remaining_stages = len(world.rocket.stages) - world.rocket.current_stage_index
        if remaining_stages > 0:
            deg = math.degrees(world.rocket.pitch_angle) - 90.0 # Point up standard
            draw_rocket(self.surface, rx, ry, active, remaining_stages, deg)
            
        self._draw_ui(world)

    def _draw_ui(self, world):
        alt = world.rocket.get_altitude()
        vel = world.rocket.get_velocity_mag()
        mass = world.rocket.get_total_mass()
        
        info = [
            f"MISSION TIME: {format_time(world.time_elapsed)}",
            f"PHASE: {PHASE_NAMES.get(world.phase, 'UNKNOWN')}",
            f"ALTITUDE: {alt/1000.0:.2f} km",
            f"VELOCITY: {vel/1000.0:.2f} km/s",
            f"MASS:     {mass:,.0f} kg",
            f"TIME WARP:{world.time_warp}x"
        ]
        
        y_pos = 20
        for line in info:
            self._draw_text(line, 20, y_pos, (0, 255, 0))
            y_pos += 20
            
        if world.rocket.current_stage_index < len(world.rocket.stages):
            st = world.rocket.stages[world.rocket.current_stage_index]
            self._draw_text(f"STAGE: {st.name}", 20, config.SCREEN_HEIGHT - 60, (200, 200, 200))
            self._draw_text(f"PROP:  {st.fuel_system.fuel:,.0f} kg", 20, config.SCREEN_HEIGHT - 40, (200, 200, 200))
            
    def _draw_text(self, text, x, y, color):
        s = self.font.render(text, True, color)
        self.surface.blit(s, (x, y))
        
    def _draw_centered_text(self, text, x, y, font, color):
        s = font.render(text, True, color)
        r = s.get_rect(center=(x, y))
        self.surface.blit(s, r)
