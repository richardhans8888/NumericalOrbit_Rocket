# simulation/world.py
import math
from physics.constants import EARTH_RADIUS
from physics.gravity import compute_gravity_vector
from physics.drag import compute_drag_force
from physics.integrator import update_velocity, update_position, rk4_step_state
from rocket.rocket import Rocket
from mission.flight_phases import FlightPhase
from simulation.events import EVENT_STAGE_SEPARATION, EVENT_ENGINE_CUTOFF

class World:
    def __init__(self, mission_profile):
        self.mission = mission_profile
        self.rocket = Rocket(self.mission.vehicle_data)
        self.debris = []
        self.time_elapsed = 0.0
        self.last_thrust_n = 0.0
        
        self.phase = FlightPhase.PRELAUNCH
        self.time_warp = 1.0
        self._entered_seco = False
        
    def start(self):
        self.phase = FlightPhase.LIFTOFF
        self.rocket.activate_next_stage()

    def _inject_to_target_orbit(self):
        target_alt = float(self.mission.orbit_data["target_altitude_m"])
        target_vel = float(self.mission.orbit_data["target_velocity_m_s"])

        r = math.hypot(self.rocket.x, self.rocket.y)
        if r <= 0:
            return

        target_r = EARTH_RADIUS + target_alt
        sx = target_r / r
        self.rocket.x *= sx
        self.rocket.y *= sx

        radial = math.atan2(self.rocket.y, self.rocket.x)
        tangent = radial - (math.pi / 2.0)
        self.rocket.vx = math.cos(tangent) * target_vel
        self.rocket.vy = math.sin(tangent) * target_vel

        m, a, cd = self.estimate_satellite_params()
        self.rocket.enter_satellite_mode(m, a, cd)

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
        event, thrust_mag = self.rocket.update_systems(dt, throttle_pct)
        self.last_thrust_n = thrust_mag
        
        if event == "EVENT_SEPARATION":
            detached = self.rocket.separate_current_stage()
            if detached:
                pitch = self.rocket.pitch_angle
                ux = math.cos(pitch)
                uy = math.sin(pitch)
                px = -uy
                py = ux
                back = 22.0
                side = 10.0
                dvx = -ux * back + px * side
                dvy = -uy * back + py * side
                self.debris.append({
                    "kind": "stage",
                    "stage": detached,
                    "x": self.rocket.x,
                    "y": self.rocket.y,
                    "vx": self.rocket.vx + dvx,
                    "vy": self.rocket.vy + dvy,
                    "age": 0.0
                })
                self.phase = FlightPhase.BOOSTER_BURNOUT
                # Jump to second stage phase if applicable
                if len(self.rocket.stages) - self.rocket.current_stage_index == 1:
                     self.phase = FlightPhase.SECOND_STAGE_BURN
                # If no stages remain, switch to satellite mode so dynamics continue (no mass=freeze)
                if self.rocket.current_stage_index >= len(self.rocket.stages) and not getattr(self.rocket, "satellite_mode", False):
                    m, a, cd = self.estimate_satellite_params()
                    self.rocket.enter_satellite_mode(m, a, cd)
                    self.phase = FlightPhase.SECO

        if alt > self.rocket.vehicle_data.get("fairing", {}).get("jettison_altitude", 999999) and self.rocket.fairing_attached:
            self.rocket.jettison_fairing()
            self.phase = FlightPhase.FAIRING_SEP
            pitch = self.rocket.pitch_angle
            ux = math.cos(pitch)
            uy = math.sin(pitch)
            px = -uy
            py = ux
            for sgn in (-1.0, 1.0):
                self.debris.append({
                    "kind": "fairing",
                    "stage": None,
                    "x": self.rocket.x + px * 3.0 * sgn,
                    "y": self.rocket.y + py * 3.0 * sgn,
                    "vx": self.rocket.vx + px * 18.0 * sgn - ux * 6.0,
                    "vy": self.rocket.vy + py * 18.0 * sgn - uy * 6.0,
                    "age": 0.0,
                })
            
        if vel >= self.mission.orbit_data["target_velocity_m_s"] and self.phase != FlightPhase.SECO:
            self.phase = FlightPhase.SECO
            if self.rocket.current_stage_index < len(self.rocket.stages):
                self.rocket.stages[self.rocket.current_stage_index].active = False
            self._entered_seco = True
            if getattr(self.mission, "vehicle_id", "") != "CUSTOM":
                self._inject_to_target_orbit()
                
        # 2. Physics integration
        rocket_mass = self.rocket.get_total_mass()
        if rocket_mass > 0:
            if self.phase == FlightPhase.SECO:
                def deriv(y):
                    x, y_, vx, vy = y
                    gax, gay = compute_gravity_vector(x, y_)
                    r = math.sqrt(x * x + y_ * y_)
                    alt_ = r - EARTH_RADIUS
                    vmag = math.sqrt(vx * vx + vy * vy)
                    dmag = compute_drag_force(vmag, alt_, self.rocket.drag_coefficient, self.rocket.cross_sectional_area)
                    dax, day = 0.0, 0.0
                    if vmag > 0:
                        dax = -(vx / vmag) * (dmag / rocket_mass)
                        day = -(vy / vmag) * (dmag / rocket_mass)
                    ax = gax + dax
                    ay = gay + day
                    return [vx, vy, ax, ay]

                s0 = [self.rocket.x, self.rocket.y, self.rocket.vx, self.rocket.vy]
                s1 = rk4_step_state(s0, dt, deriv)
                self.rocket.x, self.rocket.y, self.rocket.vx, self.rocket.vy = s1
            else:
                gx, gy = compute_gravity_vector(self.rocket.x, self.rocket.y)
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
                
                if d.get("kind") == "fairing":
                    d_mass = 250.0
                else:
                    d_mass = d["stage"].dry_mass
                ax_drag = -(d["vx"] / d_vel) * (d_drag_mag / d_mass) if d_vel > 0 else 0
                ay_drag = -(d["vy"] / d_vel) * (d_drag_mag / d_mass) if d_vel > 0 else 0
                
                d["vx"], d["vy"] = update_velocity(d["vx"], d["vy"], gx + ax_drag, gy + ay_drag, dt)
                d["x"], d["y"] = update_position(d["x"], d["y"], d["vx"], d["vy"], dt)

    def estimate_satellite_params(self):
        oid = getattr(self.mission, "orbit_id", "LEO")
        veh = self.mission.vehicle_data
        if oid == "GTO":
            cap = float(veh.get("payload_geo_kg", 800.0))
        else:
            cap = float(veh.get("payload_leo_kg", 800.0))
        mass = max(200.0, min(5000.0, cap * 0.25))
        area = 6.0 if oid in ("LEO", "SSO") else 10.0
        cd = 2.2
        return mass, area, cd
