# rendering/sprites.py
import pygame
import random

def draw_rocket(surface, screen_x, screen_y, is_active, stage_count):
    width = 20
    height_per_stage = 30
    total_height = height_per_stage * stage_count
    
    # Rocket Body
    rect = pygame.Rect(0, 0, width, total_height)
    rect.centerx = screen_x
    rect.bottom = screen_y
    pygame.draw.rect(surface, (200, 200, 200), rect)
    
    # Nose cone
    if stage_count > 0:
        points = [
            (screen_x - width//2, screen_y - total_height),
            (screen_x + width//2, screen_y - total_height),
            (screen_x, screen_y - total_height - 20)
        ]
        pygame.draw.polygon(surface, (255, 50, 50), points)
        
    # Lines representing stage breaks
    for s in range(1, stage_count):
        y_line = screen_y - s * height_per_stage
        pygame.draw.line(surface, (50, 50, 50), (screen_x - width//2, y_line), (screen_x + width//2, y_line), 2)
        
    # Engine exhaust
    if is_active:
        flame_points = [
            (screen_x - width//2 + 2, screen_y),
            (screen_x + width//2 - 2, screen_y),
            (screen_x, screen_y + random.randint(20, 50))
        ]
        pygame.draw.polygon(surface, (255, 150, 0), flame_points)

def draw_debris(surface, screen_x, screen_y):
    width = 20
    height = 30
    rect = pygame.Rect(0, 0, width, height)
    rect.centerx = screen_x
    rect.bottom = screen_y
    pygame.draw.rect(surface, (100, 100, 100), rect)
