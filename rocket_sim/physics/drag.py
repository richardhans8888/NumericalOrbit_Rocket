# physics/drag.py
"""
Atmospheric drag model using exponential density decay.

The atmosphere is modeled as an exponentially decreasing density profile:
    rho(h) = rho_0 * exp(-h / H)

where rho_0 = 1.225 kg/m^3 (sea level) and H = 8500 m (scale height).

Above the Karman line (100 km), density is treated as zero.

Drag force follows the standard aerodynamic drag equation:
    F_drag = 0.5 * rho * v^2 * Cd * A
"""
import math
from physics.constants import SEA_LEVEL_DENSITY, SCALE_HEIGHT, ATMOSPHERE_BOUNDARY

def get_air_density(altitude):
    """
    Calculate atmospheric density at a given altitude using exponential model.
    
    Args:
        altitude: height above Earth surface in meters
        
    Returns:
        density in kg/m^3
    """
    if altitude > ATMOSPHERE_BOUNDARY:
        return 0.0
    return SEA_LEVEL_DENSITY * math.exp(-altitude / SCALE_HEIGHT)

def compute_drag_force(velocity_magnitude, altitude, drag_coefficient, cross_sectional_area):
    """
    Compute aerodynamic drag force magnitude.
    
    Uses the standard drag equation: F = 0.5 * rho * v^2 * Cd * A
    
    Args:
        velocity_magnitude: speed in m/s
        altitude: height above surface in meters
        drag_coefficient: Cd (dimensionless, typically 0.3-0.5 for rockets)
        cross_sectional_area: reference area in m^2
        
    Returns:
        drag force in Newtons
    """
    density = get_air_density(altitude)
    return 0.5 * density * (velocity_magnitude ** 2) * drag_coefficient * cross_sectional_area

