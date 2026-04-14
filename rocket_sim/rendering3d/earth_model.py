# rendering3d/earth_model.py
from panda3d.core import NodePath
from physics.constants import EARTH_RADIUS
import random

class EarthModel:
    def __init__(self, engine):
        self.engine = engine
        
        try:
            self.model = engine.loader.loadModel("models/misc/sphere")
            box = engine.loader.loadModel("models/box")
        except:
            pass
            
        self.model.reparentTo(engine.render)
        self.model.setScale(EARTH_RADIUS)
        self.model.setPos(0, 0, -EARTH_RADIUS)
        self.model.setColor(0.1, 0.3, 0.4, 1.0)
        
        self.land_node = engine.render.attachNewNode("DetailedLand")
        
        for ix in range(-30, 30):
            for iy in range(-20, 50): 
                tile = box.copyTo(self.land_node)
                tile.setScale(1000, 1000, 2)
                dist_sq = (ix*1000)**2 + (iy*1000)**2
                curved_z = -2 - (dist_sq / (2 * EARTH_RADIUS))
                
                tile.setPos(ix * 1000, iy * 1000, curved_z)
                
                r = random.uniform(0.3, 0.5)
                g = random.uniform(0.5, 0.8)
                b = random.uniform(0.2, 0.4)
                tile.setColor(r, g, b, 1.0)
        
        concrete = box.copyTo(self.land_node)
        concrete.setScale(200, 200, 2.5)
        concrete.setPos(0, 0, -2.5)
        concrete.setColor(0.4, 0.4, 0.42, 1.0)
        
        for i in range(-150, 150):
            tree = self.model.copyTo(self.land_node)
            size = random.uniform(10, 60)
            tree.setScale(size)
            dist_x = i * 150
            dist_y = 15000 + random.uniform(-1000, 1000)
            dist_sq = dist_x**2 + dist_y**2
            curved_z = size*0.5 - (dist_sq / (2 * EARTH_RADIUS))
            
            tree.setPos(dist_x, dist_y, curved_z)
            tree.setColor(0.1, 0.25, 0.4, 1.0)
            
    def destroy(self):
        self.model.removeNode()
        self.land_node.removeNode()
