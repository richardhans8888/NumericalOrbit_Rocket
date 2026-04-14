# rendering/camera.py
import config

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.y_offset_meters = 0.0
        
    def update(self, target_y_meters):
        # Target pixel height from bottom
        target_offset = target_y_meters - (self.height * 0.2) / config.PIXELS_PER_METER
        
        # Only pan up, don't pan back down to keep the starting look clean
        if target_offset > self.y_offset_meters:
            self.y_offset_meters = target_offset
            
    def world_to_screen(self, world_x, world_y):
        # Center x
        screen_x = self.width / 2 + world_x * config.PIXELS_PER_METER
        
        # Pygame +y is down. So y is inverted.
        screen_y = self.height - (world_y - self.y_offset_meters) * config.PIXELS_PER_METER
        return int(screen_x), int(screen_y)
