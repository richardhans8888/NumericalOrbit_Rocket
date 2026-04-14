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
WIDTH, HEIGHT = 1440, 900
DASH_H = 280  # taller dashboard
VIEW_H = HEIGHT - DASH_H
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
C_OCEAN      = (20, 55, 100)
C_LAND1      = (60, 130, 45)
C_LAND2      = (90, 150, 60)
C_LAND3      = (45, 100, 35)
C_DESERT     = (170, 150, 100)
C_ICE        = (210, 225, 240)


# ─── UTILITIES ────────────────────────────────────────────
def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def world_to_screen(wx, wy, cam_x, cam_y, zoom):
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
        pygame.draw.rect(surface, (22, 28, 38), rect)
        pygame.draw.rect(surface, C_DASH_LINE, rect, 1)
        for i in range(1, 4):
            ly = y + h - int(h * i / 4)
            pygame.draw.line(surface, (30, 35, 45), (x, ly), (x + w, ly))
        if len(self.data) > 1:
            pts = []
            step = w / (len(self.data) - 1)
            for i, v in enumerate(self.data):
                px = x + int(i * step)
                frac = min(v / self.max_val, 1.0) if self.max_val > 0 else 0
                py = y + h - int(frac * (h - 4)) - 2
                pts.append((px, py))
            pygame.draw.lines(surface, self.color, False, pts, 2)
        lbl = font.render(self.label, True, (170, 170, 170))
        surface.blit(lbl, (x + 3, y + 2))
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
        pygame.draw.rect(surface, (18, 22, 32), rect)
        pygame.draw.rect(surface, C_DASH_LINE, rect, 1)
        cx, cy = x + w // 2, y + h // 2
        if self.draw_earth:
            er = (EARTH_RADIUS / 1000.0) / self.scale * (w / 2)
            if er > 2:
                pygame.draw.circle(surface, (20, 50, 80), (cx, cy), int(er))
                pygame.draw.circle(surface, (30, 80, 120), (cx, cy), int(er), 1)
        if len(self.pts) > 1:
            screen_pts = []
            for kx, ky in self.pts:
                if self.draw_earth:
                    sx = cx + int((kx / self.scale) * (w / 2))
                    sy = cy - int((ky / self.scale) * (h / 2))
                else:
                    sx = x + int((kx / self.scale) * w) + w // 2
                    sy = y + h - int(((ky - EARTH_RADIUS / 1000.0) / self.scale) * h)
                screen_pts.append((max(x, min(x + w, sx)), max(y, min(y + h, sy))))
            if len(screen_pts) > 1:
                pygame.draw.lines(surface, self.color, False, screen_pts, 2)
        lbl = font.render(self.label, True, (170, 170, 170))
        surface.blit(lbl, (x + 3, y + 2))


# ─── DRAWING FUNCTIONS ───────────────────────────────────
def draw_sky(surface, alt):
    t = min(1.0, alt / 100000.0)
    for row in range(VIEW_H):
        frac = row / VIEW_H
        ground_col = lerp_color(C_SKY_TOP, C_SKY_BOT, frac)
        col = lerp_color(ground_col, C_SPACE, t)
        pygame.draw.line(surface, col, (0, row), (WIDTH, row))


def draw_stars(surface, alt):
    if alt > 30000:
        brightness = min(255, int((alt - 30000) / 70000 * 255))
        random.seed(12345)
        for _ in range(150):
            sx = random.randint(0, WIDTH)
            sy = random.randint(0, VIEW_H)
            sz = random.randint(1, 3)
            pygame.draw.circle(surface, (brightness, brightness, brightness), (sx, sy), sz)


def draw_earth_detailed(surface, cam_x, cam_y, zoom, alt):
    """Detailed Earth with continent patches, ice caps, and atmosphere glow."""
    center_x, center_y = world_to_screen(0, 0, cam_x, cam_y, zoom)
    radius_px = int(EARTH_RADIUS * zoom)

    if radius_px < 5 or radius_px > 5e6:
        return

    # Atmosphere glow (3 layers)
    for i in range(3):
        glow_r = radius_px + int(radius_px * 0.03 * (3 - i))
        alpha = 30 + i * 20
        glow_col = (60 + i * 30, 120 + i * 30, 200 + i * 15)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*glow_col, alpha), (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (center_x - glow_r, center_y - glow_r))

    # Ocean base
    pygame.draw.circle(surface, C_OCEAN, (center_x, center_y), radius_px)

    # Continent patches — procedural landmasses at fixed angles
    random.seed(999)
    continents = [
        (0.15, 0.3, 0.25, 0.35, C_LAND1),     # North America-ish
        (-0.1, -0.2, 0.2, 0.25, C_LAND2),      # South America-ish
        (0.5, 0.25, 0.15, 0.30, C_LAND1),       # Europe/Africa-ish
        (0.55, -0.1, 0.12, 0.20, C_DESERT),     # Sahara
        (0.8, 0.15, 0.20, 0.15, C_LAND3),       # Asia-ish
        (-0.3, 0.1, 0.12, 0.08, C_LAND2),       # Pacific islands
        (0.0, -0.6, 0.3, 0.1, C_ICE),           # Antarctica
        (0.0, 0.65, 0.15, 0.08, C_ICE),         # Arctic
    ]
    for cx_frac, cy_frac, w_frac, h_frac, color in continents:
        lx = center_x + int(cx_frac * radius_px) - int(w_frac * radius_px / 2)
        ly = center_y - int(cy_frac * radius_px) - int(h_frac * radius_px / 2)
        lw = max(2, int(w_frac * radius_px))
        lh = max(2, int(h_frac * radius_px))
        # Clip to circle using ellipse
        land_surf = pygame.Surface((lw, lh), pygame.SRCALPHA)
        pygame.draw.ellipse(land_surf, (*color, 220), (0, 0, lw, lh))
        surface.blit(land_surf, (lx, ly))

    # Outline
    pygame.draw.circle(surface, (60, 130, 200), (center_x, center_y), radius_px, 2)


def draw_ground_and_pad(surface, cam_x, cam_y, zoom):
    g_left_x, g_left_y = world_to_screen(-50000, EARTH_RADIUS, cam_x, cam_y, zoom)
    ground_rect_h = VIEW_H - g_left_y
    if ground_rect_h > 0 and g_left_y < VIEW_H:
        pygame.draw.rect(surface, C_GROUND, (0, g_left_y, WIDTH, ground_rect_h + 10))
        pygame.draw.rect(surface, C_GROUND_DK, (0, g_left_y, WIDTH, max(2, int(3 * zoom))))

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
    if abs(ws(-5, 0)[0] - ws(5, 0)[0]) > 1:
        pygame.draw.line(surface, C_ROAD, ws(-5, 0), ws(-5, -200), max(1, int(10 * zoom)))
        pygame.draw.line(surface, C_ROAD, ws(5, 0), ws(5, -200), max(1, int(10 * zoom)))

    # VAB
    vab_bl = ws(-260, 0)
    vab_tr = ws(-140, 80)
    vw = vab_tr[0] - vab_bl[0]
    vh = vab_bl[1] - vab_tr[1]
    if vw > 3:
        pygame.draw.rect(surface, C_VAB, (vab_bl[0], vab_tr[1], vw, vh))
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
        for arm_y in [25, 40]:
            al = ws(6, arm_y)
            ar = ws(16, arm_y + 3)
            aw = ar[0] - al[0]
            ah = al[1] - ar[1]
            if aw > 1:
                pygame.draw.rect(surface, C_TOWER, (al[0], ar[1], aw, max(ah, 2)))

    # Lightning rods
    for lx in [-30, 30]:
        base = ws(lx, 0)
        top = ws(lx, 85)
        pygame.draw.line(surface, (180, 180, 180), base, top, max(1, int(1 * zoom)))


def draw_clouds(surface, cam_x, cam_y, zoom, cloud_data):
    for cx, cy, cw, ch in cloud_data:
        sx, sy = world_to_screen(cx, cy + EARTH_RADIUS, cam_x, cam_y, zoom)
        pw = max(1, int(cw * zoom))
        ph = max(1, int(ch * zoom))
        if 0 < sx < WIDTH and 0 < sy < VIEW_H and pw < 2000:
            cloud_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.ellipse(cloud_surf, (*C_CLOUD, 130), (0, 0, pw, ph))
            surface.blit(cloud_surf, (sx - pw // 2, sy - ph // 2))


def draw_rocket(surface, rocket, cam_x, cam_y, zoom, phase):
    alt = rocket.get_altitude()
    rx, ry = rocket.x, rocket.y
    pitch = rocket.pitch_angle

    def rotated_offset(dx, dy):
        c = math.cos(pitch)
        s = math.sin(pitch)
        return rx + dx * (-s) + dy * c, ry + dx * c + dy * s

    def draw_part(dx, dy, w, h, color):
        corners = [(-w / 2, 0), (w / 2, 0), (w / 2, h), (-w / 2, h)]
        sc = [world_to_screen(*rotated_offset(dx + cx, dy + cy), cam_x, cam_y, zoom) for cx, cy in corners]
        pygame.draw.polygon(surface, color, sc)
        pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in color), sc, 1)

    def draw_triangle(dx, dy, w, h, color):
        pts = [(-w / 2, 0), (w / 2, 0), (0, h)]
        sc = [world_to_screen(*rotated_offset(dx + cx, dy + cy), cam_x, cam_y, zoom) for cx, cy in pts]
        pygame.draw.polygon(surface, color, sc)

    # SRBs
    if rocket.current_stage_index == 0:
        for side in [-5.5, 5.5]:
            draw_part(side, 0, 3.6, 30, C_WHITE)
            draw_triangle(side, 30, 3.6, 4, C_WHITE)
            draw_triangle(side, -3, 2.4, -3, C_NOZZLE)

    # Core
    if rocket.current_stage_index <= 1:
        draw_part(0, 0, 8.4, 42, C_ORANGE)
        for nx in [-2, 0, 2]:
            draw_triangle(nx, -2, 1.6, -2.5, C_NOZZLE)

    # Upper stage
    draw_part(0, 42, 7, 8, C_WHITE)
    # Orion
    draw_part(0, 50, 5, 5, C_WHITE)
    draw_triangle(0, 55, 5, 5, C_WHITE)
    # LES needle
    sb = world_to_screen(*rotated_offset(0, 60), cam_x, cam_y, zoom)
    st_ = world_to_screen(*rotated_offset(0, 64), cam_x, cam_y, zoom)
    pygame.draw.line(surface, (150, 150, 150), sb, st_, max(1, int(0.3 * zoom)))

    # Flame
    is_active = (rocket.current_stage_index < len(rocket.stages) and rocket.stages[rocket.current_stage_index].active)
    if is_active and phase != FlightPhase.PRELAUNCH:
        vac_expand = 1.0 + min(alt / 40000.0, 3.0)
        flame_w = 4.0 * vac_expand
        if rocket.current_stage_index == 0:
            flame_w = 8.0 * vac_expand
        flame_l = random.uniform(15, 30) * vac_expand
        draw_triangle(0, -3, flame_w * 1.2, -flame_l, C_FLAME_OUT)
        draw_triangle(0, -3, flame_w * 0.7, -flame_l * 0.8, C_FLAME_MID)
        draw_triangle(0, -3, flame_w * 0.3, -flame_l * 0.6, C_FLAME_IN)


def draw_debris(surface, debris, cam_x, cam_y, zoom):
    for d in debris:
        sx, sy = world_to_screen(d["x"], d["y"], cam_x, cam_y, zoom)
        size = max(2, int(5 * zoom))
        pygame.draw.rect(surface, C_ORANGE, (sx - size, sy - size, size * 2, size))
        pygame.draw.rect(surface, C_NOZZLE, (sx - size // 2, sy, size, size // 2))


def draw_dashboard(surface, font, font_sm, font_tiny, rocket, world, graphs, traj_local, traj_orbit):
    dash_y = VIEW_H
    pygame.draw.rect(surface, C_DASH_BG, (0, dash_y, WIDTH, DASH_H))
    pygame.draw.line(surface, C_DASH_LINE, (0, dash_y), (WIDTH, dash_y), 2)

    alt = rocket.get_altitude()
    vel = rocket.get_velocity_mag()
    pitch_deg = math.degrees(rocket.pitch_angle) if hasattr(rocket, 'pitch_angle') else 90
    incl = max(0, 90.0 - pitch_deg)
    stg = rocket.current_stage_index
    stg_name = rocket.stages[stg].name if stg < len(rocket.stages) else "COAST"

    # --- Left column: readouts ---
    col_x = 12
    ly = dash_y + 8
    surface.blit(font.render(f"SPEED: {vel:.1f} m/s", True, C_GREEN_GO), (col_x, ly)); ly += 22
    surface.blit(font.render(f"ALT: {alt:.1f} m", True, C_CYAN), (col_x, ly)); ly += 22
    surface.blit(font_sm.render(f"G-LOAD: {graphs['gforce_val']:.2f}", True, C_MAGENTA), (col_x, ly)); ly += 18
    surface.blit(font_sm.render(f"Pitch: {pitch_deg:.1f}\u00b0", True, C_TEXT), (col_x, ly)); ly += 18
    surface.blit(font_sm.render(f"Incl: {incl:.1f}\u00b0", True, C_TEXT), (col_x, ly)); ly += 18
    surface.blit(font_sm.render(f"Mass: {rocket.get_total_mass():.0f} kg", True, C_TEXT), (col_x, ly)); ly += 18
    surface.blit(font_sm.render(f"Stage: {stg_name}", True, C_YELLOW), (col_x, ly)); ly += 18
    # Fuel remaining
    if stg < len(rocket.stages):
        fuel_pct = rocket.stages[stg].fuel_system.fuel / (rocket.stages[stg].fuel_system.fuel + rocket.stages[stg].fuel_system.consumed + 0.001) * 100
        bar_w = 100
        bar_h = 12
        pygame.draw.rect(surface, (40, 40, 40), (col_x, ly, bar_w, bar_h))
        fill_w = int(bar_w * fuel_pct / 100)
        bar_color = C_GREEN_GO if fuel_pct > 30 else C_YELLOW if fuel_pct > 10 else C_RED
        pygame.draw.rect(surface, bar_color, (col_x, ly, fill_w, bar_h))
        pygame.draw.rect(surface, C_DASH_LINE, (col_x, ly, bar_w, bar_h), 1)
        surface.blit(font_tiny.render(f"FUEL {fuel_pct:.0f}%", True, C_TEXT), (col_x + bar_w + 5, ly))

    # --- Controls info ---
    ctrl_y = dash_y + DASH_H - 22
    ctrl_txt = "W/S Pitch | \u2190/\u2192 Warp | Space Launch | C Cam | R Reset"
    surface.blit(font_tiny.render(ctrl_txt, True, (120, 120, 120)), (col_x, ctrl_y))

    # --- Row 1 graphs ---
    gw = 155
    gh_top = 105
    gh_bot = 105
    gx_start = 170
    gap = 8

    row1_y = dash_y + 10
    row2_y = dash_y + 10 + gh_top + 8

    # Row 1: Alt, Vel, Max-Q, G-Force
    for i, key in enumerate(["alt", "vel", "maxq", "gforce"]):
        gx = gx_start + i * (gw + gap)
        graphs[key].draw(surface, (gx, row1_y, gw, gh_top), font_tiny)

    # Row 2: Thrust, Fuel, Ascent Profile, Global Orbit
    for i, key in enumerate(["thrust", "fuel_graph"]):
        gx = gx_start + i * (gw + gap)
        graphs[key].draw(surface, (gx, row2_y, gw, gh_bot), font_tiny)

    tx = gx_start + 2 * (gw + gap)
    traj_local.draw(surface, (tx, row2_y, gw, gh_bot), font_tiny)
    traj_orbit.draw(surface, (tx + gw + gap, row2_y, gw, gh_bot), font_tiny)

    # --- System Health (rightmost) ---
    hx = gx_start + 4 * (gw + gap) + 10
    surface.blit(font.render("System Health", True, C_TEXT), (hx, row1_y))
    systems = ["Avionics", "Propulsion", "Thermal", "Propellant", "Navigation", "Comms"]
    for i, name in enumerate(systems):
        sy_ = row1_y + 22 + i * 20
        surface.blit(font_sm.render(name, True, (160, 160, 160)), (hx, sy_))
        surface.blit(font_sm.render("GO", True, C_GREEN_GO), (hx + 100, sy_))

    # Phase under health
    phase_names_short = {
        0: "PRE", 1: "LIFT", 2: "MAX-Q", 3: "G-TURN",
        4: "SRB SEP", 5: "FAIR SEP", 6: "STG 2", 7: "SECO"
    }
    phase_str = phase_names_short.get(world.phase, "?")
    surface.blit(font.render(f"PHASE: {phase_str}", True, C_YELLOW), (hx, row2_y + 10))
    surface.blit(font_sm.render(f"T: {format_time(world.time_elapsed)}", True, C_TEXT), (hx, row2_y + 35))
    surface.blit(font_sm.render(f"Warp: {world.time_warp:.0f}x", True, C_TEXT), (hx, row2_y + 55))
    # Downrange
    downrange = abs(rocket.x) / 1000.0
    surface.blit(font_sm.render(f"Range: {downrange:.1f} km", True, C_TEXT), (hx, row2_y + 75))


def draw_hud(surface, font, font_lg, world, phase):
    elapsed = world.time_elapsed
    warp = world.time_warp

    time_str = f"T: {format_time(elapsed)} | WARP: {warp:.0f}x"
    surface.blit(font.render(time_str, True, C_TEXT), (15, 8))

    phase_map = {
        0: "T-MINUS (PRELAUNCH)", 1: "LIFTOFF",
        2: "MAX-Q (MAX DYNAMIC PRESSURE)", 3: "GRAVITY TURN",
        4: "SRB SEPARATION", 5: "FAIRING SEPARATION",
        6: "CORE SEP / STAGE 2", 7: "SECO (ORBITAL INSERTION)"
    }
    event_str = phase_map.get(phase, PHASE_NAMES.get(phase, "UNKNOWN"))
    phase_surf = font_lg.render(f"  PHASE: {event_str}  ", True, C_YELLOW, (15, 15, 20))
    surface.blit(phase_surf, (WIDTH // 2 - phase_surf.get_width() // 2, 30))

    # Restart button
    pygame.draw.rect(surface, (50, 55, 65), (WIDTH - 115, 6, 105, 28), border_radius=4)
    pygame.draw.rect(surface, C_DASH_LINE, (WIDTH - 115, 6, 105, 28), 1, border_radius=4)
    surface.blit(font.render("RESTART", True, C_TEXT), (WIDTH - 105, 10))


# ─── MAIN APPLICATION ────────────────────────────────────
def run_app():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rocket Mission Simulator \u2014 Artemis II")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Menlo", 15)
    font_sm = pygame.font.SysFont("Menlo", 12)
    font_lg = pygame.font.SysFont("Menlo", 18, bold=True)
    font_tiny = pygame.font.SysFont("Menlo", 11)

    random.seed(42)
    clouds = [(random.uniform(-15000, 15000), random.uniform(2000, 7000),
               random.uniform(200, 800), random.uniform(60, 200)) for _ in range(50)]

    def init_world():
        mission = MissionProfile("FALCON_9", "LEO")
        w = World(mission)
        w.time_warp = 1.0
        return w

    def make_graphs():
        return {
            "alt": RollingGraph(max_pts=80, max_val=200, color=C_CYAN, label="Alt (km)"),
            "vel": RollingGraph(max_pts=80, max_val=8, color=(255, 130, 0), label="Vel (km/s)"),
            "maxq": RollingGraph(max_pts=80, max_val=50, color=C_RED, label="Max-Q (kPa)"),
            "gforce": RollingGraph(max_pts=80, max_val=5, color=C_MAGENTA, label="G-Force"),
            "thrust": RollingGraph(max_pts=80, max_val=40000, color=C_YELLOW, label="Thrust (kN)"),
            "fuel_graph": RollingGraph(max_pts=80, max_val=100, color=C_GREEN_GO, label="Fuel (%)"),
            "gforce_val": 1.0,
        }

    world = init_world()
    graphs = make_graphs()
    traj_local = TrajectoryPlot(scale=500, color=C_YELLOW, label="Ascent Profile")
    traj_orbit = TrajectoryPlot(scale=15000, color=C_MAGENTA, label="Global Orbit", draw_earth=True)

    graph_timer = 0.0
    last_vel = 0.0
    cam_mode = 0
    manual_pitch_offset = 0.0
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

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
                    graphs = make_graphs()
                    traj_local = TrajectoryPlot(scale=500, color=C_YELLOW, label="Ascent Profile")
                    traj_orbit = TrajectoryPlot(scale=15000, color=C_MAGENTA, label="Global Orbit", draw_earth=True)
                    last_vel = 0
                    cam_mode = 0
                    manual_pitch_offset = 0.0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if WIDTH - 115 <= mx <= WIDTH - 10 and 6 <= my <= 34:
                    world = init_world()
                    graphs = make_graphs()
                    traj_local = TrajectoryPlot(scale=500, color=C_YELLOW, label="Ascent Profile")
                    traj_orbit = TrajectoryPlot(scale=15000, color=C_MAGENTA, label="Global Orbit", draw_earth=True)
                    last_vel = 0
                    cam_mode = 0
                    manual_pitch_offset = 0.0

        # Continuous key input for pitch control
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            manual_pitch_offset += 0.5 * dt
        if keys[pygame.K_s]:
            manual_pitch_offset -= 0.5 * dt
        manual_pitch_offset = max(-0.5, min(0.5, manual_pitch_offset))

        # Apply manual pitch offset
        if world.phase != FlightPhase.PRELAUNCH:
            world.rocket.pitch_angle += manual_pitch_offset * dt * 2

        # Physics
        world.update(dt)
        rocket = world.rocket
        alt = rocket.get_altitude()
        vel = rocket.get_velocity_mag()

        # Camera
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

        # Graph updates
        graph_timer += dt
        if graph_timer >= 0.2:
            accel = (vel - last_vel) / graph_timer if graph_timer > 0 else 0
            last_vel = vel
            gforce_val = abs(accel / 9.81)
            if alt < 10:
                gforce_val = 1.0
            graphs["gforce_val"] = gforce_val

            rho = 1.225 * math.exp(-alt / 8500.0) if alt > 0 else 1.225
            q = 0.5 * rho * vel ** 2

            graphs["alt"].push(alt / 1000.0)
            graphs["vel"].push(vel / 1000.0)
            graphs["maxq"].push(q / 1000.0)
            graphs["gforce"].push(gforce_val)

            # Thrust
            stg = rocket.current_stage_index
            if stg < len(rocket.stages) and rocket.stages[stg].active:
                t_kn = rocket.stages[stg].thrust_sl / 1000.0
            else:
                t_kn = 0
            graphs["thrust"].push(t_kn)

            # Fuel %
            if stg < len(rocket.stages):
                fs = rocket.stages[stg].fuel_system
                fuel_pct = fs.fuel / (fs.fuel + fs.consumed + 0.001) * 100
            else:
                fuel_pct = 0
            graphs["fuel_graph"].push(fuel_pct)

            traj_local.push(rocket.x, rocket.y)
            traj_orbit.push(rocket.x, rocket.y)
            graph_timer = 0.0

        # ─── DRAW ─────────────────────────────────────
        draw_sky(screen, alt)
        draw_stars(screen, alt)

        if alt > 20000:
            draw_earth_detailed(screen, cam_x, cam_y, zoom, alt)
        else:
            draw_ground_and_pad(screen, cam_x, cam_y, zoom)
            draw_clouds(screen, cam_x, cam_y, zoom, clouds)

        draw_debris(screen, world.debris, cam_x, cam_y, zoom)
        draw_rocket(screen, rocket, cam_x, cam_y, zoom, world.phase)

        draw_dashboard(screen, font, font_sm, font_tiny, rocket, world, graphs, traj_local, traj_orbit)
        draw_hud(screen, font, font_lg, world, world.phase)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
