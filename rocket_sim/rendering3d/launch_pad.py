# rendering3d/launch_pad.py
from panda3d.core import NodePath, LineSegs

class LaunchPad:
    def __init__(self, engine):
        self.engine = engine
        
        try:
            box = engine.loader.loadModel("models/box")
            sphere = engine.loader.loadModel("models/misc/sphere")
        except:
            pass
            
        self.pad_root = engine.render.attachNewNode("LaunchPad")
        self.pad_root.setPos(0, 0, 0)
        
        deck = box.copyTo(self.pad_root)
        deck.setScale(20, 20, 2)
        deck.setPos(0, 0, -1)
        deck.setColor(0.15, 0.15, 0.15, 1.0)
        
        stripe = box.copyTo(self.pad_root)
        stripe.setScale(20.2, 20.2, 0.5)
        stripe.setPos(0, 0, -0.2)
        stripe.setColor(0.8, 0.7, 0.1, 1.0)
        
        ramp = box.copyTo(self.pad_root)
        ramp.setScale(26, 20, 1)
        ramp.setPos(0, 0, -2)
        ramp.setColor(0.1, 0.1, 0.1, 1.0)
        
        for side in [-1, 1]:
            st = box.copyTo(self.pad_root)
            st.setScale(1.5, 1.5, 20)
            st.setPos(side * 6, 0, 10) 
            st.setColor(0.9, 0.5, 0.0, 1.0) 
            
            for z in range(2, 18, 4):
                truss = box.copyTo(self.pad_root)
                truss.setScale(0.5, 0.5, 5)
                truss.setPos(side * 6, 0, z+2)
                truss.setHpr(0, 45, 0)
                truss.setColor(0.9, 0.6, 0.1, 1.0)
            
        tower_base = box.copyTo(self.pad_root)
        tower_base.setScale(3.5, 3.5, 26)
        tower_base.setPos(-16, 0, 13)
        tower_base.setColor(0.1, 0.1, 0.1, 1.0)
        
        tower_top = box.copyTo(self.pad_root)
        tower_top.setScale(4.5, 4.5, 4)
        tower_top.setPos(-16, 0, 28)
        tower_top.setColor(0.4, 0.4, 0.4, 1.0)
        
        antenna = box.copyTo(self.pad_root)
        antenna.setScale(0.2, 0.2, 6)
        antenna.setPos(-16, 0, 33)
        antenna.setColor(0.8, 0.2, 0.2, 1.0)
        
        ls = LineSegs()
        ls.setColor(0.9, 0.8, 0.1, 1.0)
        ls.setThickness(2.0)
        for z in range(0, 26, 3):
            z_f = float(z)
            ls.moveTo(-14.0, -1.8, z_f)
            ls.drawTo(-14.0, 1.8, z_f)
            ls.drawTo(-17.8, 1.8, z_f)
            ls.drawTo(-17.8, -1.8, z_f)
            ls.drawTo(-14.0, -1.8, z_f)
            ls.moveTo(-14.0, -1.8, z_f)
            ls.drawTo(-14.0, 1.8, z_f+3.0)
            
        scaff_node = ls.create()
        self.pad_root.attachNewNode(scaff_node)
        
        tank = sphere.copyTo(self.pad_root)
        tank.setScale(6, 6, 6)
        tank.setPos(22, 0, 8)
        tank.setColor(0.95, 0.95, 0.95, 1.0)
        
        for lx in [20, 24]:
            for ly in [-2, 2]:
                leg = box.copyTo(self.pad_root)
                leg.setScale(0.5, 0.5, 4)
                leg.setPos(lx, ly, 2)
                leg.setColor(0.7, 0.7, 0.7, 1.0)
