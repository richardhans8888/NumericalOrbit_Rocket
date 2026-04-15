# physics/gravity.py
"""
Earth-centric gravitational model using Newton's Law of Universal Gravitation.

The gravity vector always points toward the center of Earth (origin).
This module computes the gravitational acceleration at any (x, y) position
in the 2D simulation plane, where the Earth center is at (0, 0).

Formula: g = G * M / r^2
Direction: unit vector from position toward origin
"""
import math
from physics.constants import G, EARTH_MASS

def compute_gravity_vector(x, y):
    """
    Computes true 2D gravity acceleration vector pulling towards (0,0).
    
    Args:
        x: horizontal position in meters (Earth-centric)
        y: vertical position in meters (Earth-centric)
        
    Returns:
        tuple (ax, ay): gravitational acceleration components in m/s^2
    """
    dist_sq = x * x + y * y
    if dist_sq == 0:
        return 0.0, 0.0
        
    distance = math.sqrt(dist_sq)
    
    # Newton's law: F = G*M*m/r^2, so a = G*M/r^2
    accel_mag = (G * EARTH_MASS) / dist_sq
    
    # Unit vector pointing from position (x,y) toward origin (0,0)
    ux = -x / distance
    uy = -y / distance
    
    return accel_mag * ux, accel_mag * uy

