# rocket/rocket.py
import math
from physics.thrust import compute_thrust_force
from physics.constants import EARTH_RADIUS
from rocket.stage import Stage

class Rocket:
    def __init__(self, vehicle_data):
        self.stages = []
        self.current_stage_index = 0
        self.vehicle_data = vehicle_data
        
        # Load stages
        for s in vehicle_data["stages"]:
            burn_rate = s["propellant_mass"] / s["burn_time"] if s["burn_time"] > 0 else 0
            self.stages.append(Stage(
                name=s["name"],
                dry_mass=s["dry_mass"],
                fuel_mass=s["propellant_mass"],
                thrust_sl=s["thrust_sl"],
                thrust_vac=s["thrust_vac"],
                burn_rate=burn_rate
            ))
            
        self.fairing_mass = vehicle_data.get("fairing", {}).get("mass", 0)
        self.fairing_attached = True
        
        self.cross_sectional_area = vehicle_data.get("cross_sectional_area", 10.0)
        self.drag_coefficient = vehicle_data.get("drag_coefficient", 0.4)
        
        # True Earth-centric coordinates. Rocket starts at surface of Earth.
        self.x = 0.0
        self.y = EARTH_RADIUS
        
        self.vx = 0.0
        self.vy = 0.0
        
        self.pitch_angle = math.pi / 2.0 # Pointing strictly UP (positive Y)
        
    def get_altitude(self):
        distance = math.sqrt(self.x**2 + self.y**2)
        return distance - EARTH_RADIUS
        
    def get_velocity_mag(self):
        return math.sqrt(self.vx**2 + self.vy**2)

    def get_total_mass(self):
        mass = sum(stage.get_mass() for stage in self.stages if not stage.detached)
        if self.fairing_attached:
            mass += self.fairing_mass
        return mass
        
    def activate_next_stage(self):
        if self.current_stage_index < len(self.stages):
            self.stages[self.current_stage_index].active = True
            
    def update_systems(self, dt):
        thrust_magnitude = 0.0
        event = None
        
        if self.current_stage_index < len(self.stages):
            current_stage = self.stages[self.current_stage_index]
            
            if current_stage.active:
                alt = self.get_altitude()
                # Rough engine vacuum transition interpolation
                if alt > 50000:
                    t_power = current_stage.thrust_vac
                else:
                    ratio = alt / 50000.0
                    t_power = current_stage.thrust_sl + (current_stage.thrust_vac - current_stage.thrust_sl) * ratio
                    
                thrust_magnitude = current_stage.update(t_power, dt)
                
                if current_stage.fuel_system.empty:
                    current_stage.active = False
                    event = "EVENT_SEPARATION"
                    thrust_magnitude = 0.0
        return event, thrust_magnitude

    def get_thrust_force(self, thrust_magnitude):
        if thrust_magnitude <= 0.0:
            return 0.0, 0.0
        return compute_thrust_force(thrust_magnitude, self.pitch_angle)
        
    def separate_current_stage(self):
        if self.current_stage_index < len(self.stages):
            separated_stage = self.stages[self.current_stage_index]
            separated_stage.detached = True
            
            self.current_stage_index += 1
            self.activate_next_stage()
            return separated_stage
        return None
        
    def jettison_fairing(self):
        if self.fairing_attached:
            self.fairing_attached = False
            return True
        return False
