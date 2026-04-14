# rendering3d/launch_pad.py
from panda3d.core import NodePath

class LaunchPad:
    def __init__(self, engine):
        self.engine = engine
        
        try:
            box = engine.loader.loadModel("models/box")
        except:
            pass
            
        self.pad_root = engine.render.attachNewNode("LaunchPad")
        self.pad_root.setPos(0, 0, 0)
        
        deck = box.copyTo(self.pad_root)
        deck.setScale(20, 20, 2)
        deck.setPos(0, 0, -1)
        deck.setColor(0.4, 0.4, 0.42, 1.0)
        
        ramp = box.copyTo(self.pad_root)
        ramp.setScale(26, 20, 1)
        ramp.setPos(0, 0, -2)
        ramp.setColor(0.3, 0.3, 0.3, 1.0)
