# physics/drag.py
import math
from physics.constants import SEA_LEVEL_DENSITY, SCALE_HEIGHT

def get_air_density(altitude):
    if altitude > 100000:
        return 0.0
    # Exponential decay model
    return SEA_LEVEL_DENSITY * math.exp(-altitude / SCALE_HEIGHT)

def compute_drag_force(velocity_magnitude, altitude, drag_coefficient, cross_sectional_area):
    density = get_air_density(altitude)
    # F = 1/2 * rho * v^2 * Cd * A
    return 0.5 * density * (velocity_magnitude ** 2) * drag_coefficient * cross_sectional_area
