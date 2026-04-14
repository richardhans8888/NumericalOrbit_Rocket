# physics/thrust.py
"""
Thrust force decomposition module.

Converts scalar thrust magnitude and direction angle into 2D force components.
The angle is measured from the positive x-axis:
    - pi/2 (90 degrees) = straight up
    - 0 = horizontal (prograde at equator)
    
Force decomposition:
    Fx = F * cos(theta)
    Fy = F * sin(theta)
"""
import math

def compute_thrust_force(engine_power, direction_angle_rad=math.pi / 2.0):
    """
    Decompose engine thrust into x and y force components.
    
    Args:
        engine_power: total thrust magnitude in Newtons
        direction_angle_rad: angle from positive x-axis in radians
                            (pi/2 = straight up, 0 = horizontal right)
    
    Returns:
        tuple (Fx, Fy): force components in Newtons
    """
    fx = engine_power * math.cos(direction_angle_rad)
    fy = engine_power * math.sin(direction_angle_rad)
    return (fx, fy)

