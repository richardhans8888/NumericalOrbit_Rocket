# simulation/world.py
from physics.constants import EARTH_RADIUS
from physics.gravity import compute_gravity_acceleration
from physics.integrator import update_velocity, update_position
from rocket.rocket import Rocket
from rocket.stage import Stage
from simulation.events import EVENT_STAGE_SEPARATION

class World:
    def __init__(self):
        self.rocket = Rocket()
        self.debris = [] # detached stages
        
        # Build 3 stages
        # Using simplified values for Phase 1
        s1 = Stage("Stage 1", dry_mass=15000, fuel_mass=250000, thrust_power=6000000, burn_rate=2000)
        s2 = Stage("Stage 2", dry_mass=5000, fuel_mass=50000, thrust_power=1200000, burn_rate=400)
        s3 = Stage("Stage 3", dry_mass=1500, fuel_mass=10000, thrust_power=200000, burn_rate=50)
        
        self.rocket.add_stage(s1)
        self.rocket.add_stage(s2)
        self.rocket.add_stage(s3)
        
        self.rocket.y = 0.0 # Surface of earth
        self.time_elapsed = 0.0
        
    def start(self):
        self.rocket.activate_next_stage()

    def update(self, dt):
        self.time_elapsed += dt
        
        # 1. Update rocket systems
        event, thrust_mag = self.rocket.update_systems(dt)
        
        if event == "EVENT_SEPARATION":
            detached = self.rocket.separate_current_stage()
            if detached:
                self.debris.append({
                    "stage": detached,
                    "x": self.rocket.x,
                    "y": self.rocket.y,
                    "vx": self.rocket.vx,
                    "vy": self.rocket.vy
                })
        
        # 2. Compute forces for active rocket
        rocket_mass = self.rocket.get_total_mass()
        if rocket_mass > 0:
            # Gravity acts based on distance from earth center
            r = EARTH_RADIUS + self.rocket.y
            g_accel = compute_gravity_acceleration(r)
            
            # Thrust force
            fx, fy = self.rocket.get_thrust_force(thrust_mag)
            ax_thrust = fx / rocket_mass
            ay_thrust = fy / rocket_mass
            
            # Total accel
            ax = ax_thrust
            ay = g_accel + ay_thrust
            
            # Prevent falling into earth before launch
            if self.rocket.y <= 0 and ay < 0:
                ay = 0
                self.rocket.vy = 0
            
            # Integrate motion
            self.rocket.vx, self.rocket.vy = update_velocity(self.rocket.vx, self.rocket.vy, ax, ay, dt)
            self.rocket.x, self.rocket.y = update_position(self.rocket.x, self.rocket.y, self.rocket.vx, self.rocket.vy, dt)
            
            # Ground collision check
            if self.rocket.y < 0:
                self.rocket.y = 0
                self.rocket.vy = 0
                
        # 3. Update physics for detached debris
        for d in self.debris:
            if d["y"] > 0:
                r = EARTH_RADIUS + d["y"]
                g_accel = compute_gravity_acceleration(r)
                
                d["vx"], d["vy"] = update_velocity(d["vx"], d["vy"], 0, g_accel, dt)
                d["x"], d["y"] = update_position(d["x"], d["y"], d["vx"], d["vy"], dt)
                
                if d["y"] <= 0:
                    d["y"] = 0
                    d["vy"] = 0
