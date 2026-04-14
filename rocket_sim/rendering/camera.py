# rendering/camera.py
import config
from physics.constants import EARTH_RADIUS

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.zoom = 5.0 # meters per pixel
        self.center_x_meters = 0.0
        self.center_y_meters = EARTH_RADIUS
        
    def update(self, rocket_x, rocket_y, altitude):
        self.center_x_meters = rocket_x
        self.center_y_meters = rocket_y
        
        # Dynamic zoom out to see orbital curvature
        zoom_target = max(5.0, altitude / 200.0) 
        self.zoom += (zoom_target - self.zoom) * 0.05
        
    def world_to_screen(self, world_x, world_y):
        dx = world_x - self.center_x_meters
        dy = world_y - self.center_y_meters
        
        screen_x = self.width / 2.0 + (dx / self.zoom)
        screen_y = self.height / 2.0 - (dy / self.zoom)
        return int(screen_x), int(screen_y)
        
    def get_screen_radius(self, world_radius):
        return int(world_radius / self.zoom)
