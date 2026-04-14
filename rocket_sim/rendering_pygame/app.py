# rendering_pygame/app.py
# Full-featured Pygame rocket mission simulator renderer
import pygame
import sys
import math
import random
import collections
from mission.mission_profile import MissionProfile
from mission.flight_phases import FlightPhase, PHASE_NAMES
from mission.telemetry import format_time
from simulation.world import World
from physics.constants import EARTH_RADIUS

# ─── CONSTANTS ────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 800
DASH_H = 200  # bottom dashboard height
VIEW_H = HEIGHT - DASH_H  # 3D viewport height
FPS = 60

# Colors
C_SKY_TOP    = (30, 60, 120)
C_SKY_BOT    = (120, 170, 230)
C_SPACE      = (5, 5, 15)
C_GROUND     = (72, 140, 50)
C_GROUND_DK  = (55, 110, 38)
C_PAD        = (140, 140, 135)
C_PAD_DARK   = (80, 80, 80)
C_ROAD       = (90, 90, 90)
C_TOWER      = (160, 150, 140)
C_VAB        = (110, 115, 130)
C_VAB_DOOR   = (70, 75, 85)
C_ORANGE     = (225, 120, 20)
C_WHITE      = (240, 240, 235)
C_NOZZLE     = (60, 60, 65)
C_FLAME_IN   = (255, 255, 180)
C_FLAME_MID  = (255, 200, 50)
C_FLAME_OUT  = (255, 100, 20)
C_CLOUD      = (240, 245, 255)
C_DASH_BG    = (15, 20, 28)
C_DASH_LINE  = (50, 60, 80)
C_TEXT        = (220, 220, 220)
C_GREEN_GO   = (30, 255, 80)
C_CYAN       = (0, 200, 255)
C_YELLOW     = (255, 255, 60)
C_MAGENTA    = (210, 60, 210)
C_RED        = (255, 50, 50)


# ─── UTILITIES ────────────────────────────────────────────
def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def world_to_screen(wx, wy, cam_x, cam_y, zoom):
    """Convert physics world coords to screen pixel coords."""
    sx = WIDTH // 2 + (wx - cam_x) * zoom
    sy = VIEW_H // 2 - (wy - cam_y) * zoom
    return int(sx), int(sy)


# ─── GRAPH HELPER ─────────────────────────────────────────
class RollingGraph:
    def __init__(self, max_pts=80, max_val=100.0, color=C_CYAN, label=""):
        self.data = collections.deque(maxlen=max_pts)
        self.max_val = max_val
        self.color = color
        self.label = label

    def push(self, v):
        self.data.append(v)
        if v > self.max_val * 0.85:
            self.max_val = v * 1.3

    def draw(self, surface, rect, font):
        x, y, w, h = rect
        # background
        pygame.draw.rect(surface, (25, 30, 40), rect)
        pygame.draw.rect(surface, C_DASH_LINE, rect, 1)
        # axis lines
        for i in range(1, 4):
            ly = y + h - int(h * i / 4)
            pygame.draw.line(surface, (35, 40, 50), (x, ly), (x + w, ly))
        # plot
        if len(self.data) > 1:
            pts = []
            step = w / (len(self.data) - 1)
            for i, v in enumerate(self.data):
                px = x + int(i * step)
                frac = min(v / self.max_val, 1.0) if self.max_val > 0 else 0
                py = y + h - int(frac * (h - 4)) - 2
                pts.append((px, py))
            pygame.draw.lines(surface, self.color, False, pts, 2)
        # title
        lbl = font.render(self.label, True, (180, 180, 180))
        surface.blit(lbl, (x + 3, y + 2))
        # value
        val = self.data[-1] if self.data else 0
        vt = font.render(f"{val:.2f}", True, self.color)
        surface.blit(vt, (x + w - vt.get_width() - 3, y + 2))


class TrajectoryPlot:
    def __init__(self, max_pts=300, scale=500.0, color=C_YELLOW, label="", draw_earth=False):
        self.pts = collections.deque(maxlen=max_pts)
        self.scale = scale
        self.color = color
        self.label = label
        self.draw_earth = draw_earth

    def push(self, px, py):
        self.pts.append((px / 1000.0, py / 1000.0))

    def draw(self, surface, rect, font):
        x, y, w, h = rect
        pygame.draw.rect(surface, (20, 25, 35), rect)
        pygame.draw.rect(surface, C_DASH_LINE, rect, 1)

        cx, cy = x + w // 2, y + h // 2

        if self.draw_earth:
            er = (EARTH_RADIUS / 1000.0) / self.scale * (w / 2)
            if er > 2:
                pygame.draw.circle(surface, (25, 60, 90), (cx, cy), int(er), 1)

        if len(self.pts) > 1:
            screen_pts = []
            for kx, ky in self.pts:
                if self.draw_earth:
                    sx = cx + int((kx / self.scale) * (w / 2))
                    sy = cy - int((ky / self.scale) * (h / 2))
                else:
                    sx = x + int((kx / self.scale) * w) + w // 2
                    sy = y + h - int(((ky - EARTH_RADIUS / 1000.0) / self.scale) * h)
                screen_pts.append((sx, sy))
            pygame.draw.lines(surface, self.color, False, screen_pts, 2)

        lbl = font.render(self.label, True, (180, 180, 180))
        surface.blit(lbl, (x + 3, y + 2))


# ─── DRAWING FUNCTIONS ───────────────────────────────────
def draw_sky(surface, alt):
    """Gradient sky that transitions to black space."""
    t = min(1.0, alt / 100000.0)
    for row in range(VIEW_H):
        frac = row / VIEW_H
        ground_col = lerp_color(C_SKY_TOP, C_SKY_BOT, frac)
        col = lerp_color(ground_col, C_SPACE, t)
        pygame.draw.line(surface, col, (0, row), (WIDTH, row))


def draw_stars(surface, alt):
    """Draw stars when high altitude."""
    if alt > 30000:
        brightness = min(255, int((alt - 30000) / 70000 * 255))
        random.seed(12345)
        for _ in range(120):
            sx = random.randint(0, WIDTH)
            sy = random.randint(0, VIEW_H)
            sz = random.randint(1, 3)
            pygame.draw.circle(surface, (brightness, brightness, brightness), (sx, sy), sz)


def draw_earth_curve(surface, cam_x, cam_y, zoom, alt):
    """Draw the curved Earth surface when at high altitude."""
    if alt > 20000:
        center_x, center_y = world_to_screen(0, 0, cam_x, cam_y, zoom)
        radius_px = int(EARTH_RADIUS * zoom)
        if radius_px > 5 and radius_px < 1e7:
            pygame.draw.circle(surface, C_GROUND, (center_x, center_y), radius_px)
            # Ocean layer
            pygame.draw.circle(surface, (30, 80, 140), (center_x, center_y), radius_px, 3)


def draw_ground_and_pad(surface, cam_x, cam_y, zoom):
    """Draw flat ground, launch pad, VAB, tower — all in screen space."""
    # Ground plane (extends far left and right)
    g_left_x, g_left_y = world_to_screen(-50000, EARTH_RADIUS, cam_x, cam_y, zoom)
    g_right_x, g_right_y = world_to_screen(50000, EARTH_RADIUS, cam_x, cam_y, zoom)
    ground_rect_h = VIEW_H - g_left_y
    if ground_rect_h > 0 and g_left_y < VIEW_H:
        pygame.draw.rect(surface, C_GROUND, (0, g_left_y, WIDTH, ground_rect_h + 10))
        # darker stripe
        pygame.draw.rect(surface, C_GROUND_DK, (0, g_left_y, WIDTH, max(2, int(3 * zoom))))

    # Pad
    def ws(wx, wy):
        return world_to_screen(wx, wy + EARTH_RADIUS, cam_x, cam_y, zoom)

    # Concrete pad
    pad_tl = ws(-25, 0)
    pad_br = ws(25, 4)
    pw = pad_br[0] - pad_tl[0]
    ph = pad_tl[1] - pad_br[1]
    if pw > 2:
        pygame.draw.rect(surface, C_PAD, (pad_tl[0], pad_br[1], pw, ph))

    # Flame trench
    tr_tl = ws(-8, -3)
    tr_br = ws(8, 0)
    tw_ = tr_br[0] - tr_tl[0]
    th = tr_tl[1] - tr_br[1]
    if tw_ > 1:
        pygame.draw.rect(surface, C_PAD_DARK, (tr_tl[0], tr_br[1], tw_, th))

    # Road
    rd_tl = ws(-6, -1)
    rd_br = ws(6, 0)
    rd_end = ws(-6, -1)
    rd_far = ws(6, -200)
    if abs(rd_tl[0] - rd_br[0]) > 1:
        pygame.draw.line(surface, C_ROAD, ws(-5, 0), ws(-5, -200), max(1, int(10 * zoom)))
        pygame.draw.line(surface, C_ROAD, ws(5, 0), ws(5, -200), max(1, int(10 * zoom)))

    # VAB building
    vab_bl = ws(-260, 0)
    vab_tr = ws(-140, 80)
    vw = vab_tr[0] - vab_bl[0]
    vh = vab_bl[1] - vab_tr[1]
    if vw > 3:
        pygame.draw.rect(surface, C_VAB, (vab_bl[0], vab_tr[1], vw, vh))
        # door
        dw = vw // 3
        dh = vh * 3 // 4
        pygame.draw.rect(surface, C_VAB_DOOR, (vab_bl[0] + vw // 2 - dw // 2, vab_tr[1] + vh - dh, dw, dh))

    # Service tower
    tw_bl = ws(10, 0)
    tw_tr = ws(16, 70)
    tww = tw_tr[0] - tw_bl[0]
    twh = tw_bl[1] - tw_tr[1]
    if tww > 1:
        pygame.draw.rect(surface, C_TOWER, (tw_bl[0], tw_tr[1], tww, twh))
        # arms
        arm1_l = ws(6, 40)
        arm1_r = ws(16, 43)
        aw = arm1_r[0] - arm1_l[0]
        ah = arm1_l[1] - arm1_r[1]
        if aw > 1:
            pygame.draw.rect(surface, C_TOWER, (arm1_l[0], arm1_r[1], aw, max(ah, 2)))
        arm2_l = ws(6, 25)
        arm2_r = ws(16, 28)
        aw2 = arm2_r[0] - arm2_l[0]
        ah2 = arm2_l[1] - arm2_r[1]
        if aw2 > 1:
            pygame.draw.rect(surface, C_TOWER, (arm2_l[0], arm2_r[1], aw2, max(ah2, 2)))

    # Lightning rods
    for lx in [-30, 30]:
        base = ws(lx, 0)
        top = ws(lx, 85)
        pygame.draw.line(surface, (180, 180, 180), base, top, max(1, int(1 * zoom)))


def draw_clouds(surface, cam_x, cam_y, zoom, cloud_data):
    """Draw simple cloud ellipses."""
    for cx, cy, cw, ch in cloud_data:
        sx, sy = world_to_screen(cx, cy + EARTH_RADIUS, cam_x, cam_y, zoom)
        pw = max(1, int(cw * zoom))
        ph = max(1, int(ch * zoom))
        if 0 < sx < WIDTH and 0 < sy < VIEW_H and pw < 2000:
            cloud_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.ellipse(cloud_surf, (*C_CLOUD, 140), (0, 0, pw, ph))
            surface.blit(cloud_surf, (sx - pw // 2, sy - ph // 2))


def draw_rocket(surface, rocket, cam_x, cam_y, zoom, phase):
    """Draw the Artemis-style SLS rocket."""
    alt = rocket.get_altitude()
    rx, ry = rocket.x, rocket.y
    pitch = rocket.pitch_angle

    def rotated_offset(dx, dy):
        """Rotate (dx, dy) by pitch angle and return world coords."""
        c = math.cos(pitch)
        s = math.sin(pitch)
        return rx + dx * (-s) + dy * c, ry + dx * c + dy * s

    def draw_part(dx, dy, w, h, color):
        """Draw a rotated rectangle representing a rocket part."""
        corners_local = [
            (-w / 2, 0), (w / 2, 0), (w / 2, h), (-w / 2, h)
        ]
        screen_corners = []
        for clx, cly in corners_local:
            wx, wy = rotated_offset(dx + clx, dy + cly)
            screen_corners.append(world_to_screen(wx, wy, cam_x, cam_y, zoom))
        pygame.draw.polygon(surface, color, screen_corners)

    def draw_triangle(dx, dy, w, h, color):
        """Draw a rotated triangle (nose cone / nozzle)."""
        pts_local = [(-w / 2, 0), (w / 2, 0), (0, h)]
        screen_pts = []
        for clx, cly in pts_local:
            wx, wy = rotated_offset(dx + clx, dy + cly)
            screen_pts.append(world_to_screen(wx, wy, cam_x, cam_y, zoom))
        pygame.draw.polygon(surface, color, screen_pts)

    # SRBs (only if stage 0)
    if rocket.current_stage_index == 0:
        for side in [-5.5, 5.5]:
            draw_part(side, 0, 3.6, 30, C_WHITE)
            draw_triangle(side, 30, 3.6, 4, C_WHITE)
            # SRB nozzle
            draw_triangle(side, -3, 2.4, -3, C_NOZZLE)

    # Core stage (orange) — present until stage index > 1
    if rocket.current_stage_index <= 1:
        draw_part(0, 0, 8.4, 42, C_ORANGE)
        # Core nozzles
        for nx in [-2, 0, 2]:
            draw_triangle(nx, -2, 1.6, -2.5, C_NOZZLE)

    # Upper stage (white)
    draw_part(0, 42, 7, 8, C_WHITE)

    # Orion capsule
    draw_part(0, 50, 5, 5, C_WHITE)
    draw_triangle(0, 55, 5, 5, C_WHITE)

    # LES needle
    tip_b = rotated_offset(0, 60)
    tip_t = rotated_offset(0, 64)
    sb = world_to_screen(*tip_b, cam_x, cam_y, zoom)
    st_ = world_to_screen(*tip_t, cam_x, cam_y, zoom)
    pygame.draw.line(surface, (150, 150, 150), sb, st_, max(1, int(0.3 * zoom)))

    # --- Flame ---
    is_active = (
        rocket.current_stage_index < len(rocket.stages)
        and rocket.stages[rocket.current_stage_index].active
    )
    if is_active and phase != FlightPhase.PRELAUNCH:
        vac_expand = 1.0 + min(alt / 40000.0, 3.0)
        flame_w = 4.0 * vac_expand
        if rocket.current_stage_index == 0:
            flame_w = 8.0 * vac_expand
        flame_l = random.uniform(15, 30) * vac_expand

        # Outer flame
        draw_triangle(0, -3, flame_w * 1.2, -flame_l, C_FLAME_OUT)
        # Middle flame
        draw_triangle(0, -3, flame_w * 0.7, -flame_l * 0.8, C_FLAME_MID)
        # Inner flame
        draw_triangle(0, -3, flame_w * 0.3, -flame_l * 0.6, C_FLAME_IN)


def draw_debris(surface, debris, cam_x, cam_y, zoom):
    """Draw separated stages tumbling."""
    for d in debris:
        sx, sy = world_to_screen(d["x"], d["y"], cam_x, cam_y, zoom)
        size = max(2, int(5 * zoom))
        pygame.draw.rect(surface, C_ORANGE, (sx - size, sy - size, size * 2, size))
        pygame.draw.rect(surface, C_NOZZLE, (sx - size // 2, sy, size, size // 2))


def draw_dashboard(surface, font, font_sm, rocket, world, graphs, traj_local, traj_orbit):
    """Draw the bottom telemetry dashboard."""
    dash_y = VIEW_H
    # Background
    pygame.draw.rect(surface, C_DASH_BG, (0, dash_y, WIDTH, DASH_H))
    pygame.draw.line(surface, C_DASH_LINE, (0, dash_y), (WIDTH, dash_y), 2)

    alt = rocket.get_altitude()
    vel = rocket.get_velocity_mag()

    # --- Left column: big readouts ---
    col_x = 15
    surface.blit(font.render(f"SPEED: {vel:.1f} m/s", True, C_GREEN_GO), (col_x, dash_y + 15))
    surface.blit(font.render(f"ALTITUDE: {alt:.1f} m", True, C_CYAN), (col_x, dash_y + 40))

    pitch_deg = math.degrees(rocket.pitch_angle) if hasattr(rocket, 'pitch_angle') else 90
    incl = max(0, 90.0 - pitch_deg)
    surface.blit(font_sm.render(f"G-LOAD: {graphs['gforce_val']:.2f}", True, C_MAGENTA), (col_x, dash_y + 65))
    surface.blit(font_sm.render(f"Inclination: {incl:.1f}\u00b0", True, C_TEXT), (col_x, dash_y + 85))
    surface.blit(font_sm.render(f"Mass: {rocket.get_total_mass():.0f} kg", True, C_TEXT), (col_x, dash_y + 105))

    # Stage indicator text
    stg = rocket.current_stage_index
    stg_name = rocket.stages[stg].name if stg < len(rocket.stages) else "COAST"
    surface.blit(font_sm.render(f"Stage: {stg_name}", True, C_YELLOW), (col_x, dash_y + 130))

    # --- Graphs ---
    gw, gh = 145, 130
    gx_start = 220
    gap = 10

    for i, key in enumerate(["alt", "vel", "maxq"]):
        gx = gx_start + i * (gw + gap)
        graphs[key].draw(surface, (gx, dash_y + 25, gw, gh), font_sm)

    # Trajectory plots
    tx = gx_start + 3 * (gw + gap)
    traj_local.draw(surface, (tx, dash_y + 25, gw, gh), font_sm)
    traj_orbit.draw(surface, (tx + gw + gap, dash_y + 25, gw, gh), font_sm)

    # --- System Health (rightmost) ---
    hx = tx + 2 * (gw + gap) + 10
    surface.blit(font.render("System Health", True, C_TEXT), (hx, dash_y + 15))
    systems = ["Avionics", "Propulsion", "Thermal", "Propellant", "Navigation", "Comms"]
    for i, name in enumerate(systems):
        sy_ = dash_y + 40 + i * 22
        surface.blit(font_sm.render(name, True, (170, 170, 170)), (hx, sy_))
        surface.blit(font_sm.render("GO", True, C_GREEN_GO), (hx + 95, sy_))


def draw_hud(surface, font, font_lg, world, phase):
    """Draw the top HUD overlay."""
    elapsed = world.time_elapsed
    warp = world.time_warp

    # Time
    time_str = f"T: {format_time(elapsed)} | WARP: {warp:.0f}x"
    surface.blit(font.render(time_str, True, C_TEXT), (15, 10))

    # Controls
    ctrl = "[Spacebar] LAUNCH  |  C CAMERA  |  \u2190/\u2192 WARP  |  R RESTART"
    ctrl_surf = font.render(ctrl, True, (180, 180, 180))
    surface.blit(ctrl_surf, (WIDTH // 2 - ctrl_surf.get_width() // 2, 10))

    # Phase box
    event_str = PHASE_NAMES.get(phase, "UNKNOWN")
    phase_map = {
        0: "T-MINUS (PRELAUNCH)", 1: "LIFTOFF",
        2: "MAX-Q (MAX DYNAMIC PRESSURE)", 3: "GRAVITY TURN",
        4: "SRB SEPARATION", 5: "FAIRING SEPARATION",
        6: "CORE SEP / STAGE 2", 7: "SECO (ORBITAL INSERTION)"
    }
    event_str = phase_map.get(phase, event_str)
    phase_surf = font_lg.render(f"  PHASE: {event_str}  ", True, C_YELLOW, (20, 20, 20))
    surface.blit(phase_surf, (WIDTH // 2 - phase_surf.get_width() // 2, 35))

    # Restart button
    pygame.draw.rect(surface, (50, 55, 65), (WIDTH - 110, 8, 100, 30), border_radius=4)
    pygame.draw.rect(surface, C_DASH_LINE, (WIDTH - 110, 8, 100, 30), 1, border_radius=4)
    surface.blit(font.render("RESTART", True, C_TEXT), (WIDTH - 100, 14))


# ─── MAIN APPLICATION ────────────────────────────────────
def run_app():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rocket Mission Simulator — Artemis II")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Menlo", 16)
    font_sm = pygame.font.SysFont("Menlo", 13)
    font_lg = pygame.font.SysFont("Menlo", 20, bold=True)

    # --- Generate cloud data once ---
    random.seed(42)
    clouds = []
    for _ in range(50):
        cx = random.uniform(-15000, 15000)
        cy = random.uniform(2000, 7000)
        cw = random.uniform(200, 800)
        ch = random.uniform(60, 200)
        clouds.append((cx, cy, cw, ch))

    def init_world():
        mission = MissionProfile("FALCON_9", "LEO")
        w = World(mission)
        w.time_warp = 1.0
        return w

    world = init_world()

    # Graphs
    g_alt = RollingGraph(max_pts=80, max_val=200, color=C_CYAN, label="Alt (km)")
    g_vel = RollingGraph(max_pts=80, max_val=8, color=(255, 130, 0), label="Vel (km/s)")
    g_q = RollingGraph(max_pts=80, max_val=50, color=C_RED, label="Max-Q (kPa)")
    traj_local = TrajectoryPlot(scale=500, color=C_YELLOW, label="Ascent Profile")
    traj_orbit = TrajectoryPlot(scale=15000, color=C_MAGENTA, label="Global Orbit", draw_earth=True)

    graph_timer = 0.0
    last_vel = 0.0
    gforce_val = 1.0

    cam_mode = 0
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if world.phase == FlightPhase.PRELAUNCH:
                        world.start()
                elif event.key == pygame.K_RIGHT:
                    if world.time_warp < 100:
                        world.time_warp *= 2
                elif event.key == pygame.K_LEFT:
                    if world.time_warp > 1:
                        world.time_warp /= 2
                elif event.key == pygame.K_c:
                    cam_mode = (cam_mode + 1) % 3
                elif event.key == pygame.K_r:
                    world = init_world()
                    g_alt = RollingGraph(max_pts=80, max_val=200, color=C_CYAN, label="Alt (km)")
                    g_vel = RollingGraph(max_pts=80, max_val=8, color=(255, 130, 0), label="Vel (km/s)")
                    g_q = RollingGraph(max_pts=80, max_val=50, color=C_RED, label="Max-Q (kPa)")
                    traj_local = TrajectoryPlot(scale=500, color=C_YELLOW, label="Ascent Profile")
                    traj_orbit = TrajectoryPlot(scale=15000, color=C_MAGENTA, label="Global Orbit", draw_earth=True)
                    last_vel = 0
                    gforce_val = 1.0
                    cam_mode = 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if WIDTH - 110 <= mx <= WIDTH - 10 and 8 <= my <= 38:
                    world = init_world()
                    g_alt = RollingGraph(max_pts=80, max_val=200, color=C_CYAN, label="Alt (km)")
                    g_vel = RollingGraph(max_pts=80, max_val=8, color=(255, 130, 0), label="Vel (km/s)")
                    g_q = RollingGraph(max_pts=80, max_val=50, color=C_RED, label="Max-Q (kPa)")
                    traj_local = TrajectoryPlot(scale=500, color=C_YELLOW, label="Ascent Profile")
                    traj_orbit = TrajectoryPlot(scale=15000, color=C_MAGENTA, label="Global Orbit", draw_earth=True)
                    last_vel = 0
                    gforce_val = 1.0
                    cam_mode = 0

        # --- Physics ---
        world.update(dt)
        rocket = world.rocket
        alt = rocket.get_altitude()
        vel = rocket.get_velocity_mag()

        # --- Camera ---
        if cam_mode == 0:
            if alt < 300:
                cam_x, cam_y = -30, EARTH_RADIUS + 40
                zoom = 3.0
            else:
                cam_x = rocket.x
                cam_y = rocket.y + 50
                zoom = max(0.3, 3.0 - alt / 5000.0)
        elif cam_mode == 1:
            cam_x = rocket.x
            cam_y = rocket.y
            zoom = max(0.01, 0.5 - alt / 200000.0)
        else:
            cam_x = rocket.x
            cam_y = rocket.y
            zoom = max(0.0001, 0.001 - alt / 50000000.0)

        zoom = max(zoom, 0.00005)

        # --- Graph updates (every 0.2s) ---
        graph_timer += dt
        if graph_timer >= 0.2:
            accel = (vel - last_vel) / graph_timer if graph_timer > 0 else 0
            last_vel = vel
            gforce_val = abs(accel / 9.81)
            if alt < 10:
                gforce_val = 1.0

            rho = 1.225 * math.exp(-alt / 8500.0) if alt > 0 else 1.225
            q = 0.5 * rho * vel ** 2

            g_alt.push(alt / 1000.0)
            g_vel.push(vel / 1000.0)
            g_q.push(q / 1000.0)
            traj_local.push(rocket.x, rocket.y)
            traj_orbit.push(rocket.x, rocket.y)
            graph_timer = 0.0

        # ─── DRAW ─────────────────────────────────────
        draw_sky(screen, alt)
        draw_stars(screen, alt)

        # At very high alt, draw curved Earth
        if alt > 20000:
            draw_earth_curve(screen, cam_x, cam_y, zoom, alt)
        else:
            draw_ground_and_pad(screen, cam_x, cam_y, zoom)
            draw_clouds(screen, cam_x, cam_y, zoom, clouds)

        draw_debris(screen, world.debris, cam_x, cam_y, zoom)
        draw_rocket(screen, rocket, cam_x, cam_y, zoom, world.phase)

        graphs_dict = {"alt": g_alt, "vel": g_vel, "maxq": g_q, "gforce_val": gforce_val}
        draw_dashboard(screen, font, font_sm, rocket, world, graphs_dict, traj_local, traj_orbit)
        draw_hud(screen, font, font_lg, world, world.phase)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
