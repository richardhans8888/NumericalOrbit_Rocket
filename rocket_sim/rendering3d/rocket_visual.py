# rendering3d/rocket_visual.py
from panda3d.core import Vec3, NodePath
from rendering3d.geometry import create_cylinder, create_cone
import math
from physics.constants import EARTH_RADIUS

class RocketVisual:
    def __init__(self, engine, physics_rocket):
        self.engine = engine
        self.physics_rocket = physics_rocket
        self.head_node = engine.render.attachNewNode("RocketHead")
        
        # SRB Left
        self.srb_left = NodePath("SRB_L")
        self.srb_left.reparentTo(self.head_node)
        srb_l_geom = create_cylinder("s1", 1.8, 30.0)
        srb_l_geom.reparentTo(self.srb_left)
        srb_l_geom.setColor(0.9, 0.9, 0.9, 1.0)
        srb_l_cone = create_cone("s1c", 1.8, 3.0)
        srb_l_cone.reparentTo(self.srb_left)
        srb_l_cone.setPos(0, 0, 30.0)
        srb_l_cone.setColor(0.9, 0.9, 0.9, 1.0)
        self.srb_left.setPos(-4.5, 0, 0)
        
        # SRB Right
        self.srb_right = NodePath("SRB_R")
        self.srb_right.reparentTo(self.head_node)
        srb_r_geom = create_cylinder("s2", 1.8, 30.0)
        srb_r_geom.reparentTo(self.srb_right)
        srb_r_geom.setColor(0.9, 0.9, 0.9, 1.0)
        srb_r_cone = create_cone("s2c", 1.8, 3.0)
        srb_r_cone.reparentTo(self.srb_right)
        srb_r_cone.setPos(0, 0, 30.0)
        srb_r_cone.setColor(0.9, 0.9, 0.9, 1.0)
        self.srb_right.setPos(4.5, 0, 0)
        
        # ORANGE CORE
        self.core = NodePath("CORE")
        self.core.reparentTo(self.head_node)
        core_geom = create_cylinder("c1", 4.0, 40.0)
        core_geom.reparentTo(self.core)
        core_geom.setColor(0.85, 0.45, 0.1, 1.0) # Vivid Orange
        
        # WHITE UPPER STAGE & PAYLOAD CAPSULE
        self.capsule = NodePath("CAPSULE")
        self.capsule.reparentTo(self.head_node)
        cap_geom = create_cylinder("c2", 4.0, 10.0)
        cap_geom.reparentTo(self.capsule)
        cap_geom.setColor(0.95, 0.95, 0.95, 1.0)
        fairing = create_cone("f1", 4.0, 6.0)
        fairing.reparentTo(self.capsule)
        fairing.setPos(0, 0, 10.0)
        fairing.setColor(0.95, 0.95, 0.95, 1.0)
        self.capsule.setPos(0, 0, 40.0)
        
        self.debris_visuals = []
        self.srb_detached = False
        self.core_detached = False

    def sync(self, rocket, phase, world_debris, dt):
        z_visual = rocket.y - EARTH_RADIUS
        self.head_node.setPos(rocket.x, 0, z_visual)
        
        deg = math.degrees(rocket.pitch_angle) - 90.0
        self.head_node.setHpr(0, 0, deg)
        
        # Separation Event 1: Drop side SRBs
        if rocket.current_stage_index > 0 and not self.srb_detached:
            self.srb_detached = True
            self.srb_left.wrtReparentTo(self.engine.render)
            self.srb_right.wrtReparentTo(self.engine.render)
            # Add dramatic lateral push velocity!
            self.debris_visuals.append({"node": self.srb_left, "vx": -40.0, "vy": -20.0, "x": rocket.x, "y": rocket.y})
            self.debris_visuals.append({"node": self.srb_right, "vx": 40.0, "vy": -20.0, "x": rocket.x, "y": rocket.y})
            
        # Separation Event 2: Drop Core
        if rocket.current_stage_index > 1 and not self.core_detached:
            self.core_detached = True
            self.core.wrtReparentTo(self.engine.render)
            self.debris_visuals.append({"node": self.core, "vx": 0.0, "vy": -30.0, "x": rocket.x, "y": rocket.y})
            
        # Move visual custom debris using simple falling physics
        for dv in self.debris_visuals:
            dv["x"] += dv["vx"] * dt
            dv["y"] += dv["vy"] * dt
            dv["vy"] -= 9.81 * dt 
            dv["node"].setPos(dv["x"], 0, dv["y"] - EARTH_RADIUS)
            dv["node"].setHpr(dv["node"].getHpr() + Vec3(30*dt, -15*dt, 5*dt))
