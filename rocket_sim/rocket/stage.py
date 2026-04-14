# rocket/stage.py
from rocket.fuel_system import FuelSystem

class Stage:
    def __init__(self, name, dry_mass, fuel_mass, thrust_power, burn_rate):
        self.name = name
        self.dry_mass = dry_mass
        self.fuel_system = FuelSystem(fuel_mass)
        self.thrust_power = thrust_power
        self.burn_rate = burn_rate
        self.active = False
        self.detached = False
        
    def get_mass(self):
        return self.dry_mass + self.fuel_system.fuel
        
    def update(self, dt):
        if not self.active or self.detached:
            return 0.0
            
        if self.fuel_system.empty:
            return 0.0
            
        fuel_to_consume = self.burn_rate * dt
        self.fuel_system.consume(fuel_to_consume)
        
        if self.fuel_system.empty:
            return 0.0
            
        return self.thrust_power
