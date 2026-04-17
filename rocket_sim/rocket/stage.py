# rocket/stage.py
from rocket.fuel_system import FuelSystem

class Stage:
    def __init__(self, name, dry_mass, fuel_mass, thrust_sl, thrust_vac, burn_rate):
        self.name = name
        self.dry_mass = dry_mass
        self.fuel_system = FuelSystem(fuel_mass)
        self.thrust_sl = thrust_sl
        self.thrust_vac = thrust_vac
        self.burn_rate = burn_rate
        self.active = False
        self.detached = False
        
    def get_mass(self):
        return self.dry_mass + self.fuel_system.fuel
        
    def update(self, current_thrust_power, dt):
        if not self.active or self.detached:
            return 0.0
            
        if self.fuel_system.empty:
            return 0.0

        if current_thrust_power <= 0.0:
            return 0.0
            
        ref = max(self.thrust_vac, self.thrust_sl, 1.0)
        thrust_frac = max(0.0, min(1.25, current_thrust_power / ref))
        fuel_to_consume = self.burn_rate * thrust_frac * dt
        self.fuel_system.consume(fuel_to_consume)
        
        if self.fuel_system.empty:
            return 0.0
            
        return current_thrust_power
