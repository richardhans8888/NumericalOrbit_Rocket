# rendering/sprites.py
import pygame
import random

def draw_rocket(surface, screen_x, screen_y, is_active, stage_count, rotation_deg=0.0):
    width = 16
    height_per_stage = 24
    total_height = height_per_stage * stage_count
    
    surf_size = total_height + 80
    temp_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    
    cx = surf_size // 2
    cy = surf_size // 2
    
    # Body
    rect = pygame.Rect(0, 0, width, total_height)
    rect.center = (cx, cy)
    pygame.draw.rect(temp_surf, (220, 220, 220), rect)
    
    # Nose cone
    if stage_count > 0:
        points = [
            (cx - width//2, cy - total_height//2),
            (cx + width//2, cy - total_height//2),
            (cx, cy - total_height//2 - 15)
        ]
        pygame.draw.polygon(temp_surf, (200, 50, 50), points)
        
    # Lines representing stage breaks
    for s in range(1, stage_count):
        y_line = cy - total_height//2 + s * height_per_stage
        pygame.draw.line(temp_surf, (50, 50, 50), (cx - width//2, y_line), (cx + width//2, y_line), 2)
        
    # Engine exhaust
    if is_active:
        flame_points = [
            (cx - width//2 + 2, cy + total_height//2),
            (cx + width//2 - 2, cy + total_height//2),
            (cx, cy + total_height//2 + random.randint(20, 40))
        ]
        pygame.draw.polygon(temp_surf, (255, 120, 0), flame_points)

    # Pygame rotate rotates CCW, our trig gave us mathematical CCW
    rotated_surf = pygame.transform.rotate(temp_surf, rotation_deg)
    rot_rect = rotated_surf.get_rect(center=(screen_x, screen_y))
    surface.blit(rotated_surf, rot_rect.topleft)

def draw_debris(surface, screen_x, screen_y):
    pygame.draw.rect(surface, (100, 100, 100), (screen_x - 8, screen_y - 12, 16, 24))
