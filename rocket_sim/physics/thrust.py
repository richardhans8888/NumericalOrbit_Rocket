# physics/thrust.py
import math

def compute_thrust_force(engine_power, direction_angle_rad=math.pi / 2.0):
    """
    Computes thrust force vector.
    direction_angle_rad: angle in radians. pi/2 is straight up.
    Returns (Fx, Fy)
    """
    fx = engine_power * math.cos(direction_angle_rad)
    fy = engine_power * math.sin(direction_angle_rad)
    return (fx, fy)
