# mission/mission_profile.py
from mission.vehicle_database import VEHICLES
from mission.orbit_targets import ORBITS

class MissionProfile:
    def __init__(self, vehicle_id, orbit_id):
        self.vehicle_id = vehicle_id
        self.orbit_id = orbit_id
        self.vehicle_data = VEHICLES[vehicle_id]
        self.orbit_data = ORBITS[orbit_id]
