# rendering3d/rocket_visual.py
from panda3d.core import Vec3, NodePath
from rendering3d.particle_system import SimpleParticleSystem
from rendering3d.geometry import create_cylinder, create_cone
import math
from physics.constants import EARTH_RADIUS

class RocketVisual:
    def __init__(self, engine, physics_rocket):
        self.engine = engine
        self.physics_rocket = physics_rocket
        
        self.head_node = engine.render.attachNewNode("RocketHead")
        self.stages = []
        
        stage_z = 0.0
        for i, s in enumerate(physics_rocket.stages[::-1]): 
            stage_node = NodePath(f"Stage_{i}")
            stage_node.reparentTo(self.head_node)
            
            radius = 2.0
            height = 15.0
            
            if i == 0:
                cyl1 = create_cylinder("b1", radius, height*0.3)
                cyl1.reparentTo(stage_node)
                cyl1.setColor(0.1, 0.1, 0.1, 1.0)
                
                cyl2 = create_cylinder("b2", radius, height*0.4)
                cyl2.reparentTo(stage_node)
                cyl2.setPos(0, 0, height*0.3)
                cyl2.setColor(0.6, 0.6, 0.6, 1.0)
                
                cyl3 = create_cylinder("b3", radius, height*0.3)
                cyl3.reparentTo(stage_node)
                cyl3.setPos(0, 0, height*0.7)
                cyl3.setColor(0.15, 0.15, 0.15, 1.0)
            else:
                cyl = create_cylinder("upper", radius, height)
                cyl.reparentTo(stage_node)
                cyl.setColor(0.9, 0.9, 0.95, 1.0)
                
            stage_node.setPos(0, 0, stage_z)
            stage_z += height
            self.stages.insert(0, stage_node) 
            
        fairing = create_cone("fairing", radius, 6.0)
        fairing.reparentTo(self.stages[0]) 
        fairing.setPos(0, 0, height)
        fairing.setColor(1.0, 1.0, 1.0, 1.0)
            
        self.smoke_system = SimpleParticleSystem(engine, color=(0.8, 0.8, 0.8, 0.5), growth_rate=4.0)
        self.flame_system = SimpleParticleSystem(engine, color=(1.0, 0.8, 0.2, 0.9), growth_rate=1.0)
        self.debris_visuals = []

    def sync(self, rocket, phase, world_debris, dt):
        z_visual = rocket.y - EARTH_RADIUS
        self.head_node.setPos(rocket.x, 0, z_visual)
        
        deg = math.degrees(rocket.pitch_angle) - 90.0
        self.head_node.setHpr(0, 0, deg)
        
        for i, s in enumerate(rocket.stages):
            vis = self.stages[i]
            if s.detached and vis.getParent() == self.head_node:
                vis.wrtReparentTo(self.engine.render) 
                self.debris_visuals.append({"stage": s, "node": vis})
                
        for d in world_debris:
            for dv in self.debris_visuals:
                if dv["stage"] == d["stage"]:
                    dv["node"].setPos(d["x"], 0, d["y"] - EARTH_RADIUS)
                    dv["node"].setHpr(dv["node"].getHpr() + Vec3(10*dt, 20*dt, 30*dt))
            
        is_active = rocket.current_stage_index < len(rocket.stages) and rocket.stages[rocket.current_stage_index].active
        if is_active:
            import random
            base_pos = self.head_node.getPos(self.engine.render)
            
            if rocket.y < EARTH_RADIUS + 50000:
                vel = Vec3(random.uniform(-5,5), random.uniform(-5,5), random.uniform(-10, -5))
                self.smoke_system.emit(base_pos, vel, size=3.0, life=3.0)
                
            flame_dir = self.engine.render.getRelativeVector(self.head_node, Vec3(0, 0, -50))
            scale = 2.0 + max(0, (rocket.y - EARTH_RADIUS)/10000)
            self.flame_system.emit(base_pos, flame_dir, size=scale, life=0.2)
            
        self.smoke_system.update(dt)
        self.flame_system.update(dt)
