# rendering3d/particle_system.py
from panda3d.core import Vec4
import random

class SimpleParticleSystem:
    def __init__(self, engine, color, growth_rate=2.0):
        self.engine = engine
        self.particles = []
        self.color = Vec4(*color)
        self.growth_rate = growth_rate
        
        try:
            self.base_model = engine.loader.loadModel("models/misc/sphere")
        except:
            self.base_model = engine.loader.loadModel("smiley")
            
        # Particles use transparency
        self.base_model.setTransparency(True)
            
    def emit(self, pos_vec, vel_vec, size, life):
        p = self.base_model.copyTo(self.engine.render)
        p.setPos(pos_vec)
        p.setScale(size)
        p.setColor(self.color)
        
        self.particles.append({
            "node": p,
            "vel": vel_vec,
            "life": life,
            "max_life": life,
            "size": size
        })
        
    def update(self, dt):
        alive = []
        for p in self.particles:
            p["life"] -= dt
            if p["life"] > 0:
                pos = p["node"].getPos()
                pos += p["vel"] * dt
                p["node"].setPos(pos)
                
                # Expand size and fade transparency
                ratio = p["life"] / p["max_life"]
                growth = 1.0 + (self.growth_rate - 1.0) * (1.0 - ratio)
                p["node"].setScale(p["size"] * growth) 
                
                # Keep color but fade alpha
                color = Vec4(self.color)
                color[3] = ratio # Alpha fades out
                p["node"].setColor(color)
                
                alive.append(p)
            else:
                p["node"].removeNode()
        self.particles = alive
