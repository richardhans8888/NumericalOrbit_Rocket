# mission/vehicle_database.py

FALCON_9 = {
    "name": "Falcon 9 (Approx)",
    "stages": [
        {
            "name": "Stage 1 (Booster)",
            "dry_mass": 22200,
            "propellant_mass": 411000,
            "thrust_sl": 7607000,
            "thrust_vac": 8227000,
            "burn_time": 162.0,
            "engine_count": 9,
        },
        {
            "name": "Stage 2",
            "dry_mass": 4000,
            "propellant_mass": 111500,
            "thrust_sl": 0,
            "thrust_vac": 934000,
            "burn_time": 397.0,
            "engine_count": 1,
        }
    ],
    "fairing": {
        "mass": 1900,
        "jettison_altitude": 115000.0 # 115km
    },
    "cross_sectional_area": 10.5, # ~3.66m diameter
    "drag_coefficient": 0.4
}

VEHICLES = {
    "FALCON_9": FALCON_9
}
