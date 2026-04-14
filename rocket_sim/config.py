SCREEN_WIDTH = 800
SCREEN_HEIGHT = 1000
FPS = 60
TITLE = "Rocket Launch Simulator - Phase 1"

BG_COLOR = (10, 10, 20)
TEXT_COLOR = (255, 255, 255)

# Physics integration timestep
SIM_TIME_STEP = 1.0 / FPS

# Visual scale 
# Meters per pixel. If a rocket is 50m tall, and we want it to be 50px tall, then 1 pixel = 1 meter.
PIXELS_PER_METER = 1.0

# Start coordinates (usually earth surface)
START_ALTITUDE = 0.0
