# simulation/state_manager.py
import pygame
from simulation.world import World
from mission.mission_profile import MissionProfile

class StateManager:
    def __init__(self):
        self.state = "MENU"
        self.world = None
        self.selected_vehicle = "FALCON_9"
        self.selected_orbit = "LEO"
        
    def handle_event(self, event):
        if self.state == "MENU":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.world = World(MissionProfile(self.selected_vehicle, self.selected_orbit))
                self.state = "SIMULATION"
                self.world.start()
        elif self.state == "SIMULATION":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.state = "PAUSE"
            # Time warp controls
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    if self.world.time_warp < 100.0:
                        self.world.time_warp *= 5.0
                elif event.key == pygame.K_LEFT:
                    if self.world.time_warp > 1.0:
                        self.world.time_warp /= 5.0
                        
        elif self.state == "PAUSE":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.state = "SIMULATION"

    def update(self, dt):
        if self.state == "SIMULATION":
            self.world.update(dt)
            
    def get_current_state(self):
        return {
            "name": self.state,
            "world": self.world,
            "menu_data": {
                "vehicle": self.selected_vehicle,
                "orbit": self.selected_orbit
            }
        }
