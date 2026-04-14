# rendering3d/earth_model.py
from panda3d.core import NodePath
from physics.constants import EARTH_RADIUS

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
        self.ground.setColor(0.4, 0.4, 0.4, 1.0)
        
    def destroy(self):
        self.model.removeNode()
        self.ground.removeNode()
