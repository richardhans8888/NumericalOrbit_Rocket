# rocket/rocket.py
import math
from physics.thrust import compute_thrust_force

class Rocket:
    def __init__(self):
        self.stages = []
        self.current_stage_index = 0
        
        # Physics state
        self.x = 0.0
        self.y = 0.0 # From earth surface
        self.vx = 0.0
        self.vy = 0.0
        self.pitch_angle = math.pi / 2.0 # PI/2 radians is straight up
        
    def add_stage(self, stage):
        """Adds a stage. Bottom stage should be added first."""
        self.stages.append(stage)
        
    def activate_next_stage(self):
        if self.current_stage_index < len(self.stages):
            self.stages[self.current_stage_index].active = True
            
    def get_total_mass(self):
        return sum(stage.get_mass() for stage in self.stages if not stage.detached)
        
    def update_systems(self, dt):
        """
        Updates internal rocket systems like fuel.
        Returns a tuple: (event_name, thrust_magnitude)
        """
        thrust_magnitude = 0.0
        event = None
        
        if self.current_stage_index < len(self.stages):
            current_stage = self.stages[self.current_stage_index]
            
            if current_stage.active:
                thrust_magnitude = current_stage.update(dt)
                
                # Check for stage separation logic (fuel empty)
                if current_stage.fuel_system.empty:
                    current_stage.active = False
                    event = "EVENT_SEPARATION"
                    thrust_magnitude = 0.0
        else:
            # All stages depleted
            pass
            
        return event, thrust_magnitude

    def get_thrust_force(self, thrust_magnitude):
        if thrust_magnitude <= 0.0:
            return 0.0, 0.0
        return compute_thrust_force(thrust_magnitude, self.pitch_angle)
        
    def separate_current_stage(self):
        """
        Detaches the current stage, activates the next, and returns the detached stage object.
        """
        if self.current_stage_index < len(self.stages):
            separated_stage = self.stages[self.current_stage_index]
            separated_stage.detached = True
            
            self.current_stage_index += 1
            self.activate_next_stage()
            
            return separated_stage
        return None
