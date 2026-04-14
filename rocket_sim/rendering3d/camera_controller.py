# rendering3d/camera_controller.py
class CameraController:
    def __init__(self, engine, target_node):
        self.engine = engine
        self.target = target_node
        self.engine.disableMouse() 
        self.mode = 0  
        
    def update(self):
        target_pos = self.target.getPos()
        alt = target_pos.z 
        
        if self.mode == 0:
            self.engine.camera.setPos(80, -150, target_pos.z + 10)
            self.engine.camera.lookAt(self.target)
            
            if alt > 150:
                self.mode = 1
                
        elif self.mode == 1:
            self.engine.camera.setPos(target_pos.x + 100, target_pos.y - 200, target_pos.z + 50)
            self.engine.camera.lookAt(self.target)
            
            if alt > 50000:
                self.mode = 2
                
        elif self.mode == 2:
            zoom = max(500, alt * 2.0)
            self.engine.camera.setPos(target_pos.x, target_pos.y - zoom, target_pos.z)
            self.engine.camera.lookAt(self.target)
            
    def cycle_mode(self):
        self.mode = (self.mode + 1) % 3
