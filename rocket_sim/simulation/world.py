# simulation/world.py
import math
from physics.constants import EARTH_RADIUS
from physics.gravity import compute_gravity_vector
from physics.drag import compute_drag_force
from physics.integrator import update_velocity, update_position
from rocket.rocket import Rocket
from mission.flight_phases import FlightPhase
from simulation.events import EVENT_STAGE_SEPARATION, EVENT_ENGINE_CUTOFF

class World:
    def __init__(self, mission_profile):
        self.mission = mission_profile
        self.rocket = Rocket(self.mission.vehicle_data)
        self.debris = []
        self.time_elapsed = 0.0
        
        self.phase = FlightPhase.PRELAUNCH
        self.time_warp = 1.0
        
    def start(self):
        self.phase = FlightPhase.LIFTOFF
        self.rocket.activate_next_stage()

    def update(self, dt_real):
        if self.phase == FlightPhase.PRELAUNCH:
            return
            
        dt = dt_real * self.time_warp
        self.time_elapsed += dt
        
        alt = self.rocket.get_altitude()
        vel = self.rocket.get_velocity_mag()
        
        throttle_pct = 1.0
        if self.phase != FlightPhase.SECO:
            # Max Q check (~10km to 15km)
            if 10000 < alt < 15000:
                self.phase = FlightPhase.MAX_Q
                throttle_pct = 0.6
                
            # Gravity Turn Profile
            if alt > 15000:
                if self.phase <= FlightPhase.MAX_Q:
                    self.phase = FlightPhase.GRAVITY_TURN
                
            target_alt = self.mission.orbit_data["target_altitude_m"]
            
            # Very simplistic gravity turn that zeros out pitch as we approach target altitude
            # Starts aggressively pitching down above 15km
            if alt > 1000:
                pitch_fraction = 1.0 - min((alt - 1000) / (target_alt * 0.9), 1.0)
                # Keep it strictly between pi/2 (up) and 0 (horizontal)
                target_pitch = (math.pi / 2.0) * max(pitch_fraction, 0.0)
                # Wait, if we pitch to 0, thrust is in +x. That is correct.
                # However, orbital velocity is a tangent to the Earth curve.
                # To be robust in 2D, pitch should be relative to the local orbital tangent!
                # Local tangent angle: (x,y) is position. Radial is atan2(y, x). Tangent is radial - pi/2.
                radial_angle = math.atan2(self.rocket.y, self.rocket.x)
                tangent_angle = radial_angle - (math.pi / 2.0)
                
                # We start pointing radially outward: radial_angle
                # And transition to tangent_angle
                self.rocket.pitch_angle = radial_angle * pitch_fraction + tangent_angle * (1.0 - pitch_fraction)
        
        # 1. Update Rocket Systems
        event, thrust_mag_raw = self.rocket.update_systems(dt)
        thrust_mag = thrust_mag_raw * throttle_pct
        
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
                self.phase = FlightPhase.BOOSTER_BURNOUT
                # Jump to second stage phase if applicable
                if len(self.rocket.stages) - self.rocket.current_stage_index == 1:
                     self.phase = FlightPhase.SECOND_STAGE_BURN

        if alt > self.rocket.vehicle_data.get("fairing", {}).get("jettison_altitude", 999999) and self.rocket.fairing_attached:
            self.rocket.jettison_fairing()
            self.phase = FlightPhase.FAIRING_SEP
            
        if vel >= self.mission.orbit_data["target_velocity_m_s"] and self.phase != FlightPhase.SECO:
            self.phase = FlightPhase.SECO
            if self.rocket.current_stage_index < len(self.rocket.stages):
                self.rocket.stages[self.rocket.current_stage_index].active = False
                
        # 2. Physics integration
        rocket_mass = self.rocket.get_total_mass()
        if rocket_mass > 0:
            gx, gy = compute_gravity_vector(self.rocket.x, self.rocket.y)
            
            if self.phase == FlightPhase.SECO:
                fx, fy = 0.0, 0.0
            else:
                fx, fy = self.rocket.get_thrust_force(thrust_mag)
                
            ax_thrust = fx / rocket_mass
            ay_thrust = fy / rocket_mass
            
            drag_mag = compute_drag_force(vel, alt, self.rocket.drag_coefficient, self.rocket.cross_sectional_area)
            ax_drag, ay_drag = 0.0, 0.0
            if vel > 0.0:
                ax_drag = -(self.rocket.vx / vel) * (drag_mag / rocket_mass)
                ay_drag = -(self.rocket.vy / vel) * (drag_mag / rocket_mass)

            ax = gx + ax_thrust + ax_drag
            ay = gy + ay_thrust + ay_drag
            
            if alt <= 0.0 and self.phase == FlightPhase.PRELAUNCH:
                ax, ay = 0.0, 0.0
                self.rocket.vx, self.rocket.vy = 0.0, 0.0
                     
            self.rocket.vx, self.rocket.vy = update_velocity(self.rocket.vx, self.rocket.vy, ax, ay, dt)
            self.rocket.x, self.rocket.y = update_position(self.rocket.x, self.rocket.y, self.rocket.vx, self.rocket.vy, dt)
            
        # 3. Handle Debris
        for d in self.debris:
            r = math.sqrt(d["x"]**2 + d["y"]**2)
            d_alt = r - EARTH_RADIUS
            if d_alt > 0:
                gx, gy = compute_gravity_vector(d["x"], d["y"])
                
                d_vel = math.sqrt(d["vx"]**2 + d["vy"]**2)
                d_drag_mag = compute_drag_force(d_vel, d_alt, 1.0, 5.0)
                
                d_mass = d["stage"].dry_mass
                ax_drag = -(d["vx"] / d_vel) * (d_drag_mag / d_mass) if d_vel > 0 else 0
                ay_drag = -(d["vy"] / d_vel) * (d_drag_mag / d_mass) if d_vel > 0 else 0
                
                d["vx"], d["vy"] = update_velocity(d["vx"], d["vy"], gx + ax_drag, gy + ay_drag, dt)
                d["x"], d["y"] = update_position(d["x"], d["y"], d["vx"], d["vy"], dt)
