# physics/gravity.py
import math
from physics.constants import G, EARTH_MASS

def compute_gravity_vector(x, y):
    """
    Computes true 2D gravity acceleration vector pulling towards (0,0) (center of Earth).
    Returns (ax, ay)
    """
    dist_sq = x*x + y*y
    if dist_sq == 0:
        return 0.0, 0.0
        
    distance = math.sqrt(dist_sq)
    accel_mag = (G * EARTH_MASS) / dist_sq
    
    # Unit vector pointing from (x,y) to origin (0,0)
    ux = -x / distance
    uy = -y / distance
    
    return accel_mag * ux, accel_mag * uy
