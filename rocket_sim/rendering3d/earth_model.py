# rendering3d/earth_model.py
from panda3d.core import NodePath
from physics.constants import EARTH_RADIUS
import random

class EarthModel:
    def __init__(self, engine):
        self.engine = engine
        
        try:
            self.model = engine.loader.loadModel("models/misc/sphere")
            self.box = engine.loader.loadModel("models/box")
        except:
            pass
            
        self.model.reparentTo(engine.render)
        self.model.setScale(EARTH_RADIUS)
        self.model.setPos(0, 0, -EARTH_RADIUS)
        self.model.setColor(0.3, 0.3, 0.3, 1.0)
        
        self.ground = self.box.copyTo(engine.render)
        self.ground.setScale(100000, 100000, 2)
        self.ground.setPos(0, 0, -2)
        self.ground.setColor(0.55, 0.7, 0.3, 1.0) 
        
        self.clouds = engine.render.attachNewNode("Clouds")
        for _ in range(50):
            cloud = self.model.copyTo(self.clouds)
            scale_x = random.uniform(50, 200)
            scale_y = random.uniform(50, 200)
            scale_z = random.uniform(20, 50)
            cloud.setScale(scale_x, scale_y, scale_z)
            
            lx = random.uniform(-10000, 10000)
            ly = random.uniform(-10000, 10000)
            lz = random.uniform(1500, 8000)
            
            dist_sq = lx**2 + ly**2
            hz = lz - (dist_sq / (2 * EARTH_RADIUS))
            
            cloud.setPos(lx, ly, hz)
            cloud.setColor(1.0, 1.0, 1.0, 0.8)
            
    def destroy(self):
        self.model.removeNode()
        self.ground.removeNode()
        self.clouds.removeNode()
