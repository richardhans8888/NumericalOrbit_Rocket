# simulation/state_manager.py
import pygame
from simulation.world import World

class StateManager:
    def __init__(self):
        self.state = "MENU"
        self.world = World()
        
    def handle_event(self, event):
        if self.state == "MENU":
            # Press space to play
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.state = "SIMULATION"
                self.world.start()
        elif self.state == "SIMULATION":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.state = "PAUSE"
        elif self.state == "PAUSE":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.state = "SIMULATION"

    def update(self, dt):
        if self.state == "SIMULATION":
            self.world.update(dt)
            
    def get_current_state(self):
        return {
            "name": self.state,
            "world": self.world
        }
