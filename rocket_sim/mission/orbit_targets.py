# mission/orbit_targets.py
"""
Target orbit definitions for satellite launch missions.
Altitudes and velocities are approximate circular-orbit values.
"""
from physics.constants import EARTH_RADIUS
import math

# Convenience: circular orbital velocity at radius r
def _v_circ(alt_m):
    G = 6.674e-11
    M = 5.972e24
    r = EARTH_RADIUS + alt_m
    return math.sqrt(G * M / r)

ORBITS = {
    "LEO": {
        "name": "Low Earth Orbit (LEO)",
        "target_altitude_m": 400000.0,          # 400 km ISS-class
        "target_velocity_m_s": 7670.0,
        "inclination_deg": 28.5,
        "description": "400 km circular orbit. Used for crewed missions, imaging, comms constellations.",
        "color": (0, 200, 255),                  # cyan
    },
    "SSO": {
        "name": "Sun-Synchronous Orbit (SSO)",
        "target_altitude_m": 500000.0,           # 500 km
        "target_velocity_m_s": 7613.0,
        "inclination_deg": 97.4,
        "description": "500 km polar orbit. Consistent sun angle — ideal for Earth observation satellites.",
        "color": (100, 255, 140),                # green
    },
    "MEO": {
        "name": "Medium Earth Orbit (MEO)",
        "target_altitude_m": 20200000.0,         # GPS altitude
        "target_velocity_m_s": 3870.0,
        "inclination_deg": 55.0,
        "description": "20,200 km. GPS/GNSS navigation satellite constellation altitude.",
        "color": (255, 200, 50),                 # yellow
    },
    "GTO": {
        "name": "Geostationary Transfer Orbit (GTO)",
        "target_altitude_m": 35786000.0,
        "target_velocity_m_s": 10200.0,
        "inclination_deg": 0.0,
        "description": "Transfer orbit to GEO. Used for large comms & weather satellites.",
        "color": (220, 80, 255),                 # magenta
    },
}
