# rendering3d/earth_model.py
from panda3d.core import NodePath, TransparencyAttrib
from physics.constants import EARTH_RADIUS
import random

class EarthModel:
    def __init__(self, engine):
        self.engine = engine
        self.root = engine.render.attachNewNode("EarthRoot")

        self.sphere = engine.loader.loadModel("models/misc/sphere")
        self.box = engine.loader.loadModel("models/box")

        # Strip default textures from source models
        self.sphere.setTextureOff(1)
        self.box.setTextureOff(1)

        # --- Large Earth sphere for orbital view ---
        self.earth_globe = self.sphere.copyTo(self.root)
        self.earth_globe.setScale(EARTH_RADIUS)
        self.earth_globe.setPos(0, 0, -EARTH_RADIUS)
        self.earth_globe.setColor(0.15, 0.35, 0.55, 1.0)

        # --- Simple green grass ground ---
        self.ground = self.box.copyTo(self.root)
        self.ground.setScale(200000, 200000, 1)
        self.ground.setPos(0, 0, -1)
        self.ground.setColor(0.35, 0.55, 0.2, 1.0)

        # --- Low-poly clouds ---
        self.clouds = self.root.attachNewNode("Clouds")
        random.seed(42)
        for _ in range(35):
            cloud = self.sphere.copyTo(self.clouds)
            sx = random.uniform(100, 400)
            sy = random.uniform(100, 400)
            sz = random.uniform(15, 40)
            cloud.setScale(sx, sy, sz)
            cx = random.uniform(-12000, 12000)
            cy = random.uniform(-12000, 12000)
            cz = random.uniform(2000, 6000)
            cloud.setPos(cx, cy, cz)
            cloud.setColor(1.0, 1.0, 1.0, 0.7)
            cloud.setTransparency(TransparencyAttrib.MAlpha)

    def destroy(self):
        self.root.removeNode()
