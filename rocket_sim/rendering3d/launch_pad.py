# rendering3d/launch_pad.py
from panda3d.core import NodePath
from rendering3d.geometry import create_cylinder, create_cone

class LaunchPad:
    def __init__(self, engine):
        self.engine = engine
        box = engine.loader.loadModel("models/box")
        box.setTextureOff(1)  # Strip default rainbow texture

        self.pad_root = engine.render.attachNewNode("LaunchPad")
        self.pad_root.setPos(0, 0, 0)

        # --- Concrete launch mount ---
        deck = box.copyTo(self.pad_root)
        deck.setScale(25, 25, 3)
        deck.setPos(0, 0, -1.5)
        deck.setColor(0.55, 0.55, 0.52, 1.0)

        # Flame trench
        trench = box.copyTo(self.pad_root)
        trench.setScale(8, 20, 2)
        trench.setPos(0, 0, -4)
        trench.setColor(0.2, 0.2, 0.2, 1.0)

        # --- Access road ---
        road = box.copyTo(self.pad_root)
        road.setScale(8, 150, 0.3)
        road.setPos(0, -100, -0.5)
        road.setColor(0.35, 0.35, 0.35, 1.0)

        # --- VAB building ---
        vab = box.copyTo(self.pad_root)
        vab.setScale(60, 40, 70)
        vab.setPos(-200, 100, 34)
        vab.setColor(0.45, 0.45, 0.5, 1.0)

        # VAB door
        vab_door = box.copyTo(self.pad_root)
        vab_door.setScale(20, 1, 55)
        vab_door.setPos(-200, 80, 27)
        vab_door.setColor(0.3, 0.3, 0.35, 1.0)

        # --- Service Tower ---
        tower = box.copyTo(self.pad_root)
        tower.setScale(4, 4, 65)
        tower.setPos(12, 0, 31)
        tower.setColor(0.6, 0.55, 0.5, 1.0)

        # Tower arms
        arm = box.copyTo(self.pad_root)
        arm.setScale(8, 2, 2)
        arm.setPos(6, 0, 40)
        arm.setColor(0.6, 0.55, 0.5, 1.0)

        arm2 = box.copyTo(self.pad_root)
        arm2.setScale(8, 2, 2)
        arm2.setPos(6, 0, 25)
        arm2.setColor(0.6, 0.55, 0.5, 1.0)

        # --- Lightning towers ---
        for lx, ly in [(-30, 30), (30, 30), (-30, -30), (30, -30)]:
            pole = create_cylinder("lpole", 0.4, 80)
            pole.reparentTo(self.pad_root)
            pole.setPos(lx, ly, 0)
            pole.setColor(0.7, 0.7, 0.7, 1.0)

        # --- Support equipment ---
        for i in range(6):
            eq = box.copyTo(self.pad_root)
            eq.setScale(5, 3, 3)
            eq.setPos(-40 + i * 12, -40, 1.5)
            c = 0.4 + (i % 3) * 0.1
            eq.setColor(c, c * 0.9, c * 0.7, 1.0)
