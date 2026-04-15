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
        pygame.draw.line(surface, C_ROAD, ws(-5, 0),  ws(-5, -200), max(1, int(10 * zoom)))
        pygame.draw.line(surface, C_ROAD, ws(5, 0),   ws(5, -200),  max(1, int(10 * zoom)))
    v1 = ws(-260, 0); v2 = ws(-140, 80)
    vw = v2[0] - v1[0]; vh = v1[1] - v2[1]
    if vw > 3:
        pygame.draw.rect(surface, C_VAB, (v1[0], v2[1], vw, vh))
        pygame.draw.rect(surface, C_VAB_DOOR,
                         (v1[0] + vw // 3, v2[1] + vh // 4, vw // 3, vh * 3 // 4))
    tw1 = ws(10, 0); tw2 = ws(16, 70)
    tww = tw2[0] - tw1[0]; twh = tw1[1] - tw2[1]
    if tww > 1:
        pygame.draw.rect(surface, C_TOWER, (tw1[0], tw2[1], tww, twh))
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
    alt = rocket.get_altitude()
    rx, ry = rocket.x, rocket.y
    pitch  = rocket.pitch_angle

    def ro(dx, dy):
        c = math.cos(pitch); s = math.sin(pitch)
        return rx + dx * (-s) + dy * c, ry + dx * c + dy * s

    def draw_part(dx, dy, w, h, color):
        corners = [(-w/2, 0), (w/2, 0), (w/2, h), (-w/2, h)]
        sc = [world_to_screen(*ro(dx + cx, dy + cy), cam_x, cam_y, zoom)
              for cx, cy in corners]
        pygame.draw.polygon(surface, color, sc)
        pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in color), sc, 1)

    def draw_tri(dx, dy, w, h, color):
        pts = [(-w/2, 0), (w/2, 0), (0, h)]
        sc  = [world_to_screen(*ro(dx + cx, dy + cy), cam_x, cam_y, zoom)
               for cx, cy in pts]
        pygame.draw.polygon(surface, color, sc)

    if rocket.current_stage_index == 0:
        for side in [-5.5, 5.5]:
            draw_part(side, 0,  3.6, 30, C_WHITE)
            draw_tri(side,  30, 3.6,  4, C_WHITE)
            draw_tri(side,  -3, 2.4, -3, C_NOZZLE)
    if rocket.current_stage_index <= 1:
        draw_part(0, 0,  8.4, 42, C_ORANGE)
        for nx in [-2, 0, 2]:
            draw_tri(nx, -2, 1.6, -2.5, C_NOZZLE)
    draw_part(0, 42, 7,  8, C_WHITE)
    draw_part(0, 50, 5,  5, C_WHITE)
    draw_tri(0,  55, 5,  5, C_WHITE)
    sb  = world_to_screen(*ro(0, 60), cam_x, cam_y, zoom)
    st_ = world_to_screen(*ro(0, 64), cam_x, cam_y, zoom)
    pygame.draw.line(surface, (150, 150, 150), sb, st_, max(1, int(0.3 * zoom)))

    is_active = (rocket.current_stage_index < len(rocket.stages)
                 and rocket.stages[rocket.current_stage_index].active)
    if is_active and phase != FlightPhase.PRELAUNCH:
        vac = 1.0 + min(alt / 40000.0, 3.0)
        fw = (8.0 if rocket.current_stage_index == 0 else 4.0) * vac
        fl = random.uniform(15, 28) * vac
        draw_tri(0, -3, fw * 1.2, -fl,        C_FLAME_OUT)
        draw_tri(0, -3, fw * 0.7, -fl * 0.8,  C_FLAME_MID)
        draw_tri(0, -3, fw * 0.3, -fl * 0.6,  C_FLAME_IN)


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
        draw_rocket(screen, rocket, cam_x, cam_y, zoom, world.phase)

        draw_sidebar(screen, font, font_sm, font_tiny, rocket, world,
                     manual_throttle, manual_pitch, cam_mode, vehicle_name)
        draw_dashboard(screen, font, font_sm, font_tiny, rocket, world,
                       graphs, traj, oid)
        draw_hud(screen, font, font_lg, world, world.phase, vehicle_name, oid)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
