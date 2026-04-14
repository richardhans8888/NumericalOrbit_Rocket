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
        deck.setScale(10, 10, 2)
        deck.setPos(0, 0, -1)
        deck.setColor(0.5, 0.5, 0.5, 1.0)
