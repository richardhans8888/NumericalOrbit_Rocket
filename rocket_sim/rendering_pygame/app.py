# rendering_pygame/app.py
"""
Pygame-based rocket mission simulator renderer.
Optimized for 60 FPS with pre-cached sky gradient and efficient cloud rendering.
"""
import pygame
import sys
import math
import random
import collections
from mission.mission_profile import MissionProfile
from mission.flight_phases import FlightPhase, PHASE_NAMES
from mission.telemetry import format_time
from simulation.world import World
from physics.constants import EARTH_RADIUS, G, EARTH_MASS

# ─── LAYOUT ──────────────────────────────────────────────
WIDTH, HEIGHT = 1440, 900
SIDE_W = 180
DASH_H = 280
VIEW_X = SIDE_W
VIEW_W = WIDTH - SIDE_W
VIEW_H = HEIGHT - DASH_H
FPS = 60

MOON_DISTANCE = 384400000.0
MOON_RADIUS = 1737000.0

# ─── COLORS ──────────────────────────────────────────────
C_GROUND    = (72, 140, 50)
C_GROUND_DK = (55, 110, 38)
C_PAD       = (140, 140, 135)
C_PAD_DARK  = (80, 80, 80)
C_ROAD      = (90, 90, 90)
C_TOWER     = (160, 150, 140)
C_VAB       = (110, 115, 130)
C_VAB_DOOR  = (70, 75, 85)
C_ORANGE    = (225, 120, 20)
C_WHITE     = (240, 240, 235)
C_NOZZLE    = (60, 60, 65)
C_FLAME_IN  = (255, 255, 180)
C_FLAME_MID = (255, 200, 50)
C_FLAME_OUT = (255, 100, 20)
C_DASH_BG   = (15, 20, 28)
C_SIDE_BG   = (12, 16, 24)
C_DASH_LINE = (50, 60, 80)
C_TEXT      = (220, 220, 220)
C_GREEN_GO  = (30, 255, 80)
C_CYAN      = (0, 200, 255)
C_YELLOW    = (255, 255, 60)
C_MAGENTA   = (210, 60, 210)
C_RED       = (255, 50, 50)
C_OCEAN     = (20, 55, 100)
C_LAND1     = (60, 130, 45)
C_LAND2     = (90, 150, 60)
C_LAND3     = (45, 100, 35)
C_DESERT    = (170, 150, 100)
C_ICE       = (210, 225, 240)
C_MOON      = (180, 180, 175)


def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def world_to_screen(wx, wy, cam_x, cam_y, zoom):
    sx = VIEW_X + VIEW_W // 2 + (wx - cam_x) * zoom
    sy = VIEW_H // 2 - (wy - cam_y) * zoom
    return int(sx), int(sy)


# ─── PRE-CACHED SKY ─────────────────────────────────────
def build_sky_cache():
    """Pre-render 11 sky gradient surfaces for altitude bands."""
    skies = []
    for level in range(11):
        t = level / 10.0
        surf = pygame.Surface((VIEW_W, VIEW_H))
        for row in range(0, VIEW_H, 4):  # every 4th pixel for speed
            frac = row / VIEW_H
            sky_top = (30, 60, 120)
            sky_bot = (120, 170, 230)
            space = (5, 5, 15)
            ground_col = lerp_color(sky_top, sky_bot, frac)
            col = lerp_color(ground_col, space, t)
            pygame.draw.rect(surf, col, (0, row, VIEW_W, 4))
        skies.append(surf)
    return skies


def get_sky_index(alt):
    return min(10, int(alt / 10000.0))


# ─── GRAPH ───────────────────────────────────────────────
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


# ─── SCENE DRAWING ───────────────────────────────────────
def draw_stars(surface, alt):
    if alt > 20000:
        brightness = min(255, int((alt - 20000) / 80000 * 255))
        random.seed(12345)
        for _ in range(150):
            sx = random.randint(VIEW_X, WIDTH)
            sy = random.randint(0, VIEW_H)
            sz = random.randint(1, 2)
            pygame.draw.circle(surface, (brightness, brightness, brightness), (sx, sy), sz)


def draw_moon(surface, cam_x, cam_y, zoom):
    mx, my = world_to_screen(MOON_DISTANCE, 0, cam_x, cam_y, zoom)
    mr = max(2, int(MOON_RADIUS * zoom))
    if mr < 500000 and VIEW_X - mr < mx < WIDTH + mr and -mr < my < VIEW_H + mr:
        pygame.draw.circle(surface, C_MOON, (mx, my), mr)
        if mr > 6:
            for dx, dy, cr in [(0.2, 0.1, 0.15), (-0.3, -0.2, 0.1), (0.1, -0.3, 0.12)]:
                pygame.draw.circle(surface, (160, 160, 155),
                                   (mx + int(dx * mr), my + int(dy * mr)), max(1, int(cr * mr)), 1)


def draw_earth_detailed(surface, cam_x, cam_y, zoom):
    cx, cy = world_to_screen(0, 0, cam_x, cam_y, zoom)
    rp = int(EARTH_RADIUS * zoom)
    if rp < 5 or rp > 2e6:
        return
    # Atmosphere glow
    for i in range(2):
        gr = rp + int(rp * 0.02 * (2 - i))
        if gr < 3000:
            pygame.draw.circle(surface, (40 + i * 40, 100 + i * 40, 180 + i * 20), (cx, cy), gr, 3)
    pygame.draw.circle(surface, C_OCEAN, (cx, cy), rp)
    continents = [
        (0.15, 0.3, 0.25, 0.35, C_LAND1), (-0.1, -0.2, 0.2, 0.25, C_LAND2),
        (0.5, 0.25, 0.15, 0.30, C_LAND1), (0.55, -0.1, 0.12, 0.20, C_DESERT),
        (0.8, 0.15, 0.20, 0.15, C_LAND3), (0.0, -0.6, 0.3, 0.1, C_ICE),
        (0.0, 0.65, 0.15, 0.08, C_ICE),
    ]
    for cfx, cfy, wf, hf, col in continents:
        lx = cx + int(cfx * rp) - int(wf * rp / 2)
        ly = cy - int(cfy * rp) - int(hf * rp / 2)
        lw = max(2, int(wf * rp))
        lh = max(2, int(hf * rp))
        if lw < 2000 and lh < 2000:
            s = pygame.Surface((lw, lh), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*col, 200), (0, 0, lw, lh))
            surface.blit(s, (lx, ly))
    pygame.draw.circle(surface, (60, 130, 200), (cx, cy), rp, 2)


def draw_ground_and_pad(surface, cam_x, cam_y, zoom):
    _, gy = world_to_screen(-50000, EARTH_RADIUS, cam_x, cam_y, zoom)
    gh = VIEW_H - gy
    if gh > 0 and gy < VIEW_H:
        pygame.draw.rect(surface, C_GROUND, (VIEW_X, gy, VIEW_W, gh + 10))
        pygame.draw.rect(surface, C_GROUND_DK, (VIEW_X, gy, VIEW_W, max(2, int(3 * zoom))))

    def ws(wx, wy):
        return world_to_screen(wx, wy + EARTH_RADIUS, cam_x, cam_y, zoom)

    p1 = ws(-25, 0); p2 = ws(25, 4)
    pw = p2[0] - p1[0]; ph = p1[1] - p2[1]
    if pw > 2:
        pygame.draw.rect(surface, C_PAD, (p1[0], p2[1], pw, ph))
    t1 = ws(-8, -3); t2 = ws(8, 0)
    tw = t2[0] - t1[0]; th = t1[1] - t2[1]
    if tw > 1:
        pygame.draw.rect(surface, C_PAD_DARK, (t1[0], t2[1], tw, th))
    if abs(ws(-5, 0)[0] - ws(5, 0)[0]) > 1:
        pygame.draw.line(surface, C_ROAD, ws(-5, 0), ws(-5, -200), max(1, int(10 * zoom)))
        pygame.draw.line(surface, C_ROAD, ws(5, 0), ws(5, -200), max(1, int(10 * zoom)))
    v1 = ws(-260, 0); v2 = ws(-140, 80)
    vw = v2[0] - v1[0]; vh = v1[1] - v2[1]
    if vw > 3:
        pygame.draw.rect(surface, C_VAB, (v1[0], v2[1], vw, vh))
        pygame.draw.rect(surface, C_VAB_DOOR, (v1[0] + vw // 3, v2[1] + vh // 4, vw // 3, vh * 3 // 4))
    tw1 = ws(10, 0); tw2 = ws(16, 70)
    tww = tw2[0] - tw1[0]; twh = tw1[1] - tw2[1]
    if tww > 1:
        pygame.draw.rect(surface, C_TOWER, (tw1[0], tw2[1], tww, twh))
        for ay in [25, 40]:
            a1 = ws(6, ay); a2 = ws(16, ay + 3)
            aw = a2[0] - a1[0]
            if aw > 1:
                pygame.draw.rect(surface, C_TOWER, (a1[0], a2[1], aw, max(a1[1] - a2[1], 2)))
    for lx in [-30, 30]:
        pygame.draw.line(surface, (180, 180, 180), ws(lx, 0), ws(lx, 85), max(1, int(zoom)))


def draw_clouds_simple(surface, cam_x, cam_y, zoom, cloud_data):
    """Draw clouds as simple filled ellipses — no alpha surfaces."""
    for cx, cy, cw, ch in cloud_data:
        sx, sy = world_to_screen(cx, cy + EARTH_RADIUS, cam_x, cam_y, zoom)
        pw = int(cw * zoom)
        ph = int(ch * zoom)
        if 2 < pw < 1500 and VIEW_X < sx < WIDTH and 0 < sy < VIEW_H:
            pygame.draw.ellipse(surface, (235, 240, 250), (sx - pw // 2, sy - ph // 2, pw, ph))


def draw_rocket(surface, rocket, cam_x, cam_y, zoom, phase):
    alt = rocket.get_altitude()
    rx, ry = rocket.x, rocket.y
    pitch = rocket.pitch_angle

    def ro(dx, dy):
        c = math.cos(pitch); s = math.sin(pitch)
        return rx + dx * (-s) + dy * c, ry + dx * c + dy * s

    def draw_part(dx, dy, w, h, color):
        corners = [(-w / 2, 0), (w / 2, 0), (w / 2, h), (-w / 2, h)]
        sc = [world_to_screen(*ro(dx + cx, dy + cy), cam_x, cam_y, zoom) for cx, cy in corners]
        pygame.draw.polygon(surface, color, sc)
        pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in color), sc, 1)

    def draw_tri(dx, dy, w, h, color):
        pts = [(-w / 2, 0), (w / 2, 0), (0, h)]
        sc = [world_to_screen(*ro(dx + cx, dy + cy), cam_x, cam_y, zoom) for cx, cy in pts]
        pygame.draw.polygon(surface, color, sc)

    if rocket.current_stage_index == 0:
        for side in [-5.5, 5.5]:
            draw_part(side, 0, 3.6, 30, C_WHITE)
            draw_tri(side, 30, 3.6, 4, C_WHITE)
            draw_tri(side, -3, 2.4, -3, C_NOZZLE)
    if rocket.current_stage_index <= 1:
        draw_part(0, 0, 8.4, 42, C_ORANGE)
        for nx in [-2, 0, 2]:
            draw_tri(nx, -2, 1.6, -2.5, C_NOZZLE)
    draw_part(0, 42, 7, 8, C_WHITE)
    draw_part(0, 50, 5, 5, C_WHITE)
    draw_tri(0, 55, 5, 5, C_WHITE)
    sb = world_to_screen(*ro(0, 60), cam_x, cam_y, zoom)
    st_ = world_to_screen(*ro(0, 64), cam_x, cam_y, zoom)
    pygame.draw.line(surface, (150, 150, 150), sb, st_, max(1, int(0.3 * zoom)))

    is_active = (rocket.current_stage_index < len(rocket.stages)
                 and rocket.stages[rocket.current_stage_index].active)
    if is_active and phase != FlightPhase.PRELAUNCH:
        vac = 1.0 + min(alt / 40000.0, 3.0)
        fw = (8.0 if rocket.current_stage_index == 0 else 4.0) * vac
        fl = random.uniform(15, 28) * vac
        draw_tri(0, -3, fw * 1.2, -fl, C_FLAME_OUT)
        draw_tri(0, -3, fw * 0.7, -fl * 0.8, C_FLAME_MID)
        draw_tri(0, -3, fw * 0.3, -fl * 0.6, C_FLAME_IN)


def draw_debris(surface, debris, cam_x, cam_y, zoom):
    for d in debris:
        sx, sy = world_to_screen(d["x"], d["y"], cam_x, cam_y, zoom)
        size = max(2, int(5 * zoom))
        if VIEW_X < sx < WIDTH and 0 < sy < VIEW_H:
            pygame.draw.rect(surface, C_ORANGE, (sx - size, sy - size, size * 2, size))


# ─── LEFT SIDEBAR ────────────────────────────────────────
def draw_sidebar(surface, font, font_sm, font_tiny, rocket, world, manual_throttle, manual_pitch_offset, cam_mode):
    pygame.draw.rect(surface, C_SIDE_BG, (0, 0, SIDE_W, HEIGHT))
    pygame.draw.line(surface, C_DASH_LINE, (SIDE_W - 1, 0), (SIDE_W - 1, HEIGHT), 1)

    x = 8; y = 8
    surface.blit(font.render("MANUAL CTRL", True, C_YELLOW), (x, y)); y += 22
    surface.blit(font_sm.render(f"Throttle: {manual_throttle * 100:.0f}%", True, C_TEXT), (x, y)); y += 16
    bw = SIDE_W - 20
    pygame.draw.rect(surface, (40, 40, 40), (x, y, bw, 12))
    fill = int(bw * manual_throttle)
    bc = C_GREEN_GO if manual_throttle > 0.3 else C_YELLOW if manual_throttle > 0.1 else C_RED
    pygame.draw.rect(surface, bc, (x, y, fill, 12))
    pygame.draw.rect(surface, C_DASH_LINE, (x, y, bw, 12), 1); y += 20

    pitch_deg = math.degrees(rocket.pitch_angle) if hasattr(rocket, 'pitch_angle') else 90
    surface.blit(font_sm.render(f"Pitch: {pitch_deg:.1f}\u00b0", True, C_TEXT), (x, y)); y += 16
    surface.blit(font_tiny.render(f"Offset: {manual_pitch_offset:.2f}", True, (120, 120, 120)), (x, y)); y += 20

    cam_names = ["TRACKING", "WIDE", "ORBITAL", "GOPRO"]
    surface.blit(font_sm.render(f"Cam: {cam_names[cam_mode]}", True, C_CYAN), (x, y)); y += 20

    surface.blit(font_tiny.render("W/S   Pitch", True, (100, 100, 100)), (x, y)); y += 13
    surface.blit(font_tiny.render("Q/E   Throttle", True, (100, 100, 100)), (x, y)); y += 13
    surface.blit(font_tiny.render("\u2190/\u2192   Warp", True, (100, 100, 100)), (x, y)); y += 13
    surface.blit(font_tiny.render("Scroll Zoom", True, (100, 100, 100)), (x, y)); y += 13
    surface.blit(font_tiny.render("Space  Launch", True, (100, 100, 100)), (x, y)); y += 13
    surface.blit(font_tiny.render("C      Camera", True, (100, 100, 100)), (x, y)); y += 13
    surface.blit(font_tiny.render("R      Reset", True, (100, 100, 100)), (x, y)); y += 22

    # Gravity box
    pygame.draw.rect(surface, (20, 25, 35), (x, y, SIDE_W - 16, 105))
    pygame.draw.rect(surface, C_DASH_LINE, (x, y, SIDE_W - 16, 105), 1)
    surface.blit(font_sm.render("GRAVITY DATA", True, C_CYAN), (x + 4, y + 3)); y += 18
    alt = rocket.get_altitude()
    r = EARTH_RADIUS + alt
    g_acc = G * EARTH_MASS / (r * r) if r > 0 else 9.81
    surface.blit(font_tiny.render(f"g: {g_acc:.4f} m/s\u00b2", True, C_TEXT), (x + 4, y)); y += 13
    surface.blit(font_tiny.render(f"g/g0: {g_acc / 9.81:.4f}", True, C_TEXT), (x + 4, y)); y += 13
    wt = rocket.get_total_mass() * g_acc
    surface.blit(font_tiny.render(f"Wt: {wt / 1000:.1f} kN", True, C_TEXT), (x + 4, y)); y += 13
    v_esc = math.sqrt(2 * G * EARTH_MASS / r) if r > 0 else 0
    surface.blit(font_tiny.render(f"V_esc: {v_esc:.0f} m/s", True, C_TEXT), (x + 4, y)); y += 13
    v_orb = math.sqrt(G * EARTH_MASS / r) if r > 0 else 0
    surface.blit(font_tiny.render(f"V_orb: {v_orb:.0f} m/s", True, C_TEXT), (x + 4, y)); y += 22

    # Orbital mech box
    pygame.draw.rect(surface, (20, 25, 35), (x, y, SIDE_W - 16, 95))
    pygame.draw.rect(surface, C_DASH_LINE, (x, y, SIDE_W - 16, 95), 1)
    surface.blit(font_sm.render("ORBITAL MECH", True, C_MAGENTA), (x + 4, y + 3)); y += 18
    vel = rocket.get_velocity_mag()
    soe = 0.5 * vel * vel - G * EARTH_MASS / r if r > 0 else 0
    surface.blit(font_tiny.render(f"E_sp: {soe / 1e6:.2f} MJ/kg", True, C_TEXT), (x + 4, y)); y += 13
    a = -G * EARTH_MASS / (2 * soe) if soe != 0 else r
    peri_alt = (r - EARTH_RADIUS) / 1000.0
    apo_alt = max(0, (a * 2 - r - EARTH_RADIUS) / 1000.0) if a > 0 else 0
    surface.blit(font_tiny.render(f"Apo: {apo_alt:.0f} km", True, C_TEXT), (x + 4, y)); y += 13
    surface.blit(font_tiny.render(f"Peri: {peri_alt:.0f} km", True, C_TEXT), (x + 4, y)); y += 13
    if a > 0:
        period = 2 * math.pi * math.sqrt(a ** 3 / (G * EARTH_MASS))
        surface.blit(font_tiny.render(f"T: {period / 60:.0f} min", True, C_TEXT), (x + 4, y))
    else:
        surface.blit(font_tiny.render("T: N/A", True, C_TEXT), (x + 4, y))


# ─── BOTTOM DASHBOARD ───────────────────────────────────
def draw_dashboard(surface, font, font_sm, font_tiny, rocket, world, graphs, traj_local, traj_orbit):
    dy = VIEW_H
    pygame.draw.rect(surface, C_DASH_BG, (0, dy, WIDTH, DASH_H))
    pygame.draw.line(surface, C_DASH_LINE, (0, dy), (WIDTH, dy), 2)

    alt = rocket.get_altitude(); vel = rocket.get_velocity_mag()
    stg = rocket.current_stage_index
    stg_name = rocket.stages[stg].name if stg < len(rocket.stages) else "COAST"

    col_x = 12; ly = dy + 8
    surface.blit(font.render(f"SPEED: {vel:.1f} m/s", True, C_GREEN_GO), (col_x, ly)); ly += 22
    surface.blit(font.render(f"ALT: {alt:.1f} m", True, C_CYAN), (col_x, ly)); ly += 22
    surface.blit(font_sm.render(f"G-LOAD: {graphs['gforce_val']:.2f}", True, C_MAGENTA), (col_x, ly)); ly += 18
    surface.blit(font_sm.render(f"Mass: {rocket.get_total_mass():.0f} kg", True, C_TEXT), (col_x, ly)); ly += 18
    surface.blit(font_sm.render(f"Stage: {stg_name}", True, C_YELLOW), (col_x, ly)); ly += 18
    if stg < len(rocket.stages):
        fs = rocket.stages[stg].fuel_system
        fp = fs.fuel / (fs.initial_fuel + 0.001) * 100
        bw = 120; bh = 14
        pygame.draw.rect(surface, (40, 40, 40), (col_x, ly, bw, bh))
        fc = C_GREEN_GO if fp > 30 else C_YELLOW if fp > 10 else C_RED
        pygame.draw.rect(surface, fc, (col_x, ly, int(bw * fp / 100), bh))
        pygame.draw.rect(surface, C_DASH_LINE, (col_x, ly, bw, bh), 1)
        surface.blit(font_tiny.render(f"FUEL {fp:.0f}%", True, C_TEXT), (col_x + bw + 5, ly + 1))

    gw = 140; gh = 100; gap = 6; gx = 170
    r1y = dy + 10; r2y = r1y + gh + 8
    for i, key in enumerate(["alt", "vel", "maxq", "gforce"]):
        graphs[key].draw(surface, (gx + i * (gw + gap), r1y, gw, gh), font_tiny)
    for i, key in enumerate(["thrust", "fuel_graph"]):
        graphs[key].draw(surface, (gx + i * (gw + gap), r2y, gw, gh), font_tiny)
    tx = gx + 2 * (gw + gap)
    traj_local.draw(surface, (tx, r2y, gw, gh), font_tiny)
    traj_orbit.draw(surface, (tx + gw + gap, r2y, gw, gh), font_tiny)

    hx = gx + 4 * (gw + gap) + 8
    surface.blit(font.render("System Health", True, C_TEXT), (hx, r1y))
    for i, name in enumerate(["Avionics", "Propulsion", "Thermal", "Propellant", "Navigation", "Comms"]):
        surface.blit(font_tiny.render(name, True, (160, 160, 160)), (hx, r1y + 22 + i * 18))
        surface.blit(font_tiny.render("GO", True, C_GREEN_GO), (hx + 85, r1y + 22 + i * 18))

    pm = {0: "PRE", 1: "LIFT", 2: "MAX-Q", 3: "G-TURN", 4: "SRB SEP", 5: "FAIR", 6: "STG2", 7: "SECO"}
    surface.blit(font.render(f"PHASE: {pm.get(world.phase, '?')}", True, C_YELLOW), (hx, r2y + 5))
    surface.blit(font_sm.render(f"T: {format_time(world.time_elapsed)}", True, C_TEXT), (hx, r2y + 28))
    surface.blit(font_sm.render(f"Warp: {world.time_warp:.0f}x", True, C_TEXT), (hx, r2y + 48))


def draw_hud(surface, font, font_lg, world, phase):
    surface.blit(font.render(f"T: {format_time(world.time_elapsed)} | WARP: {world.time_warp:.0f}x", True, C_TEXT), (VIEW_X + 10, 8))
    pm = {0: "T-MINUS (PRELAUNCH)", 1: "LIFTOFF", 2: "MAX-Q", 3: "GRAVITY TURN",
          4: "SRB SEPARATION", 5: "FAIRING SEP", 6: "CORE SEP / STG 2", 7: "SECO (ORBIT)"}
    ps = font_lg.render(f"  PHASE: {pm.get(phase, '?')}  ", True, C_YELLOW, (15, 15, 20))
    surface.blit(ps, (VIEW_X + VIEW_W // 2 - ps.get_width() // 2, 30))
    pygame.draw.rect(surface, (50, 55, 65), (WIDTH - 115, 6, 105, 28), border_radius=4)
    pygame.draw.rect(surface, C_DASH_LINE, (WIDTH - 115, 6, 105, 28), 1, border_radius=4)
    surface.blit(font.render("RESTART", True, C_TEXT), (WIDTH - 105, 10))


# ─── MAIN ────────────────────────────────────────────────
def run_app():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rocket Mission Simulator \u2014 Artemis II")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Menlo", 14)
    font_sm = pygame.font.SysFont("Menlo", 12)
    font_lg = pygame.font.SysFont("Menlo", 17, bold=True)
    font_tiny = pygame.font.SysFont("Menlo", 10)

    sky_cache = build_sky_cache()

    random.seed(42)
    clouds = [(random.uniform(-20000, 20000), random.uniform(1500, 8000),
               random.uniform(150, 700), random.uniform(40, 160)) for _ in range(80)]

    def init_world():
        m = MissionProfile("FALCON_9", "LEO")
        w = World(m); w.time_warp = 1.0
        return w

    def make_graphs():
        return {
            "alt": RollingGraph(80, 200, C_CYAN, "Alt (km)"),
            "vel": RollingGraph(80, 8, (255, 130, 0), "Vel (km/s)"),
            "maxq": RollingGraph(80, 50, C_RED, "Max-Q (kPa)"),
            "gforce": RollingGraph(80, 5, C_MAGENTA, "G-Force"),
            "thrust": RollingGraph(80, 40000, C_YELLOW, "Thrust (kN)"),
            "fuel_graph": RollingGraph(80, 100, C_GREEN_GO, "Fuel (%)"),
            "gforce_val": 1.0,
        }

    world = init_world()
    graphs = make_graphs()
    tl = TrajectoryPlot(scale=500, color=C_YELLOW, label="Ascent Profile")
    to = TrajectoryPlot(scale=15000, color=C_MAGENTA, label="Global Orbit", draw_earth=True)
    gt = 0.0; lv = 0.0
    cam_mode = 0
    manual_pitch = 0.0; manual_throttle = 1.0
    zoom_override = None  # None = auto, float = manual zoom
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_SPACE:
                    if world.phase == FlightPhase.PRELAUNCH: world.start()
                elif event.key == pygame.K_RIGHT:
                    if world.time_warp < 100: world.time_warp *= 2
                elif event.key == pygame.K_LEFT:
                    if world.time_warp > 1: world.time_warp /= 2
                elif event.key == pygame.K_c:
                    cam_mode = (cam_mode + 1) % 4
                    zoom_override = None
                elif event.key == pygame.K_r:
                    world = init_world(); graphs = make_graphs()
                    tl = TrajectoryPlot(scale=500, color=C_YELLOW, label="Ascent Profile")
                    to = TrajectoryPlot(scale=15000, color=C_MAGENTA, label="Global Orbit", draw_earth=True)
                    lv = 0; cam_mode = 0; manual_pitch = 0.0; manual_throttle = 1.0; zoom_override = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    if WIDTH - 115 <= mx <= WIDTH - 10 and 6 <= my <= 34:
                        world = init_world(); graphs = make_graphs()
                        tl = TrajectoryPlot(scale=500, color=C_YELLOW, label="Ascent Profile")
                        to = TrajectoryPlot(scale=15000, color=C_MAGENTA, label="Global Orbit", draw_earth=True)
                        lv = 0; cam_mode = 0; manual_pitch = 0.0; manual_throttle = 1.0; zoom_override = None
                elif event.button == 4:  # scroll up = zoom in
                    if zoom_override is None:
                        zoom_override = 1.0
                    zoom_override *= 1.3
                elif event.button == 5:  # scroll down = zoom out
                    if zoom_override is None:
                        zoom_override = 1.0
                    zoom_override /= 1.3
                    zoom_override = max(zoom_override, 0.0001)

        # Continuous keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: manual_pitch += 0.5 * dt
        if keys[pygame.K_s]: manual_pitch -= 0.5 * dt
        manual_pitch = max(-0.5, min(0.5, manual_pitch))
        if keys[pygame.K_q]: manual_throttle = max(0, manual_throttle - 0.5 * dt)
        if keys[pygame.K_e]: manual_throttle = min(1, manual_throttle + 0.5 * dt)

        if world.phase != FlightPhase.PRELAUNCH:
            world.rocket.pitch_angle += manual_pitch * dt * 2

        world.update(dt)
        rocket = world.rocket
        alt = rocket.get_altitude()
        vel = rocket.get_velocity_mag()

        # ─── CAMERA ──────────────────────
        if cam_mode == 0:  # Tracking
            if alt < 200:
                cam_x, cam_y = 0, EARTH_RADIUS + 35; base_zoom = 4.5
            elif alt < 5000:
                cam_x = rocket.x; cam_y = rocket.y; base_zoom = max(1.0, 4.5 - alt / 2000.0)
            else:
                cam_x = rocket.x; cam_y = rocket.y; base_zoom = max(0.08, 1.0 - alt / 100000.0)
        elif cam_mode == 1:  # Wide
            cam_x = rocket.x; cam_y = rocket.y
            base_zoom = max(0.005, 0.3 - alt / 500000.0)
        elif cam_mode == 2:  # Orbital
            cam_x = rocket.x; cam_y = rocket.y
            base_zoom = max(0.00005, 0.0005 - alt / 100000000.0)
        elif cam_mode == 3:  # GoPro on-rocket
            # Camera is right next to the rocket, looking at it from slightly offset
            cam_x = rocket.x + 15 * math.cos(rocket.pitch_angle + 0.3)
            cam_y = rocket.y + 15 * math.sin(rocket.pitch_angle + 0.3)
            base_zoom = 8.0  # very close

        zoom = zoom_override if zoom_override is not None else base_zoom
        zoom = max(zoom, 0.000005)

        # Graph updates
        gt += dt
        if gt >= 0.25:
            accel = (vel - lv) / gt if gt > 0 else 0
            lv = vel
            gf = abs(accel / 9.81)
            if alt < 10: gf = 1.0
            graphs["gforce_val"] = gf
            rho = 1.225 * math.exp(-alt / 8500.0) if alt > 0 else 1.225
            q = 0.5 * rho * vel ** 2
            graphs["alt"].push(alt / 1000.0)
            graphs["vel"].push(vel / 1000.0)
            graphs["maxq"].push(q / 1000.0)
            graphs["gforce"].push(gf)
            stg = rocket.current_stage_index
            tkn = (rocket.stages[stg].thrust_sl / 1000.0) if (stg < len(rocket.stages) and rocket.stages[stg].active) else 0
            graphs["thrust"].push(tkn)
            if stg < len(rocket.stages):
                fs = rocket.stages[stg].fuel_system
                graphs["fuel_graph"].push(fs.fuel / (fs.initial_fuel + 0.001) * 100)
            else:
                graphs["fuel_graph"].push(0)
            tl.push(rocket.x, rocket.y)
            to.push(rocket.x, rocket.y)
            gt = 0.0

        # ─── DRAW ────────────────────────
        # Sky (pre-cached, no per-pixel work)
        si = get_sky_index(alt)
        screen.blit(sky_cache[si], (VIEW_X, 0))

        draw_stars(screen, alt)

        if alt > 20000:
            draw_earth_detailed(screen, cam_x, cam_y, zoom)
            draw_moon(screen, cam_x, cam_y, zoom)
        else:
            draw_ground_and_pad(screen, cam_x, cam_y, zoom)
            draw_clouds_simple(screen, cam_x, cam_y, zoom, clouds)

        draw_debris(screen, world.debris, cam_x, cam_y, zoom)
        draw_rocket(screen, rocket, cam_x, cam_y, zoom, world.phase)

        draw_sidebar(screen, font, font_sm, font_tiny, rocket, world, manual_throttle, manual_pitch, cam_mode)
        draw_dashboard(screen, font, font_sm, font_tiny, rocket, world, graphs, tl, to)
        draw_hud(screen, font, font_lg, world, world.phase)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
