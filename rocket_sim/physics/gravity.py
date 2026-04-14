# physics/gravity.py
from physics.constants import G, EARTH_MASS

def compute_gravity_acceleration(distance_from_earth_center):
    """
    Computes gravitational acceleration magnitude.
    Returns a negative value since gravity pulls downwards.
    """
    if distance_from_earth_center <= 0:
        return 0.0
    
    # a = GM / r^2
    # The pull is towards the earth center
    acceleration_magnitude = (G * EARTH_MASS) / (distance_from_earth_center ** 2)
    return -acceleration_magnitude  # Negative assuming y-axis points up
