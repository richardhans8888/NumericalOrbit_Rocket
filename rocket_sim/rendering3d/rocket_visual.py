# rendering3d/rocket_visual.py
from panda3d.core import Vec3, NodePath, TransparencyAttrib
from rendering3d.geometry import create_cylinder, create_cone
import math
from physics.constants import EARTH_RADIUS
import random

class RocketVisual:
    def __init__(self, engine, physics_rocket):
        self.engine = engine
        self.physics_rocket = physics_rocket
        self.head_node = engine.render.attachNewNode("RocketHead")

        # --- Exhaust flame (procedural cone, pointed downward) ---
        self.flame = create_cone("flame", 1.0, 1.0)
        self.flame.setHpr(0, 180, 0)
        self.flame.setColor(1.0, 0.75, 0.1, 0.85)
        self.flame.setTransparency(TransparencyAttrib.MAlpha)
        self.flame.reparentTo(self.engine.render)
        self.flame.hide()

        # --- SRB Left booster ---
        self.srb_left = NodePath("SRB_L")
        self.srb_left.reparentTo(self.head_node)
        srb_body = create_cylinder("sl_body", 1.8, 30.0)
        srb_body.reparentTo(self.srb_left)
        srb_body.setColor(0.92, 0.92, 0.90, 1.0)
        srb_nose = create_cone("sl_nose", 1.8, 3.5)
        srb_nose.reparentTo(self.srb_left)
        srb_nose.setPos(0, 0, 30.0)
        srb_nose.setColor(0.92, 0.92, 0.90, 1.0)
        # SRB nozzle
        srb_nozzle = create_cone("sl_noz", 1.2, 2.5)
        srb_nozzle.reparentTo(self.srb_left)
        srb_nozzle.setPos(0, 0, 0)
        srb_nozzle.setHpr(0, 180, 0)
        srb_nozzle.setColor(0.3, 0.3, 0.3, 1.0)
        self.srb_left.setPos(-4.8, 0, 0)

        # --- SRB Right booster ---
        self.srb_right = NodePath("SRB_R")
        self.srb_right.reparentTo(self.head_node)
        srb_body2 = create_cylinder("sr_body", 1.8, 30.0)
        srb_body2.reparentTo(self.srb_right)
        srb_body2.setColor(0.92, 0.92, 0.90, 1.0)
        srb_nose2 = create_cone("sr_nose", 1.8, 3.5)
        srb_nose2.reparentTo(self.srb_right)
        srb_nose2.setPos(0, 0, 30.0)
        srb_nose2.setColor(0.92, 0.92, 0.90, 1.0)
        srb_nozzle2 = create_cone("sr_noz", 1.2, 2.5)
        srb_nozzle2.reparentTo(self.srb_right)
        srb_nozzle2.setPos(0, 0, 0)
        srb_nozzle2.setHpr(0, 180, 0)
        srb_nozzle2.setColor(0.3, 0.3, 0.3, 1.0)
        self.srb_right.setPos(4.8, 0, 0)

        # --- Orange Core Stage ---
        self.core = NodePath("CORE")
        self.core.reparentTo(self.head_node)
        core_body = create_cylinder("core_body", 4.2, 42.0)
        core_body.reparentTo(self.core)
        core_body.setColor(0.88, 0.48, 0.08, 1.0)  # SLS orange
        # Core engine cluster (4 RS-25 nozzles)
        for nx, ny in [(1.5, 1.5), (-1.5, 1.5), (1.5, -1.5), (-1.5, -1.5)]:
            noz = create_cone("core_noz", 0.8, 2.0)
            noz.reparentTo(self.core)
            noz.setPos(nx, ny, 0)
            noz.setHpr(0, 180, 0)
            noz.setColor(0.25, 0.25, 0.28, 1.0)

        # --- Upper Stage (ICPS / white) ---
        self.upper = NodePath("UPPER")
        self.upper.reparentTo(self.head_node)
        upper_body = create_cylinder("upper_body", 3.5, 8.0)
        upper_body.reparentTo(self.upper)
        upper_body.setColor(0.95, 0.95, 0.93, 1.0)
        self.upper.setPos(0, 0, 42.0)

        # --- Orion capsule & fairing ---
        self.capsule = NodePath("CAPSULE")
        self.capsule.reparentTo(self.head_node)
        cap_body = create_cylinder("cap_body", 2.5, 5.0)
        cap_body.reparentTo(self.capsule)
        cap_body.setColor(0.95, 0.95, 0.95, 1.0)
        # Capsule cone / Launch Escape System
        las = create_cone("las", 2.5, 5.0)
        las.reparentTo(self.capsule)
        las.setPos(0, 0, 5.0)
        las.setColor(0.96, 0.96, 0.94, 1.0)
        # LES tower needle
        needle = create_cylinder("needle", 0.15, 4.0)
        needle.reparentTo(self.capsule)
        needle.setPos(0, 0, 10.0)
        needle.setColor(0.4, 0.4, 0.4, 1.0)
        self.capsule.setPos(0, 0, 50.0)

        self.debris_visuals = []
        self.srb_detached = False
        self.core_detached = False

    def sync(self, rocket, phase, world_debris, dt):
        z_visual = rocket.y - EARTH_RADIUS
        self.head_node.setPos(rocket.x, 0, z_visual)

        deg = math.degrees(rocket.pitch_angle) - 90.0
        self.head_node.setHpr(0, 0, deg)

        # --- SRB separation ---
        if rocket.current_stage_index > 0 and not self.srb_detached:
            self.srb_detached = True
            self.srb_left.wrtReparentTo(self.engine.render)
            self.srb_right.wrtReparentTo(self.engine.render)
            self.debris_visuals.append({
                "node": self.srb_left, "vx": -50.0, "vy": -15.0,
                "x": rocket.x - 5, "y": rocket.y
            })
            self.debris_visuals.append({
                "node": self.srb_right, "vx": 50.0, "vy": -15.0,
                "x": rocket.x + 5, "y": rocket.y
            })

        # --- Core separation ---
        if rocket.current_stage_index > 1 and not self.core_detached:
            self.core_detached = True
            self.core.wrtReparentTo(self.engine.render)
            self.debris_visuals.append({
                "node": self.core, "vx": 0.0, "vy": -25.0,
                "x": rocket.x, "y": rocket.y
            })

        # --- Debris physics (tumbling separated parts) ---
        for dv in self.debris_visuals:
            dv["x"] += dv["vx"] * dt
            dv["y"] += dv["vy"] * dt
            dv["vy"] -= 9.81 * dt
            dv["node"].setPos(dv["x"], 0, dv["y"] - EARTH_RADIUS)
            dv["node"].setHpr(
                dv["node"].getHpr() + Vec3(25 * dt, -10 * dt, 8 * dt)
            )

        # --- Engine flame ---
        is_active = (
            rocket.current_stage_index < len(rocket.stages)
            and rocket.stages[rocket.current_stage_index].active
        )
        if is_active:
            self.flame.show()
            alt = rocket.y - EARTH_RADIUS
            # Flame expands in vacuum
            base_width = 3.5
            if rocket.current_stage_index == 0:
                base_width = 6.0  # SRBs + core = massive plume
            vacuum_expand = max(0, alt / 30000.0)
            width = base_width + vacuum_expand
            length = random.uniform(12.0, 22.0) + width * 2.5

            self.flame.setScale(width, width, length)

            flame_p = self.head_node.getPos(self.engine.render)
            self.flame.setPos(flame_p.x, 0, flame_p.z)
            self.flame.setHpr(0, deg, 0)
        else:
            self.flame.hide()
