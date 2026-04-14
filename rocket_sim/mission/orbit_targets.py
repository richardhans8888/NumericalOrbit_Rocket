# mission/orbit_targets.py

ORBITS = {
    "LEO": {
        "name": "Low Earth Orbit (LEO)",
        "target_altitude_m": 200000.0, # 200km
        "target_velocity_m_s": 7780.0,
        "description": "200 km circular orbit"
    },
    "GTO": {
        "name": "Geostationary Transfer Orbit (GTO)",
        "target_altitude_m": 35786000.0,
        "target_velocity_m_s": 10200.0,
        "description": "High energy transfer orbit"
    }
}
