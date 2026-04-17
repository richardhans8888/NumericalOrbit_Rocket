# rendering_pygame/app.py
"""
Pygame-based satellite mission simulator renderer.
Features:
  - Scientific-grade telemetry graphs with axes, ticks, grid, and units
  - Pre-launch vehicle & orbit selection screen
  - Multi-vehicle simulation (Falcon 9, Atlas V, Ariane 5, Electron, Soyuz-2.1b, PSLV-C37)
  - Proper computational physics dashboard
"""
import pygame
import sys
import math
import random
import collections

from mission.mission_profile import MissionProfile
from mission.flight_phases import FlightPhase, PHASE_NAMES
from mission.telemetry import format_time
from mission.orbit_targets import ORBITS
from mission.vehicle_database import VEHICLES
from simulation.world import World
from physics.constants import EARTH_RADIUS, G, EARTH_MASS
from rendering_pygame.vehicle_select import run_selection

# ── Layout ───────────────────────────────────────────────
WIDTH, HEIGHT = 1440, 900
SIDE_W  = 185
DASH_H  = 295          # taller dashboard for proper graphs
VIEW_X  = SIDE_W
VIEW_W  = WIDTH - SIDE_W
VIEW_H  = HEIGHT - DASH_H
FPS     = 60

MOON_DISTANCE = 384400000.0
MOON_RADIUS   = 1737000.0

# ── Colors ───────────────────────────────────────────────
C_GROUND    = (72,  140, 50)
C_GROUND_DK = (55,  110, 38)
C_PAD       = (140, 140, 135)
C_PAD_DARK  = (80,  80,  80)
C_ROAD      = (90,  90,  90)
C_TOWER     = (160, 150, 140)
C_VAB       = (110, 115, 130)
C_VAB_DOOR  = (70,  75,  85)
C_ORANGE    = (225, 120, 20)
C_WHITE     = (240, 240, 235)
C_NOZZLE    = (60,  60,  65)
C_FLAME_IN  = (255, 255, 180)
C_FLAME_MID = (255, 200, 50)
C_FLAME_OUT = (255, 100, 20)
C_DASH_BG   = (10,  14,  22)
C_SIDE_BG   = (8,   12,  20)
C_DASH_LINE = (38,  50,  72)
C_TEXT      = (210, 215, 225)
C_GREEN_GO  = (30,  255, 80)
C_CYAN      = (0,   200, 255)
C_YELLOW    = (255, 220, 40)
C_MAGENTA   = (210, 60,  210)
C_RED       = (255, 60,  60)
C_OCEAN     = (20,  55,  100)
C_LAND1     = (60,  130, 45)
C_LAND2     = (90,  150, 60)
C_LAND3     = (45,  100, 35)
C_DESERT    = (170, 150, 100)
C_ICE       = (210, 225, 240)
C_MOON      = (180, 180, 175)
C_GRID      = (25,  33,  50)    # graph grid lines
C_AXIS      = (55,  70,  100)   # graph axis lines


def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def scale_color(c, f):
    return (
        int(clamp(c[0] * f, 0, 255)),
        int(clamp(c[1] * f, 0, 255)),
        int(clamp(c[2] * f, 0, 255)),
    )


def build_ground_texture(w=768, h=384):
    surf = pygame.Surface((w, h))
    random.seed(20260417)
    for y in range(h):
        t = y / max(1, h - 1)
        base = lerp_color(C_LAND3, C_GROUND, 0.12 + 0.78 * t)
        pygame.draw.line(surf, base, (0, y), (w, y))
    for _ in range(int(w * h * 0.0028)):
        x = random.randrange(w)
        y = random.randrange(h)
        r = random.randint(1, 3)
        col = random.choice(
            [
                scale_color(C_GROUND, 0.85),
                scale_color(C_GROUND, 0.72),
                scale_color(C_LAND2, 0.78),
                (95, 85, 60),
                (70, 65, 48),
            ]
        )
        pygame.draw.circle(surf, col, (x, y), r)
    for _ in range(140):
        x0 = random.randrange(w)
        y0 = random.randrange(h)
        x1 = x0 + random.randint(-80, 80)
        y1 = y0 + random.randint(-25, 25)
        col = random.choice([(58, 120, 44), (62, 135, 48), (70, 150, 55)])
        pygame.draw.aaline(surf, col, (x0, y0), (x1, y1))
    return surf


def build_pad_texture(w=512, h=256):
    surf = pygame.Surface((w, h))
    random.seed(20260418)
    base0 = (105, 106, 110)
    base1 = (135, 135, 140)
    for y in range(h):
        t = y / max(1, h - 1)
        col = lerp_color(base0, base1, 0.15 + 0.7 * t)
        pygame.draw.line(surf, col, (0, y), (w, y))
    for _ in range(int(w * h * 0.002)):
        x = random.randrange(w)
        y = random.randrange(h)
        r = random.randint(1, 2)
        col = random.choice([(85, 85, 90), (120, 120, 126), (70, 70, 74)])
        pygame.draw.circle(surf, col, (x, y), r)
    for i in range(6):
        yy = int((i + 1) * h / 7)
        pygame.draw.line(surf, (160, 160, 165), (0, yy), (w, yy), 1)
    for i in range(10):
        xx = int((i + 1) * w / 11)
        pygame.draw.line(surf, (95, 95, 100), (xx, 0), (xx, h), 1)
    for x in range(40, w - 40, 56):
        pygame.draw.rect(surf, (170, 170, 175), (x, 18, 12, h - 36), 2)
    return surf


def cylinder_fill(surf, rect, base_color, edge_color=None, highlight=True):
    x, y, w, h = rect
    if w <= 1 or h <= 1:
        return
    for ix in range(w):
        nx = (ix / (w - 1)) * 2 - 1
        shade = 0.62 + 0.38 * (1 - nx * nx)
        col = scale_color(base_color, shade)
        pygame.draw.line(surf, col, (x + ix, y), (x + ix, y + h - 1))
    if highlight and w >= 6:
        hx = x + int(w * 0.28)
        pygame.draw.line(surf, (255, 255, 255, 70), (hx, y + 2), (hx, y + h - 3))
        hx2 = x + int(w * 0.66)
        pygame.draw.line(surf, (0, 0, 0, 35), (hx2, y + 2), (hx2, y + h - 3))
    if edge_color is None:
        edge_color = scale_color(base_color, 0.55)
    pygame.draw.rect(surf, edge_color, rect, 1)


def render_rocket_sprite(core_h_px, core_w_px, stage_index, fairing_attached):
    show_boosters = stage_index == 0
    ppm = max(0.00001, core_w_px / 8.4)
    total_w = core_w_px + (int(7.4 * ppm) if show_boosters else 0)
    nose_h = max(14, int(9.0 * ppm))
    bell_pad = max(10, int(5.5 * ppm))
    total_h = core_h_px + nose_h + bell_pad + 6
    surf = pygame.Surface((max(2, total_w), max(2, total_h)), pygame.SRCALPHA)

    cx = surf.get_width() // 2
    core_y = nose_h + 2
    base_y = core_y + core_h_px

    core_w = core_w_px
    core_h = core_h_px
    core_x = cx - core_w // 2
    core_y = base_y - core_h

    body_col = (235, 235, 234) if stage_index >= 1 else (232, 118, 28)
    cylinder_fill(surf, pygame.Rect(core_x, core_y, core_w, core_h), body_col)

    if stage_index <= 1:
        ring_h = max(2, int(0.55 * ppm))
        for ry in [
            core_y + int(core_h * 0.18),
            core_y + int(core_h * 0.52),
            core_y + int(core_h * 0.78),
        ]:
            pygame.draw.rect(surf, (20, 20, 24, 40), (core_x, ry, core_w, ring_h))
            pygame.draw.line(surf, (255, 255, 255, 60), (core_x + 1, ry), (core_x + core_w - 2, ry))

    inter_h = max(4, int(2.0 * ppm))
    pygame.draw.rect(surf, (245, 245, 245, 120), (core_x + 1, core_y + core_h - inter_h, core_w - 2, inter_h))
    pygame.draw.rect(surf, (0, 0, 0, 55), (core_x + 1, core_y + core_h - 1, core_w - 2, 1))

    fin_h = max(5, int(3.0 * ppm))
    fin_w = max(4, int(2.0 * ppm))
    fin_col = (210, 210, 212)
    pygame.draw.polygon(
        surf,
        (*fin_col, 210),
        [(core_x, base_y), (core_x - fin_w, base_y - fin_h), (core_x, base_y - fin_h // 2)],
    )
    pygame.draw.polygon(
        surf,
        (*fin_col, 210),
        [(core_x + core_w, base_y), (core_x + core_w + fin_w, base_y - fin_h), (core_x + core_w, base_y - fin_h // 2)],
    )

    noz_y = base_y + 1
    if stage_index == 0:
        n_cnt = 3
        bell_w = max(5, int(1.8 * ppm))
        bell_h = max(6, int(2.6 * ppm))
    else:
        n_cnt = 1
        bell_w = max(5, int(2.2 * ppm))
        bell_h = max(7, int(3.0 * ppm))
    if core_w >= 10:
        for i in range(n_cnt):
            t = (i + 1) / (n_cnt + 1)
            bx = core_x + int(t * core_w) - bell_w // 2
            pygame.draw.polygon(
                surf,
                (40, 40, 45, 220),
                [(bx, base_y), (bx + bell_w, base_y), (bx + int(bell_w * 0.7), noz_y + bell_h), (bx + int(bell_w * 0.3), noz_y + bell_h)],
            )
            pygame.draw.polygon(
                surf,
                (0, 0, 0, 55),
                [(bx, base_y), (bx + bell_w, base_y), (bx + int(bell_w * 0.7), noz_y + bell_h), (bx + int(bell_w * 0.3), noz_y + bell_h)],
                1,
            )

    nose_w = int(core_w * (1.05 if fairing_attached else 0.92))
    nx = cx - nose_w // 2
    ny = core_y - nose_h + 2
    if fairing_attached:
        cylinder_fill(surf, pygame.Rect(nx, ny + int(nose_h * 0.25), nose_w, int(nose_h * 0.75)), (240, 240, 242))
        pygame.draw.polygon(
            surf,
            (240, 240, 242, 255),
            [(nx, ny + int(nose_h * 0.28)), (nx + nose_w, ny + int(nose_h * 0.28)), (cx, ny)],
        )
        pygame.draw.polygon(
            surf,
            (0, 0, 0, 50),
            [(nx, ny + int(nose_h * 0.28)), (nx + nose_w, ny + int(nose_h * 0.28)), (cx, ny)],
            1,
        )
    else:
        pygame.draw.polygon(
            surf,
            (235, 235, 236, 255),
            [(core_x, core_y + 2), (core_x + core_w, core_y + 2), (cx, ny)],
        )
        pygame.draw.polygon(
            surf,
            (0, 0, 0, 45),
            [(core_x, core_y + 2), (core_x + core_w, core_y + 2), (cx, ny)],
            1,
        )

    if show_boosters:
        b_w = max(6, int(3.6 * ppm))
        b_h = max(10, int(30.0 * ppm))
        off = int(5.7 * ppm)
        for sgn in (-1, 1):
            bx = cx + sgn * off - b_w // 2
            by = base_y - b_h
            cylinder_fill(surf, pygame.Rect(bx, by, b_w, b_h), (238, 238, 236))
            pygame.draw.polygon(
                surf,
                (238, 238, 236, 255),
                [(bx, by + 2), (bx + b_w, by + 2), (bx + b_w // 2, by - max(6, int(3.2 * ppm)))],
            )
            pygame.draw.polygon(
                surf,
                (55, 55, 60, 220),
                [(bx + int(b_w * 0.2), base_y), (bx + int(b_w * 0.8), base_y), (bx + int(b_w * 0.65), base_y + max(5, int(2.2 * ppm))), (bx + int(b_w * 0.35), base_y + max(5, int(2.2 * ppm)))],
            )

    if core_w >= 16:
        flag_w = int(core_w * 0.45)
        flag_h = max(6, int(core_h * 0.06))
        fx = core_x + int(core_w * 0.30) - flag_w // 2
        fy = core_y + int(core_h * 0.35)
        pygame.draw.rect(surf, (20, 20, 25, 120), (fx - 2, fy - 2, flag_w + 4, flag_h + 4), border_radius=3)
        pygame.draw.rect(surf, (230, 230, 232, 210), (fx, fy, flag_w, flag_h), border_radius=2)
        pygame.draw.line(surf, (200, 60, 60, 240), (fx + 1, fy + 1), (fx + flag_w - 2, fy + 1), 2)
        pygame.draw.line(surf, (40, 90, 200, 240), (fx + 1, fy + flag_h - 2), (fx + flag_w - 2, fy + flag_h - 2), 2)

    return surf


def render_satellite_sprite(bus_w_px, bus_h_px):
    bus_w_px = max(10, int(bus_w_px))
    bus_h_px = max(8, int(bus_h_px))
    pad = max(10, int(bus_w_px * 0.9))
    surf = pygame.Surface((bus_w_px + pad * 2, bus_h_px + pad * 2), pygame.SRCALPHA)
    cx = surf.get_width() // 2
    cy = surf.get_height() // 2

    body = pygame.Rect(cx - bus_w_px // 2, cy - bus_h_px // 2, bus_w_px, bus_h_px)
    pygame.draw.rect(surf, (15, 18, 24, 160), body.inflate(6, 6), border_radius=4)
    cylinder_fill(surf, body, (220, 222, 226), edge_color=(65, 70, 85), highlight=True)

    dish_r = max(4, int(bus_h_px * 0.55))
    dish_cx = body.right + max(5, int(bus_w_px * 0.2))
    dish_cy = cy
    pygame.draw.circle(surf, (35, 38, 48, 150), (dish_cx, dish_cy), dish_r + 2)
    pygame.draw.circle(surf, (205, 205, 210, 230), (dish_cx, dish_cy), dish_r, 2)
    pygame.draw.circle(surf, (145, 145, 150, 140), (dish_cx, dish_cy), max(2, dish_r - 3), 0)
    pygame.draw.line(surf, (120, 120, 125, 180), (body.right - 1, dish_cy), (dish_cx - dish_r + 2, dish_cy), 2)

    panel_w = max(14, int(bus_w_px * 1.25))
    panel_h = max(6, int(bus_h_px * 0.85))
    gap = max(3, int(bus_w_px * 0.18))
    for sgn in (-1, 1):
        px0 = cx + sgn * (bus_w_px // 2 + gap)
        panel = pygame.Rect(px0 - panel_w // 2, cy - panel_h // 2, panel_w, panel_h)
        pygame.draw.rect(surf, (10, 14, 26, 200), panel, border_radius=2)
        pygame.draw.rect(surf, (0, 200, 255, 120), panel, 1, border_radius=2)
        cell_w = max(3, panel_w // 6)
        for i in range(1, 6):
            xx = panel.x + i * cell_w
            pygame.draw.line(surf, (0, 90, 130, 120), (xx, panel.y + 1), (xx, panel.bottom - 2), 1)
        pygame.draw.line(surf, (0, 90, 130, 120), (panel.x + 1, cy), (panel.right - 2, cy), 1)
        pygame.draw.line(surf, (150, 155, 165, 180), (body.centerx + sgn * (bus_w_px // 2), cy), (panel.centerx - sgn * (panel_w // 2), cy), 2)

    return surf


def spawn_exhaust(particles, rocket, manual_throttle, dt, intensity=1.0):
    if manual_throttle <= 0:
        return
    alt = rocket.get_altitude()
    pitch = rocket.pitch_angle
    ux = math.cos(pitch)
    uy = math.sin(pitch)
    ex = -ux
    ey = -uy
    px = -uy
    py = ux

    base_x = rocket.x - ux * 1.8
    base_y = rocket.y - uy * 1.8
    vac = 1.0 + min(alt / 40000.0, 3.0)
    rate = (90.0 if alt < 2000 else 45.0) * manual_throttle * intensity
    n = int(rate * dt)
    for _ in range(n):
        spread = random.uniform(-1.2, 1.2) * (1.2 + 0.7 * vac)
        ox = px * spread
        oy = py * spread
        speed = random.uniform(55, 115) * vac
        vx = ex * speed + random.uniform(-8, 8)
        vy = ey * speed + random.uniform(-8, 8)
        life = random.uniform(0.15, 0.35) * vac
        r0 = random.uniform(0.8, 1.8) * (1.0 + 0.5 * vac)
        particles.append(
            {
                "x": base_x + ox,
                "y": base_y + oy,
                "vx": vx,
                "vy": vy,
                "life": life,
                "ttl": life,
                "r": r0,
                "kind": "flame",
            }
        )

    if alt < 6000:
        s_rate = (110.0 if alt < 250 else 55.0) * manual_throttle * intensity
        sn = int(s_rate * dt)
        for _ in range(sn):
            spread = random.uniform(-3.2, 3.2) * (1.0 + (6000 - alt) / 6000.0)
            ox = px * spread
            oy = py * spread
            speed = random.uniform(10, 38) + random.uniform(0, 18) * (1.0 - min(alt / 6000.0, 1.0))
            vx = ex * speed * 0.6 + random.uniform(-8, 8)
            vy = ey * speed * 0.35 + random.uniform(-6, 6)
            life = random.uniform(1.2, 2.6)
            r0 = random.uniform(1.8, 4.2) * (1.0 + (800 - min(alt, 800)) / 800.0)
            particles.append(
                {
                    "x": base_x + ox,
                    "y": base_y + oy,
                    "vx": vx,
                    "vy": vy,
                    "life": life,
                    "ttl": life,
                    "r": r0,
                    "kind": "smoke",
                }
            )


def update_particles(particles, dt):
    for i in range(len(particles) - 1, -1, -1):
        p = particles[i]
        p["life"] -= dt
        if p["life"] <= 0:
            particles.pop(i)
            continue
        if p["kind"] == "smoke":
            p["vx"] *= 0.985
            p["vy"] *= 0.985
            p["vy"] += 7.0 * dt
            p["r"] += 8.0 * dt
        else:
            p["vx"] *= 0.97
            p["vy"] *= 0.97
            p["r"] += 3.2 * dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt


def draw_particles(screen, fx_surf, particles, cam_x, cam_y, zoom):
    fx_surf.fill((0, 0, 0, 0))
    for p in particles:
        sx, sy = world_to_screen(p["x"], p["y"], cam_x, cam_y, zoom)
        if not (VIEW_X - 60 <= sx <= WIDTH + 60 and -60 <= sy <= VIEW_H + 60):
            continue
        t = p["life"] / max(p["ttl"], 0.0001)
        if p["kind"] == "smoke":
            a = int(170 * clamp(t, 0, 1))
            col = (90, 92, 98, a)
            rr = max(2, int(p["r"] * zoom))
            pygame.draw.circle(fx_surf, col, (sx - VIEW_X, sy), rr)
            if rr > 6:
                pygame.draw.circle(fx_surf, (60, 62, 68, int(a * 0.45)), (sx - VIEW_X + rr // 4, sy + rr // 6), max(1, rr // 2), 0)
        else:
            a = int(190 * clamp(t, 0, 1))
            rr = max(2, int(p["r"] * zoom))
            pygame.draw.circle(fx_surf, (255, 160, 40, a), (sx - VIEW_X, sy), rr)
            pygame.draw.circle(fx_surf, (255, 230, 190, int(a * 0.7)), (sx - VIEW_X, sy), max(1, rr // 2))
    screen.blit(fx_surf, (VIEW_X, 0))


def world_to_screen(wx, wy, cam_x, cam_y, zoom):
    sx = VIEW_X + VIEW_W // 2 + (wx - cam_x) * zoom
    sy = VIEW_H // 2 - (wy - cam_y) * zoom
    return int(sx), int(sy)


# ── Pre-cached Sky ───────────────────────────────────────
def build_sky_cache():
    skies = []
    for level in range(11):
        t = level / 10.0
        surf = pygame.Surface((VIEW_W, VIEW_H))
        for row in range(0, VIEW_H, 4):
            frac = row / VIEW_H
            sky_top = (30, 60, 120)
            sky_bot = (120, 170, 230)
            space   = (5, 5, 15)
            ground_col = lerp_color(sky_top, sky_bot, frac)
            col = lerp_color(ground_col, space, t)
            pygame.draw.rect(surf, col, (0, row, VIEW_W, 4))
        skies.append(surf)
    return skies


def get_sky_index(alt):
    return min(10, int(alt / 10000.0))


# ── Scientific Graph Widget ───────────────────────────────
class SciGraph:
    """
    A proper computational-physics rolling graph with:
    - Labelled X and Y axes with tick marks
    - Adaptive Y-scale (auto-ranging)
    - Background grid
    - Current-value dot highlight
    - Min / max annotations
    - Unit label on Y axis
    """
    def __init__(self, max_pts=120, y_label="", unit="", color=C_CYAN,
                 y_min_fixed=None, y_max_fixed=None, y_ticks=5):
        self.data       = collections.deque(maxlen=max_pts)
        self.color      = color
        self.y_label    = y_label
        self.unit       = unit
        self.y_ticks    = y_ticks
        self.y_min_fix  = y_min_fixed
        self.y_max_fix  = y_max_fixed
        # Running min/max for auto-scale
        self._data_max  = 1.0
        self._data_min  = 0.0

    def push(self, v):
        self.data.append(float(v))
        if len(self.data) > 2:
            self._data_max = max(self.data)
            self._data_min = min(self.data)

    def _y_range(self):
        lo = self.y_min_fix if self.y_min_fix is not None else self._data_min
        hi = self.y_max_fix if self.y_max_fix is not None else self._data_max
        if hi <= lo:
            hi = lo + 1.0
        margin = (hi - lo) * 0.08
        return lo - margin, hi + margin

    @staticmethod
    def _nice_ticks(lo, hi, n=5):
        """Compute n evenly-spaced nice tick values in [lo, hi]."""
        if hi <= lo:
            return [lo]
        step = (hi - lo) / max(n - 1, 1)
        # Round step to 1 or 2 or 5 × 10^k
        if step == 0:
            return [lo]
        mag = 10 ** math.floor(math.log10(step))
        for m in [1, 2, 5, 10]:
            if step <= m * mag:
                step = m * mag
                break
        start = math.floor(lo / step) * step
        ticks = []
        v = start
        while v <= hi + step * 0.1:
            if lo - step * 0.1 <= v <= hi + step * 0.1:
                ticks.append(v)
            v += step
            if len(ticks) > 12:
                break
        return ticks

    def draw(self, surface, rect, font_tiny, font_label=None):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        # ── Background ──────────────────────────────────
        pygame.draw.rect(surface, (14, 18, 28), rect)

        if len(self.data) == 0:
            pygame.draw.rect(surface, C_AXIS, rect, 1)
            lbl = font_tiny.render(self.y_label, True, (80, 90, 110))
            surface.blit(lbl, (x + 4, y + 4))
            return

        lo, hi = self._y_range()
        ticks = self._nice_ticks(lo, hi, self.y_ticks)

        # Plot area margins (leave room for tick labels)
        PAD_L = 44   # Y-axis labels
        PAD_B = 18   # X-axis labels
        PAD_T = 16   # top margin
        PAD_R = 6

        px0 = x + PAD_L
        py0 = y + PAD_T
        pw  = w - PAD_L - PAD_R
        ph  = h - PAD_T - PAD_B

        def data_to_py(val):
            frac = (val - lo) / (hi - lo) if (hi - lo) != 0 else 0
            return int(py0 + ph - frac * ph)

        # ── Grid + Y-ticks ──────────────────────────────
        for tv in ticks:
            ty = data_to_py(tv)
            if py0 <= ty <= py0 + ph:
                pygame.draw.line(surface, C_GRID, (px0, ty), (px0 + pw, ty))
                pygame.draw.line(surface, C_AXIS, (px0 - 4, ty), (px0, ty))
                # Tick label
                if abs(tv) >= 1000:
                    lbl_str = f"{tv/1000:.1f}k"
                elif abs(tv) >= 1 or tv == 0:
                    lbl_str = f"{tv:.1f}"
                else:
                    lbl_str = f"{tv:.2f}"
                lbl_surf = font_tiny.render(lbl_str, True, C_AXIS)
                surface.blit(lbl_surf, (px0 - lbl_surf.get_width() - 5,
                                        ty - lbl_surf.get_height() // 2))

        # X-axis: time ticks (evenly spaced, label as index count)
        n_pts = len(self.data)
        x_ticks = 5
        for i in range(x_ticks + 1):
            tx = px0 + int(i * pw / x_ticks)
            pygame.draw.line(surface, C_GRID, (tx, py0), (tx, py0 + ph))
            pygame.draw.line(surface, C_AXIS, (tx, py0 + ph), (tx, py0 + ph + 4))

        # ── Axes ────────────────────────────────────────
        pygame.draw.line(surface, C_AXIS, (px0, py0), (px0, py0 + ph), 1)          # Y
        pygame.draw.line(surface, C_AXIS, (px0, py0 + ph), (px0 + pw, py0 + ph), 1) # X

        # ── Data line ───────────────────────────────────
        if len(self.data) > 1:
            pts = []
            for i, val in enumerate(self.data):
                gx = px0 + int(i * pw / max(len(self.data) - 1, 1))
                gy = data_to_py(val)
                gy = max(py0, min(py0 + ph, gy))
                pts.append((gx, gy))
            # Shadow / glow under line
            if len(pts) > 1:
                fill_pts = [pts[0]] + pts + [(pts[-1][0], py0 + ph), (pts[0][0], py0 + ph)]
                glow_surf = pygame.Surface((pw + PAD_L + PAD_R, ph + PAD_T + PAD_B), pygame.SRCALPHA)
                adj_pts = [(p[0] - x, p[1] - y) for p in fill_pts]
                try:
                    pygame.draw.polygon(glow_surf, (*self.color, 22), adj_pts)
                except Exception:
                    pass
                surface.blit(glow_surf, (x, y))
                pygame.draw.lines(surface, self.color, False, pts, 2)

            # Highlight current value dot
            cx_, cy_ = pts[-1]
            pygame.draw.circle(surface, C_DASH_BG, (cx_, cy_), 5)
            pygame.draw.circle(surface, self.color, (cx_, cy_), 4)
            # Dashed horizontal guide to Y axis
            for dash_x in range(px0, cx_, 6):
                pygame.draw.line(surface, (*self.color, 80), (dash_x, cy_),
                                 (min(dash_x + 3, cx_), cy_))

        # ── Labels ──────────────────────────────────────
        # Y-axis label (vertical)
        y_lbl = font_tiny.render(self.y_label, True, self.color)
        y_lbl_r = pygame.transform.rotate(y_lbl, 90)
        surface.blit(y_lbl_r, (x + 2, y + h // 2 - y_lbl_r.get_height() // 2))

        # Unit top-right
        if self.unit:
            u = font_tiny.render(f"[{self.unit}]", True, (80, 90, 110))
            surface.blit(u, (x + w - u.get_width() - 4, y + 2))

        # Current value top-left
        cur = self.data[-1]
        if abs(cur) >= 10000:
            cur_str = f"{cur/1000:.2f}k"
        elif abs(cur) >= 100:
            cur_str = f"{cur:.1f}"
        else:
            cur_str = f"{cur:.3f}"
        cv = font_tiny.render(cur_str, True, self.color)
        surface.blit(cv, (px0 + 3, y + 3))

        # Border
        pygame.draw.rect(surface, C_AXIS, rect, 1)


# ── Trajectory Map ───────────────────────────────────────
class TrajectoryMap:
    """
    Orbital trajectory plot drawn to scale relative to Earth.
    Shows: Earth (blue circle), target orbit ring (dashed), trajectory arc,
    current position crosshair, and axis labels.
    """
    def __init__(self, max_pts=400, label="Orbital Map",
                 orbit_alt_m=400000.0, orbit_color=C_CYAN):
        self.pts        = collections.deque(maxlen=max_pts)
        self.label      = label
        self.orbit_alt  = orbit_alt_m
        self.orbit_color = orbit_color

    def push(self, x_m, y_m):
        self.pts.append((x_m / 1000.0, y_m / 1000.0))  # store in km

    def _auto_scale(self, w, h):
        """Returns km per pixel so Earth + orbit + margin fit."""
        target_r_km = (EARTH_RADIUS + self.orbit_alt) / 1000.0 * 1.25
        return target_r_km / (min(w, h) / 2.0)

    def draw(self, surface, rect, font_tiny):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        pygame.draw.rect(surface, (10, 14, 22), rect)

        cx, cy = x + w // 2, y + h // 2
        scale  = self._auto_scale(w, h)      # km per pixel

        def world_km_to_px(kx, ky):
            return int(cx + kx / scale), int(cy - ky / scale)

        # ── Earth ──────────────────────────────────────
        er_px = int(EARTH_RADIUS / 1000.0 / scale)
        if 3 < er_px < w:
            pygame.draw.circle(surface, (18, 45, 85), (cx, cy), er_px)
            pygame.draw.circle(surface, (30, 80, 150), (cx, cy), er_px, 2)
            # Faint atmosphere halo
            for i in range(3):
                pygame.draw.circle(surface, (20, 60, 120),
                                   (cx, cy), er_px + 2 + i * 2, 1)

        # ── Target orbit (dashed ring) ──────────────────
        orb_r_px = int((EARTH_RADIUS + self.orbit_alt) / 1000.0 / scale)
        if 3 < orb_r_px < w * 2:
            segs = 72
            for i in range(0, segs, 2):   # dashed: every other segment
                a0 = math.radians(i * 360 / segs)
                a1 = math.radians((i + 1) * 360 / segs)
                p0 = (int(cx + orb_r_px * math.cos(a0)),
                      int(cy - orb_r_px * math.sin(a0)))
                p1 = (int(cx + orb_r_px * math.cos(a1)),
                      int(cy - orb_r_px * math.sin(a1)))
                pygame.draw.line(surface, (*self.orbit_color, 120), p0, p1, 1)

        # ── Trajectory arc ──────────────────────────────
        if len(self.pts) > 1:
            tpts = [world_km_to_px(kx, ky) for kx, ky in self.pts]
            # Clip to rect
            clipped = [(max(x+1, min(x+w-1, px)), max(y+1, min(y+h-1, py)))
                       for px, py in tpts]
            pygame.draw.lines(surface, C_YELLOW, False, clipped, 2)

            # Current position crosshair
            lx, ly = clipped[-1]
            pygame.draw.circle(surface, C_YELLOW, (lx, ly), 5)
            pygame.draw.circle(surface, (255, 255, 255), (lx, ly), 3)
            for dx, dy in [(-10, 0), (10, 0), (0, -10), (0, 10)]:
                pygame.draw.line(surface, C_YELLOW,
                                 (lx, ly), (lx + dx, ly + dy), 1)

        # ── Axis labels ─────────────────────────────────
        ax_col = (60, 75, 100)
        km_per_half = int((w / 2) * scale)
        surface.blit(font_tiny.render(f"+{km_per_half:,} km", True, ax_col),
                     (x + w - 52, cy + 2))
        surface.blit(font_tiny.render(f"-{km_per_half:,} km", True, ax_col),
                     (x + 2, cy + 2))
        surface.blit(font_tiny.render(self.label, True, (100, 110, 130)),
                     (x + 4, y + 3))
        pygame.draw.rect(surface, C_AXIS, rect, 1)


# ── Scene Drawing ────────────────────────────────────────
def draw_stars(surface, alt):
    if alt > 20000:
        brightness = min(255, int((alt - 20000) / 80000 * 255))
        random.seed(12345)
        for _ in range(200):
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
                                   (mx + int(dx * mr), my + int(dy * mr)),
                                   max(1, int(cr * mr)), 1)


def draw_earth_detailed(surface, cam_x, cam_y, zoom):
    cx, cy = world_to_screen(0, 0, cam_x, cam_y, zoom)
    rp = int(EARTH_RADIUS * zoom)
    if rp < 5 or rp > 2e6:
        return
    for i in range(3):
        gr = rp + int(rp * 0.025 * (3 - i))
        if gr < 3000:
            pygame.draw.circle(surface, (40 + i * 30, 100 + i * 30, 180 + i * 15),
                               (cx, cy), gr, 3)
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
        if "GROUND_TEX" in globals() and globals().get("GROUND_TEX") is not None:
            tex = globals()["GROUND_TEX"]
            tw, th = tex.get_width(), tex.get_height()
            off = int((cam_x * zoom * 0.22) % tw)
            start_x = VIEW_X - off - tw
            start_y = max(gy, 0)
            for yy in range(start_y, VIEW_H, th):
                for xx in range(start_x, WIDTH, tw):
                    surface.blit(tex, (xx, yy))
        else:
            pygame.draw.rect(surface, C_GROUND, (VIEW_X, gy, VIEW_W, gh + 10))
        pygame.draw.rect(surface, C_GROUND_DK, (VIEW_X, gy, VIEW_W, max(2, int(3 * zoom))))
        haze = pygame.Surface((VIEW_W, 60), pygame.SRCALPHA)
        for i in range(60):
            a = int(90 * (1 - i / 60.0))
            pygame.draw.line(haze, (200, 215, 230, a), (0, i), (VIEW_W, i))
        surface.blit(haze, (VIEW_X, gy - 38))

    def ws(wx, wy):
        return world_to_screen(wx, wy + EARTH_RADIUS, cam_x, cam_y, zoom)

    p1 = ws(-25, 0); p2 = ws(25, 4)
    pw = p2[0] - p1[0]; ph = p1[1] - p2[1]
    if pw > 2:
        pad_rect = pygame.Rect(p1[0], p2[1], pw, ph)
        if "PAD_TEX" in globals() and globals().get("PAD_TEX") is not None:
            s = pygame.transform.smoothscale(globals()["PAD_TEX"], (max(2, pad_rect.w), max(2, pad_rect.h)))
            surface.blit(s, pad_rect.topleft)
            pygame.draw.rect(surface, (35, 35, 38), pad_rect, 2)
        else:
            pygame.draw.rect(surface, C_PAD, pad_rect)
        trench = pygame.Surface((pad_rect.w, pad_rect.h), pygame.SRCALPHA)
        pygame.draw.ellipse(trench, (15, 15, 18, 170), (pad_rect.w * 0.40, pad_rect.h * 0.15, pad_rect.w * 0.20, pad_rect.h * 0.70))
        pygame.draw.ellipse(trench, (0, 0, 0, 80), (pad_rect.w * 0.39, pad_rect.h * 0.12, pad_rect.w * 0.22, pad_rect.h * 0.76), 2)
        surface.blit(trench, pad_rect.topleft)
    t1 = ws(-8, -3); t2 = ws(8, 0)
    tw = t2[0] - t1[0]; th = t1[1] - t2[1]
    if tw > 1:
        pygame.draw.rect(surface, C_PAD_DARK, (t1[0], t2[1], tw, th))
    if abs(ws(-5, 0)[0] - ws(5, 0)[0]) > 1:
        pygame.draw.line(surface, C_ROAD, ws(-5, 0),  ws(-5, -200), max(1, int(10 * zoom)))
        pygame.draw.line(surface, C_ROAD, ws(5, 0),   ws(5, -200),  max(1, int(10 * zoom)))
    v1 = ws(-260, 0); v2 = ws(-140, 80)
    vw = v2[0] - v1[0]; vh = v1[1] - v2[1]
    if vw > 3:
        vab_rect = pygame.Rect(v1[0], v2[1], vw, vh)
        grad = pygame.Surface((vab_rect.w, vab_rect.h), pygame.SRCALPHA)
        for yy in range(vab_rect.h):
            t = yy / max(1, vab_rect.h - 1)
            col = lerp_color((90, 95, 110), (120, 125, 140), 0.2 + 0.7 * t)
            pygame.draw.line(grad, (*col, 255), (0, yy), (vab_rect.w, yy))
        surface.blit(grad, vab_rect.topleft)
        pygame.draw.rect(surface, (60, 65, 80), vab_rect, 2)
        pygame.draw.rect(surface, C_VAB_DOOR, (v1[0] + vw // 3, v2[1] + vh // 4, vw // 3, vh * 3 // 4))
    tw1 = ws(10, 0); tw2 = ws(16, 70)
    tww = tw2[0] - tw1[0]; twh = tw1[1] - tw2[1]
    if tww > 1:
        tower_rect = pygame.Rect(tw1[0], tw2[1], tww, twh)
        tower_grad = pygame.Surface((tower_rect.w, tower_rect.h), pygame.SRCALPHA)
        for yy in range(tower_rect.h):
            t = yy / max(1, tower_rect.h - 1)
            col = lerp_color((125, 118, 110), (175, 170, 160), 0.2 + 0.7 * t)
            pygame.draw.line(tower_grad, (*col, 255), (0, yy), (tower_rect.w, yy))
        surface.blit(tower_grad, tower_rect.topleft)
        pygame.draw.rect(surface, (70, 65, 60), tower_rect, 2)
        for yy in range(0, tower_rect.h, max(8, int(10 * zoom))):
            pygame.draw.line(surface, (70, 65, 60), (tower_rect.x, tower_rect.y + yy), (tower_rect.right, tower_rect.y + yy), 1)
        for ay in [25, 40]:
            a1 = ws(6, ay); a2 = ws(16, ay + 3)
            aw = a2[0] - a1[0]
            if aw > 1:
                pygame.draw.rect(surface, C_TOWER,
                                 (a1[0], a2[1], aw, max(a1[1] - a2[1], 2)))
    for lx in [-30, 30]:
        pygame.draw.line(surface, (180, 180, 180), ws(lx, 0), ws(lx, 85),
                         max(1, int(zoom)))


def draw_clouds_simple(surface, cam_x, cam_y, zoom, cloud_data):
    for cx, cy, cw, ch in cloud_data:
        sx, sy = world_to_screen(cx, cy + EARTH_RADIUS, cam_x, cam_y, zoom)
        pw = int(cw * zoom)
        ph = int(ch * zoom)
        if 2 < pw < 1500 and VIEW_X < sx < WIDTH and 0 < sy < VIEW_H:
            pygame.draw.ellipse(surface, (235, 240, 250),
                                (sx - pw // 2, sy - ph // 2, pw, ph))


def draw_rocket(surface, rocket, cam_x, cam_y, zoom, phase):
    rx, ry = rocket.x, rocket.y
    pitch = rocket.pitch_angle
    stage = rocket.current_stage_index
    base_sx, base_sy = world_to_screen(rx, ry, cam_x, cam_y, zoom)

    if base_sy > VIEW_H + 200 or base_sx < VIEW_X - 300 or base_sx > WIDTH + 300:
        return

    if phase == FlightPhase.SECO:
        cache = getattr(draw_rocket, "_sat_cache", None)
        if cache is None:
            cache = {}
            setattr(draw_rocket, "_sat_cache", cache)

        bus_w_px = max(10, int(3.6 * zoom))
        bus_h_px = max(8, int(2.6 * zoom))
        key = (bus_w_px, bus_h_px)
        spr = cache.get(key)
        if spr is None:
            spr = render_satellite_sprite(bus_w_px, bus_h_px)
            cache[key] = spr

        vmag = math.hypot(rocket.vx, rocket.vy)
        ang = math.atan2(rocket.vy, rocket.vx) if vmag > 0.1 else pitch
        rot_deg = math.degrees(ang)
        rot = pygame.transform.rotate(spr, -rot_deg)
        rect = rot.get_rect(center=(base_sx, base_sy))

        glint = pygame.Surface((rot.get_width(), rot.get_height()), pygame.SRCALPHA)
        glint.blit(rot, (0, 0))
        glint.fill((255, 255, 255, 40), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(glint, (rect.x + 1, rect.y - 1))
        surface.blit(rot, rect.topleft)
        return

    core_h_m = 64.0
    if stage >= 2:
        core_h_m = 40.0

    core_h_px = int(core_h_m * zoom)
    core_w_px = int(8.4 * zoom)

    if core_h_px < 18 or core_w_px < 6:
        pygame.draw.circle(surface, C_WHITE, (base_sx, base_sy), max(2, int(2 * zoom)))
        return

    cache = getattr(draw_rocket, "_sprite_cache", None)
    if cache is None:
        cache = {}
        setattr(draw_rocket, "_sprite_cache", cache)

    key = (core_h_px, core_w_px, stage, bool(rocket.fairing_attached))
    spr = cache.get(key)
    if spr is None:
        spr = render_rocket_sprite(core_h_px, core_w_px, stage, rocket.fairing_attached)
        cache[key] = spr

    rot_deg = math.degrees(pitch - math.pi / 2.0)
    rot = pygame.transform.rotate(spr, rot_deg)

    ppm = max(0.00001, core_w_px / 8.4)
    nose_h = max(14, int(9.0 * ppm))
    base_y = nose_h + 2 + core_h_px
    center_local = pygame.math.Vector2(spr.get_width() / 2.0, spr.get_height() / 2.0)
    base_local = pygame.math.Vector2(spr.get_width() / 2.0, float(base_y))
    off = base_local - center_local
    off_rot = off.rotate(rot_deg)
    center_pos = pygame.math.Vector2(base_sx, base_sy) - off_rot
    rect = rot.get_rect(center=(int(center_pos.x), int(center_pos.y)))

    if base_sy < VIEW_H:
        sh = pygame.Surface((rot.get_width(), rot.get_height()), pygame.SRCALPHA)
        sh.blit(rot, (0, 0))
        sh.fill((0, 0, 0, 90), special_flags=pygame.BLEND_RGBA_MULT)
        sx = rect.x + int(8 * zoom)
        sy = rect.y + int(6 * zoom)
        surface.blit(sh, (sx, sy))

    surface.blit(rot, rect.topleft)


def draw_debris(surface, debris, cam_x, cam_y, zoom):
    for d in debris:
        sx, sy = world_to_screen(d["x"], d["y"], cam_x, cam_y, zoom)
        size = max(2, int(5 * zoom))
        if VIEW_X < sx < WIDTH and 0 < sy < VIEW_H:
            pygame.draw.rect(surface, C_ORANGE, (sx - size, sy - size, size * 2, size))


# ── Left Sidebar ─────────────────────────────────────────
def draw_sidebar(surface, font, font_sm, font_tiny, rocket, world,
                 manual_throttle, manual_pitch_offset, cam_mode, vehicle_name):
    pygame.draw.rect(surface, C_SIDE_BG, (0, 0, SIDE_W, HEIGHT))
    pygame.draw.line(surface, C_DASH_LINE, (SIDE_W - 1, 0), (SIDE_W - 1, HEIGHT), 1)

    x = 8; y = 8

    # Vehicle name badge
    pygame.draw.rect(surface, (18, 28, 45), (x, y, SIDE_W - 16, 28), border_radius=5)
    pygame.draw.rect(surface, C_CYAN, (x, y, SIDE_W - 16, 28), 1, border_radius=5)
    vn = font_sm.render(vehicle_name[:18], True, C_CYAN)
    surface.blit(vn, (x + (SIDE_W - 16 - vn.get_width()) // 2, y + 6))
    y += 36

    surface.blit(font.render("MANUAL CTRL", True, C_YELLOW), (x, y)); y += 22
    surface.blit(font_sm.render(f"Throttle: {manual_throttle * 100:.0f}%", True, C_TEXT), (x, y)); y += 16
    bw = SIDE_W - 20
    pygame.draw.rect(surface, (40, 40, 40), (x, y, bw, 12))
    fill = int(bw * manual_throttle)
    bc = C_GREEN_GO if manual_throttle > 0.3 else C_YELLOW if manual_throttle > 0.1 else C_RED
    pygame.draw.rect(surface, bc, (x, y, fill, 12))
    pygame.draw.rect(surface, C_DASH_LINE, (x, y, bw, 12), 1); y += 20

    pitch_deg = math.degrees(rocket.pitch_angle) if hasattr(rocket, 'pitch_angle') else 90
    surface.blit(font_sm.render(f"Pitch: {pitch_deg:.1f}°", True, C_TEXT), (x, y)); y += 16
    surface.blit(font_tiny.render(f"Offset: {manual_pitch_offset:.2f}", True, (120, 120, 120)), (x, y)); y += 20

    cam_names = ["TRACKING", "WIDE", "ORBITAL", "GOPRO"]
    surface.blit(font_sm.render(f"Cam: {cam_names[cam_mode]}", True, C_CYAN), (x, y)); y += 20

    for hint in ["W/S   Pitch", "Q/E   Throttle", "←/→   Warp",
                 "Scroll Zoom", "Space  Launch", "C      Camera", "R      New Mission"]:
        surface.blit(font_tiny.render(hint, True, (90, 100, 120)), (x, y)); y += 13
    y += 8

    # Gravity box
    pygame.draw.rect(surface, (18, 24, 38), (x, y, SIDE_W - 16, 108))
    pygame.draw.rect(surface, C_DASH_LINE, (x, y, SIDE_W - 16, 108), 1)
    surface.blit(font_sm.render("GRAVITY DATA", True, C_CYAN), (x + 4, y + 3)); y += 18
    alt = rocket.get_altitude()
    r   = EARTH_RADIUS + alt
    g_acc  = G * EARTH_MASS / (r * r) if r > 0 else 9.81
    surface.blit(font_tiny.render(f"g: {g_acc:.4f} m/s²", True, C_TEXT), (x + 4, y)); y += 13
    surface.blit(font_tiny.render(f"g/g₀: {g_acc / 9.81:.4f}", True, C_TEXT), (x + 4, y)); y += 13
    wt = rocket.get_total_mass() * g_acc
    surface.blit(font_tiny.render(f"Wt: {wt / 1000:.1f} kN", True, C_TEXT), (x + 4, y)); y += 13
    v_esc = math.sqrt(2 * G * EARTH_MASS / r) if r > 0 else 0
    surface.blit(font_tiny.render(f"V_esc: {v_esc:.0f} m/s", True, C_TEXT), (x + 4, y)); y += 13
    v_orb = math.sqrt(G * EARTH_MASS / r) if r > 0 else 0
    surface.blit(font_tiny.render(f"V_orb: {v_orb:.0f} m/s", True, C_TEXT), (x + 4, y)); y += 22

    # Orbital mechanics box
    pygame.draw.rect(surface, (18, 24, 38), (x, y, SIDE_W - 16, 98))
    pygame.draw.rect(surface, C_DASH_LINE, (x, y, SIDE_W - 16, 98), 1)
    surface.blit(font_sm.render("ORBITAL MECH", True, C_MAGENTA), (x + 4, y + 3)); y += 18
    vel = rocket.get_velocity_mag()
    soe = 0.5 * vel * vel - G * EARTH_MASS / r if r > 0 else 0
    surface.blit(font_tiny.render(f"E_sp: {soe/1e6:.2f} MJ/kg", True, C_TEXT), (x + 4, y)); y += 13
    a   = -G * EARTH_MASS / (2 * soe) if soe != 0 else r
    peri_alt = (r - EARTH_RADIUS) / 1000.0
    apo_alt  = max(0, (a * 2 - r - EARTH_RADIUS) / 1000.0) if a > 0 else 0
    surface.blit(font_tiny.render(f"Apo:  {apo_alt:.0f} km", True, C_TEXT), (x + 4, y)); y += 13
    surface.blit(font_tiny.render(f"Peri: {peri_alt:.0f} km", True, C_TEXT), (x + 4, y)); y += 13
    if a > 0:
        period = 2 * math.pi * math.sqrt(a ** 3 / (G * EARTH_MASS))
        surface.blit(font_tiny.render(f"T: {period/60:.0f} min", True, C_TEXT), (x + 4, y))
    else:
        surface.blit(font_tiny.render("T: N/A", True, C_TEXT), (x + 4, y))


# ── Bottom Dashboard ─────────────────────────────────────
def draw_dashboard(surface, font, font_sm, font_tiny, rocket, world,
                   graphs, traj_map, orbit_id):
    dy = VIEW_H
    pygame.draw.rect(surface, C_DASH_BG, (0, dy, WIDTH, DASH_H))
    pygame.draw.line(surface, C_DASH_LINE, (0, dy), (WIDTH, dy), 2)

    alt = rocket.get_altitude()
    vel = rocket.get_velocity_mag()
    stg = rocket.current_stage_index
    stg_name = rocket.stages[stg].name if stg < len(rocket.stages) else "COAST"

    # ── Column 0: Key Numbers ─────────────────────────
    col_x = 10; ly = dy + 10
    surface.blit(font_sm.render("TELEMETRY", True, C_YELLOW), (col_x, ly)); ly += 20

    def kv(label, val, unit, color=C_TEXT):
        surface.blit(font_tiny.render(label, True, (120, 130, 150)), (col_x, ly))
        v_surf = font_sm.render(f"{val} {unit}", True, color)
        surface.blit(v_surf, (col_x, ly + 12))

    pairs = [
        ("Velocity",   f"{vel:.1f}",              "m/s",  C_GREEN_GO),
        ("Altitude",   f"{alt/1000:.3f}",          "km",   C_CYAN),
        ("Range (x)",  f"{rocket.x/1000:.1f}",    "km",   C_TEXT),
        ("Mass",       f"{rocket.get_total_mass()/1000:.2f}", "t", C_TEXT),
        ("Stage",      stg_name[:14],              "",     C_YELLOW),
    ]
    for label, val, unit, color in pairs:
        surface.blit(font_tiny.render(label, True, (100, 110, 130)), (col_x, ly))
        surface.blit(font_sm.render(f"{val} {unit}", True, color), (col_x, ly + 12))
        ly += 28

    # Fuel bar
    if stg < len(rocket.stages):
        fs  = rocket.stages[stg].fuel_system
        fp  = fs.fuel / (fs.initial_fuel + 0.001) * 100
        fw_ = 148; fh_ = 12
        pygame.draw.rect(surface, (35, 38, 48), (col_x, ly, fw_, fh_))
        fc  = C_GREEN_GO if fp > 40 else C_YELLOW if fp > 15 else C_RED
        pygame.draw.rect(surface, fc, (col_x, ly, int(fw_ * fp / 100), fh_))
        pygame.draw.rect(surface, C_DASH_LINE, (col_x, ly, fw_, fh_), 1)
        surface.blit(font_tiny.render(f"FUEL {fp:.1f}%", True, C_TEXT),
                     (col_x, ly + fh_ + 2))
        ly += 24

    # G-Force readout
    gf = graphs["gforce_val"]
    gcol = C_GREEN_GO if gf < 3 else C_YELLOW if gf < 6 else C_RED
    surface.blit(font_tiny.render("G-Force", True, (100, 110, 130)), (col_x, ly))
    surface.blit(font.render(f"{gf:.2f} g", True, gcol), (col_x, ly + 12))

    # ── Columns 1–6: SciGraphs ─────────────────────────
    # Graph layout: 6 graphs, 2 rows of 3
    GW = 186; GH = 132; GAP = 8
    gx0 = col_x + 158   # start after telemetry column

    graph_rows = [
        # Row 1
        [("alt",    "Altitude",          "km",   C_CYAN),
         ("vel",    "Velocity",          "m/s",  (255, 140, 0)),
         ("maxq",   "Dyn. Pressure",     "kPa",  C_RED)],
        # Row 2
        [("gforce", "G-Force",           "g",    C_MAGENTA),
         ("thrust", "Thrust",            "kN",   C_YELLOW),
         ("fuel_g", "Propellant Mass %", "%",    C_GREEN_GO)],
    ]

    for row_i, row in enumerate(graph_rows):
        ry = dy + 10 + row_i * (GH + GAP)
        for col_i, (key, label, unit, color) in enumerate(row):
            rx = gx0 + col_i * (GW + GAP)
            graphs[key].draw(surface, pygame.Rect(rx, ry, GW, GH),
                             font_tiny)

    # ── Column 7: Trajectory Map ───────────────────────
    MAP_W = 258; MAP_H = GH * 2 + GAP
    map_x = gx0 + 3 * (GW + GAP)
    map_y = dy + 10
    traj_map.draw(surface, pygame.Rect(map_x, map_y, MAP_W, MAP_H), font_tiny)

    # ── Column 8: System Status ─────────────────────────
    sx = map_x + MAP_W + 10
    sy = dy + 10

    surface.blit(font_sm.render("SYS STATUS", True, C_CYAN), (sx, sy)); sy += 20
    systems = [
        ("Avionics",    "GO",  C_GREEN_GO),
        ("Propulsion",  "GO" if stg < len(rocket.stages) and rocket.stages[stg].active else "COAST", C_GREEN_GO),
        ("ADCS",        "GO",  C_GREEN_GO),
        ("Thermal",     "GO",  C_GREEN_GO),
        ("TT&C",        "GO",  C_GREEN_GO),
        ("Navigation",  "GO",  C_GREEN_GO),
        ("Payload",     "STBY", C_YELLOW),
    ]
    for name, status, col in systems:
        surface.blit(font_tiny.render(name, True, (140, 150, 165)), (sx, sy))
        surface.blit(font_tiny.render(status, True, col), (sx + 78, sy))
        sy += 16

    sy += 6
    # Phase, time, warp
    orb_data  = ORBITS.get(orbit_id, {})
    orb_color = orb_data.get("color", C_CYAN)
    phase_str = PHASE_NAMES.get(world.phase, "?")
    surface.blit(font_tiny.render("MISSION PHASE", True, (100, 110, 130)), (sx, sy)); sy += 14
    surface.blit(font_sm.render(phase_str, True, C_YELLOW), (sx, sy)); sy += 18

    surface.blit(font_tiny.render("TARGET ORBIT", True, (100, 110, 130)), (sx, sy)); sy += 14
    surface.blit(font_sm.render(orb_data.get("name", orbit_id), True, orb_color), (sx, sy)); sy += 18

    surface.blit(font_tiny.render(f"MET  {format_time(world.time_elapsed)}", True, C_TEXT), (sx, sy)); sy += 16
    surface.blit(font_tiny.render(f"WARP {world.time_warp:.0f}×", True, C_TEXT), (sx, sy))


def draw_hud(surface, font, font_lg, world, phase, vehicle_name, orbit_id):
    surface.blit(
        font.render(f"T+{format_time(world.time_elapsed)}  |  WARP {world.time_warp:.0f}×",
                    True, C_TEXT), (VIEW_X + 10, 8))
    phase_str = PHASE_NAMES.get(phase, "?")
    ps = font_lg.render(f"  {phase_str}  ", True, C_YELLOW, (12, 14, 20))
    surface.blit(ps, (VIEW_X + VIEW_W // 2 - ps.get_width() // 2, 28))

    # Top-right: vehicle + orbit badge
    orb_col = ORBITS.get(orbit_id, {}).get("color", C_CYAN)
    badge = font.render(f"{vehicle_name}  ·  {orbit_id}", True, orb_col)
    bx = WIDTH - badge.get_width() - 16
    pygame.draw.rect(surface, (12, 16, 24), (bx - 6, 4, badge.get_width() + 12, 24), border_radius=4)
    pygame.draw.rect(surface, orb_col, (bx - 6, 4, badge.get_width() + 12, 24), 1, border_radius=4)
    surface.blit(badge, (bx, 8))

    # Restart button
    pygame.draw.rect(surface, (50, 55, 65), (WIDTH - 120, HEIGHT - 36, 110, 28), border_radius=4)
    pygame.draw.rect(surface, C_DASH_LINE, (WIDTH - 120, HEIGHT - 36, 110, 28), 1, border_radius=4)
    surface.blit(font.render("R - New Mission", True, C_TEXT), (WIDTH - 115, HEIGHT - 30))


# ── Main ─────────────────────────────────────────────────
def run_app():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Satellite Mission Simulator")
    clock  = pygame.time.Clock()

    font      = pygame.font.SysFont("Menlo", 14)
    font_sm   = pygame.font.SysFont("Menlo", 12)
    font_lg   = pygame.font.SysFont("Menlo", 16, bold=True)
    font_tiny = pygame.font.SysFont("Menlo", 10)

    sky_cache = build_sky_cache()
    global GROUND_TEX, PAD_TEX
    GROUND_TEX = build_ground_texture()
    PAD_TEX = build_pad_texture()

    fx_surf = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
    particles = []

    random.seed(42)
    clouds = [(random.uniform(-20000, 20000),
               random.uniform(1500, 8000),
               random.uniform(150, 700),
               random.uniform(40, 160)) for _ in range(80)]

    # ── Vehicle / Orbit Selection ─────────────────────────
    def do_selection():
        return run_selection(screen, clock, FPS)

    def init_world(vid, oid):
        m = MissionProfile(vid, oid)
        w = World(m); w.time_warp = 1.0
        return w

    def make_graphs():
        return {
            "alt":    SciGraph(120, "Altitude",        "km",  C_CYAN),
            "vel":    SciGraph(120, "Velocity",        "m/s", (255, 140, 0)),
            "maxq":   SciGraph(120, "Dyn. Pres.",      "kPa", C_RED),
            "gforce": SciGraph(120, "G-Force",         "g",   C_MAGENTA, y_min_fixed=0),
            "thrust": SciGraph(120, "Thrust",          "kN",  C_YELLOW,  y_min_fixed=0),
            "fuel_g": SciGraph(120, "Propellant",      "%",   C_GREEN_GO, y_min_fixed=0, y_max_fixed=100),
            "gforce_val": 1.0,
        }

    def make_traj(oid):
        orb     = ORBITS.get(oid, {})
        alt_m   = orb.get("target_altitude_m", 400000.0)
        color   = orb.get("color", C_CYAN)
        return TrajectoryMap(400, label=f"Orbit: {oid}", orbit_alt_m=alt_m, orbit_color=color)

    # ── First run: selection ──────────────────────────────
    vid, oid = do_selection()
    world   = init_world(vid, oid)
    graphs  = make_graphs()
    traj    = make_traj(oid)

    gt = 0.0; lv = 0.0
    cam_mode = 0
    manual_pitch = 0.0; manual_throttle = 1.0
    zoom_override = None
    running = True

    vehicle_name = VEHICLES[vid]["name"]

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
                    if world.time_warp < 100: world.time_warp *= 2
                elif event.key == pygame.K_LEFT:
                    if world.time_warp > 1: world.time_warp /= 2
                elif event.key == pygame.K_c:
                    cam_mode = (cam_mode + 1) % 4
                    zoom_override = None
                elif event.key == pygame.K_r:
                    # New mission — show selection screen again
                    vid, oid = do_selection()
                    world    = init_world(vid, oid)
                    graphs   = make_graphs()
                    traj     = make_traj(oid)
                    lv = 0; cam_mode = 0
                    manual_pitch = 0.0; manual_throttle = 1.0
                    zoom_override = None
                    vehicle_name = VEHICLES[vid]["name"]

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    zoom_override = (zoom_override or 1.0) * 1.3
                elif event.button == 5:
                    zoom_override = max((zoom_override or 1.0) / 1.3, 0.0001)

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
        alt    = rocket.get_altitude()
        vel    = rocket.get_velocity_mag()
        is_active = (
            rocket.current_stage_index < len(rocket.stages)
            and rocket.stages[rocket.current_stage_index].active
            and world.phase != FlightPhase.PRELAUNCH
            and world.phase != FlightPhase.SECO
        )
        if is_active:
            spawn_exhaust(particles, rocket, manual_throttle, dt, intensity=1.0)
        update_particles(particles, dt)

        # ── Camera ────────────────────────────────────────
        if cam_mode == 0:
            if alt < 200:
                cam_x, cam_y = 0, EARTH_RADIUS + 35; base_zoom = 4.5
            elif alt < 5000:
                cam_x = rocket.x; cam_y = rocket.y
                base_zoom = max(1.0, 4.5 - alt / 2000.0)
            else:
                cam_x = rocket.x; cam_y = rocket.y
                base_zoom = max(0.08, 1.0 - alt / 100000.0)
        elif cam_mode == 1:
            cam_x = rocket.x; cam_y = rocket.y
            base_zoom = max(0.005, 0.3 - alt / 500000.0)
        elif cam_mode == 2:
            cam_x = rocket.x; cam_y = rocket.y
            base_zoom = max(0.00005, 0.0005 - alt / 100000000.0)
        elif cam_mode == 3:
            cam_x = rocket.x + 15 * math.cos(rocket.pitch_angle + 0.3)
            cam_y = rocket.y  + 15 * math.sin(rocket.pitch_angle + 0.3)
            base_zoom = 8.0

        zoom = zoom_override if zoom_override is not None else base_zoom
        zoom = max(zoom, 0.000005)

        # ── Graph updates every 0.25 s ──────────────────
        gt += dt
        if gt >= 0.25:
            accel = (vel - lv) / gt if gt > 0 else 0
            lv = vel
            gf = abs(accel / 9.81)
            if alt < 10: gf = 1.0
            graphs["gforce_val"] = gf
            rho = 1.225 * math.exp(-alt / 8500.0) if alt > 0 else 1.225
            q   = 0.5 * rho * vel ** 2
            graphs["alt"].push(alt / 1000.0)
            graphs["vel"].push(vel)
            graphs["maxq"].push(q / 1000.0)
            graphs["gforce"].push(gf)
            stg = rocket.current_stage_index
            tkn = (rocket.stages[stg].thrust_sl / 1000.0
                   if stg < len(rocket.stages) and rocket.stages[stg].active else 0)
            graphs["thrust"].push(tkn)
            if stg < len(rocket.stages):
                fs = rocket.stages[stg].fuel_system
                graphs["fuel_g"].push(fs.fuel / (fs.initial_fuel + 0.001) * 100)
            else:
                graphs["fuel_g"].push(0)
            traj.push(rocket.x, rocket.y)
            gt = 0.0

        # ── Draw ─────────────────────────────────────────
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
        draw_particles(screen, fx_surf, particles, cam_x, cam_y, zoom)
        draw_rocket(screen, rocket, cam_x, cam_y, zoom, world.phase)

        draw_sidebar(screen, font, font_sm, font_tiny, rocket, world,
                     manual_throttle, manual_pitch, cam_mode, vehicle_name)
        draw_dashboard(screen, font, font_sm, font_tiny, rocket, world,
                       graphs, traj, oid)
        draw_hud(screen, font, font_lg, world, world.phase, vehicle_name, oid)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
