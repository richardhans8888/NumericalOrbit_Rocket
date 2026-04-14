# rendering3d/camera_controller.py
import math

class CameraController:
    def __init__(self, engine, target_node):
        self.engine = engine
        self.target = target_node
        self.engine.disableMouse()
        self.mode = 0
        self.orbit_angle = 0.0

    def update(self):
        target_pos = self.target.getPos()
        alt = target_pos.z

        if self.mode == 0:
            # Pad camera: cinematic angle showing the full launch complex
            self.engine.camera.setPos(100, -180, 40)
            self.engine.camera.lookAt(self.target)

            if alt > 200:
                self.mode = 1

        elif self.mode == 1:
            # Tracking camera: follows rocket during atmospheric ascent
            dist = min(300, 80 + alt * 0.02)
            self.engine.camera.setPos(
                target_pos.x + dist * 0.6,
                target_pos.y - dist,
                target_pos.z + dist * 0.3
            )
            self.engine.camera.lookAt(self.target)

            if alt > 80000:
                self.mode = 2

        elif self.mode == 2:
            # Orbital camera: stays close enough to always see the rocket
            # Cap zoom so the rocket is never sub-pixel
            zoom = min(800, max(100, alt * 0.003))
            self.engine.camera.setPos(
                target_pos.x + zoom * 0.4,
                target_pos.y - zoom,
                target_pos.z + zoom * 0.3
            )
            self.engine.camera.lookAt(self.target)

    def cycle_mode(self):
        self.mode = (self.mode + 1) % 3
