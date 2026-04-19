# rendering_pygame/vehicle_select.py
"""
Pre-launch vehicle selection screen for the Satellite Mission Simulator.
Shows all available launch vehicles and target orbits.
Returns (vehicle_id, orbit_id) when the user clicks LAUNCH.
"""
import pygame
import math
import sys

from mission.vehicle_database import VEHICLES
from mission.orbit_targets import ORBITS
from mission.parts_database import ENGINES, FUEL_TANKS, FAIRINGS

# ── Palette ──────────────────────────────────────────────
BG          = (8, 12, 20)
PANEL_BG    = (14, 20, 32)
PANEL_DARK  = (10, 14, 24)
BORDER      = (40, 55, 80)
BORDER_SEL  = (0, 180, 255)
TEXT_HI     = (230, 235, 245)
TEXT_DIM    = (120, 130, 150)
TEXT_TINY   = (80, 90, 110)
ACCENT_CYAN = (0, 200, 255)
ACCENT_GOLD = (255, 200, 60)
ACCENT_GRN  = (40, 220, 100)
ACCENT_RED  = (255, 70, 60)
ACCENT_MAG  = (200, 80, 240)


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_rounded_rect(surf, color, rect, radius=8, border_color=None, border_w=1):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(surf, border_color, rect, border_w, border_radius=radius)


def draw_glow_text(surf, text, font, color, pos, glow_color=None, glow_passes=2):
    if glow_color:
        for d in range(glow_passes, 0, -1):
            alpha = int(120 / d)
            glow_surf = font.render(text, True, (*glow_color, alpha))
            for ox, oy in [(-d, 0), (d, 0), (0, -d), (0, d)]:
                surf.blit(glow_surf, (pos[0] + ox, pos[1] + oy))
    surf.blit(font.render(text, True, color), pos)


# ASCII rocket art per vehicle code
ROCKET_ART = {
    "F9":  ["  /\\  ", " /  \\ ", " |  | ", " |  | ", " \\__/ "],
    "AV":  ["  /\\  ", " /AT\\ ", " |LAS| ", " | V | ", " \\__/ "],
    "A5":  [" /\\/\\ ", "/Ari \\ ", "|  5  |", "|  E  |", "\\____/"],
    "EL":  ["  /\\  ", " /EL\\ ", " |  | ", " \\__/ "],
    "S2":  ["  /\\  ", " /SO\\ ", " |YUZ| ", " | 2 | ", " \\__/ "],
    "PX":  ["  /\\  ", " /PS\\ ", " |LV\\ ", " |  | ", " \\__/ "],
    "??":  ["  /\\  ", " /??\\ ", " |??| ", " |??| ", " \\__/ "],
}

# Orbit badge colors map
ORBIT_COLORS = {
    "LEO": (0, 200, 255),
    "SSO": (60, 220, 100),
    "MEO": (255, 200, 50),
    "GTO": (210, 80, 240),
}


class CustomRocketBuilder:
    def __init__(self, screen, font_body, font_head, font_small, font_tiny):
        self.screen = screen
        self.W, self.H = screen.get_size()
        self.f_body = font_body
        self.f_head = font_head
        self.f_small = font_small
        self.f_tiny = font_tiny
        self.f_title = pygame.font.SysFont("Menlo", 24, bold=True)
        self.f_huge = pygame.font.SysFont("Menlo", 40, bold=True)

        self.custom_data = VEHICLES["CUSTOM"]
        
        # Available parts lists
        self.engine_ids = list(ENGINES.keys())
        self.tank_ids = list(FUEL_TANKS.keys())
        self.fairing_ids = list(FAIRINGS.keys())

        # Current selections
        self.sel_parts = {
            "s1_tank": 2, # LARGE
            "s1_engine": 1, # RD-180
            "s1_engine_count": 1,
            "s2_tank": 1, # MEDIUM
            "s2_engine": 5, # MERLIN_VAC
            "fairing": 1, # STANDARD
        }

        self.fields = [
            {"label": "Rocket Name", "key": "name", "type": "text", "val": str(self.custom_data["name"])},
            {"label": "S1 Fuel Tank", "key": "s1_tank", "type": "part", "options": self.tank_ids, "db": FUEL_TANKS},
            {"label": "S1 Engine", "key": "s1_engine", "type": "part", "options": self.engine_ids, "db": ENGINES},
            {"label": "S1 Engine Count", "key": "s1_engine_count", "type": "num", "val": "1"},
            {"label": "S2 Fuel Tank", "key": "s2_tank", "type": "part", "options": self.tank_ids, "db": FUEL_TANKS},
            {"label": "S2 Engine", "key": "s2_engine", "type": "part", "options": self.engine_ids, "db": ENGINES},
            {"label": "Fairing Type", "key": "fairing", "type": "part", "options": self.fairing_ids, "db": FAIRINGS},
            {"label": "Drag Coeff (Cd)", "key": "drag_coefficient", "type": "num", "val": str(self.custom_data["drag_coefficient"])},
            {"label": "Rocket Area (m2)", "key": "cross_sectional_area", "type": "num", "val": str(self.custom_data["cross_sectional_area"])},
        ]
        
        self.active_field = 0
        self.rects = []
        self._update_stats()

    def _update_stats(self):
        """Calculate dry mass, propellant mass, thrust, and delta-v based on selected parts."""
        # S1
        t1 = FUEL_TANKS[self.tank_ids[self.sel_parts["s1_tank"]]]
        e1 = ENGINES[self.engine_ids[self.sel_parts["s1_engine"]]]
        ec1 = int(self.fields[3]["val"]) if self.fields[3]["val"].isdigit() else 1
        
        s1_dry = t1["dry_mass"] + (e1["mass"] * ec1)
        s1_fuel = t1["propellant_mass"]
        s1_t_sl = e1["thrust_sl"] * ec1
        s1_t_vac = e1["thrust_vac"] * ec1
        s1_isp = e1["isp_vac"]
        s1_power = e1.get("power_draw_kw", 0) * ec1
        s1_batt = t1.get("battery_capacity_kwh", 0)
        
        # S2
        t2 = FUEL_TANKS[self.tank_ids[self.sel_parts["s2_tank"]]]
        e2 = ENGINES[self.engine_ids[self.sel_parts["s2_engine"]]]
        
        s2_dry = t2["dry_mass"] + e2["mass"]
        s2_fuel = t2["propellant_mass"]
        s2_t_vac = e2["thrust_vac"]
        s2_isp = e2["isp_vac"]
        s2_power = e2.get("power_draw_kw", 0)
        s2_batt = t2.get("battery_capacity_kwh", 0)

        # Fairing
        f = FAIRINGS[self.fairing_ids[self.sel_parts["fairing"]]]
        
        # Total Stats
        m_payload = 1000 # Assume 1t payload for dV calc
        m_f = f["mass"]
        
        # dV = Isp * g0 * ln(m0/m1)
        g0 = 9.80665
        
        # Stage 2 dV
        m0_2 = s2_dry + s2_fuel + m_payload
        m1_2 = s2_dry + m_payload
        dv2 = s2_isp * g0 * math.log(m0_2 / m1_2) if m1_2 > 0 and s2_isp > 0 else 0
        
        # Stage 1 dV (including S2 mass + fairing as payload)
        m_s2_total = s2_dry + s2_fuel + m_payload + m_f
        m0_1 = s1_dry + s1_fuel + m_s2_total
        m1_1 = s1_dry + m_s2_total
        dv1 = s1_isp * g0 * math.log(m0_1 / m1_1) if m1_1 > 0 and s1_isp > 0 else 0
        
        self.total_dv = dv1 + dv2
        self.total_mass = m0_1
        self.s1_twr = s1_t_sl / (self.total_mass * g0) if self.total_mass > 0 else 0
        
        # Power / Electricity
        self.total_power_draw = s1_power + s2_power
        self.total_batt = s1_batt + s2_batt

        # Update custom_data for simulation
        self.custom_data["stages"][0]["dry_mass"] = s1_dry
        self.custom_data["stages"][0]["propellant_mass"] = s1_fuel
        self.custom_data["stages"][0]["thrust_sl"] = s1_t_sl
        self.custom_data["stages"][0]["thrust_vac"] = s1_t_vac
        self.custom_data["stages"][0]["burn_time"] = s1_fuel / (s1_t_vac / (s1_isp * g0)) if s1_isp > 0 and s1_t_vac > 0 else 150
        
        self.custom_data["stages"][1]["dry_mass"] = s2_dry
        self.custom_data["stages"][1]["propellant_mass"] = s2_fuel
        self.custom_data["stages"][1]["thrust_sl"] = 0
        self.custom_data["stages"][1]["thrust_vac"] = s2_t_vac
        self.custom_data["stages"][1]["burn_time"] = s2_fuel / (s2_t_vac / (s2_isp * g0)) if s2_isp > 0 and s2_t_vac > 0 else 300

        self.custom_data["fairing"]["mass"] = f["mass"]
        self.custom_data["fairing"]["jettison_altitude"] = f["jettison_altitude"]
        
        self.custom_data["drag_coefficient"] = float(self.fields[7]["val"]) if self.fields[7]["val"].replace('.','',1).isdigit() else 0.4
        self.custom_data["cross_sectional_area"] = float(self.fields[8]["val"]) if self.fields[8]["val"].replace('.','',1).isdigit() else 10.0
        self.custom_data["name"] = self.fields[0]["val"]

    def _draw_rocket_preview(self, rect):
        """Draw a simple 2D visualization of the rocket based on selected parts."""
        cx, cy = rect.centerx, rect.bottom - 40
        
        # Scaling
        s1_h = 140 if "LARGE" in self.tank_ids[self.sel_parts["s1_tank"]] else 100 if "MEDIUM" in self.tank_ids[self.sel_parts["s1_tank"]] else 60
        s2_h = 80 if "LARGE" in self.tank_ids[self.sel_parts["s2_tank"]] else 60 if "MEDIUM" in self.tank_ids[self.sel_parts["s2_tank"]] else 40
        w = 40 if "LARGE" in self.tank_ids[self.sel_parts["s1_tank"]] else 30
        
        # Stage 1
        s1_rect = pygame.Rect(cx - w // 2, cy - s1_h, w, s1_h)
        draw_rounded_rect(self.screen, (200, 200, 210), s1_rect, radius=2, border_color=(100, 100, 110), border_w=2)
        
        # Stage 2
        s2_rect = pygame.Rect(cx - w // 2, cy - s1_h - s2_h, w, s2_h)
        draw_rounded_rect(self.screen, (180, 180, 190), s2_rect, radius=2, border_color=(100, 100, 110), border_w=2)
        
        # Fairing (Nose cone)
        f_h = 50
        pts = [(cx - w // 2, cy - s1_h - s2_h), (cx + w // 2, cy - s1_h - s2_h), (cx, cy - s1_h - s2_h - f_h)]
        pygame.draw.polygon(self.screen, (220, 220, 230), pts)
        pygame.draw.polygon(self.screen, (100, 100, 110), pts, 2)
        
        # Engines
        ec1 = int(self.fields[3]["val"]) if self.fields[3]["val"].isdigit() else 1
        for i in range(min(ec1, 9)):
            ex = cx - (min(ec1, 3) * 8) // 2 + (i % 3) * 8
            ey = cy + (i // 3) * 4
            pygame.draw.rect(self.screen, (60, 60, 70), (ex, ey, 6, 8))

        # Labels
        self.screen.blit(self.f_tiny.render("FAIRING", True, TEXT_DIM), (cx + w // 2 + 10, cy - s1_h - s2_h - f_h // 2))
        self.screen.blit(self.f_tiny.render("STAGE 2", True, TEXT_DIM), (cx + w // 2 + 10, cy - s1_h - s2_h // 2))
        self.screen.blit(self.f_tiny.render("STAGE 1", True, TEXT_DIM), (cx + w // 2 + 10, cy - s1_h // 2))

    def draw(self):
        self.screen.fill(BG)
        # Header
        title = "◈   R O C K E T   A S S E M B L Y   H A N G A R   ◈"
        t_surf = self.f_title.render(title, True, ACCENT_CYAN)
        self.screen.blit(t_surf, (self.W // 2 - t_surf.get_width() // 2, 30))

        # Left Panel: Physics Dashboard
        lx = 50
        ly = 110
        draw_rounded_rect(self.screen, PANEL_DARK, (lx - 10, ly - 10, 320, self.H - 220), radius=10, border_color=BORDER, border_w=1)
        self.screen.blit(self.f_head.render("PHYSICS DASHBOARD", True, ACCENT_GOLD), (lx, ly)); ly += 35
        
        s1 = self.custom_data["stages"][0]
        s2 = self.custom_data["stages"][1]
        
        physics_stats = [
            ("Total Mass", f"{self.total_mass:,.0f} kg", TEXT_HI),
            ("Liftoff TWR", f"{self.s1_twr:.2f}", ACCENT_GRN if self.s1_twr > 1.2 else ACCENT_RED),
            ("Total Delta-V", f"{self.total_dv:,.0f} m/s", ACCENT_CYAN),
            ("", "", TEXT_DIM),
            ("S1 Propellant", f"{s1['propellant_mass']:,.0f} kg", TEXT_HI),
            ("S1 Thrust (SL)", f"{s1['thrust_sl']/1000:,.0f} kN", TEXT_HI),
            ("S1 Burn Time", f"{s1['burn_time']:.1f} s", TEXT_HI),
            ("", "", TEXT_DIM),
            ("S2 Propellant", f"{s2['propellant_mass']:,.0f} kg", TEXT_HI),
            ("S2 Thrust (Vac)", f"{s2['thrust_vac']/1000:,.0f} kN", TEXT_HI),
            ("S2 Burn Time", f"{s2['burn_time']:.1f} s", TEXT_HI),
            ("", "", TEXT_DIM),
            ("Total Power", f"{self.total_power_draw:.1f} kW", (200, 200, 255)),
            ("Batt Capacity", f"{self.total_batt:.1f} kWh", (200, 200, 255)),
        ]
        
        for label, val, col in physics_stats:
            if label:
                self.screen.blit(self.f_small.render(label, True, TEXT_DIM), (lx, ly))
                self.screen.blit(self.f_body.render(val, True, col), (lx + 140, ly))
            ly += 22

        # Center: Visualization
        preview_rect = pygame.Rect(self.W // 2 - 150, 100, 300, self.H - 200)
        self._draw_rocket_preview(preview_rect)

        # Right Panel: Components
        rx = self.W - 450
        ry = 110
        draw_rounded_rect(self.screen, PANEL_DARK, (rx - 10, ry - 10, 410, self.H - 220), radius=10, border_color=BORDER, border_w=1)
        self.screen.blit(self.f_head.render("VEHICLE COMPONENTS", True, ACCENT_CYAN), (rx, ry)); ry += 35
        
        self.rects = []
        field_gap = 42
        for i, field in enumerate(self.fields):
            y = ry + i * field_gap
            label_surf = self.f_small.render(field["label"], True, TEXT_DIM)
            self.screen.blit(label_surf, (rx, y))

            # Input/Select box
            rect = pygame.Rect(rx + 130, y - 5, 250, 32)
            self.rects.append(rect)
            
            is_active = (i == self.active_field)
            bg_col = (20, 35, 60) if is_active else (14, 20, 32)
            bord_col = BORDER_SEL if is_active else BORDER
            
            draw_rounded_rect(self.screen, bg_col, rect, radius=4, border_color=bord_col, border_w=2 if is_active else 1)
            
            if field["type"] == "part":
                sel_idx = self.sel_parts[field["key"]]
                part_name = field["db"][field["options"][sel_idx]]["name"]
                # Trim long names
                if len(part_name) > 22: part_name = part_name[:20] + ".."
                val_surf = self.f_body.render(f"< {part_name} >", True, (255, 255, 255) if is_active else TEXT_DIM)
            else:
                val_surf = self.f_body.render(field["val"], True, (255, 255, 255) if is_active else TEXT_DIM)
            
            self.screen.blit(val_surf, (rect.x + 8, rect.y + 6))

            if is_active and field["type"] != "part" and (pygame.time.get_ticks() // 500) % 2 == 0:
                cx = rect.x + 8 + val_surf.get_width()
                pygame.draw.line(self.screen, ACCENT_CYAN, (cx, rect.y + 6), (cx, rect.y + 26), 2)

        # Bottom buttons hint
        bx = self.W // 2
        by = self.H - 60
        self.screen.blit(self.f_head.render("[ ENTER ] FINALIZE ASSEMBLY", True, ACCENT_GRN), (bx - 260, by))
        self.screen.blit(self.f_head.render("[ ESC ] DISCARD CHANGES", True, ACCENT_RED), (bx + 60, by))

        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            field = self.fields[self.active_field]
            
            if event.key == pygame.K_ESCAPE:
                return "CANCEL"
            elif event.key == pygame.K_RETURN:
                self._update_stats()
                VEHICLES["CUSTOM"] = self.custom_data
                return "SAVE"
            elif event.key == pygame.K_UP:
                self.active_field = (self.active_field - 1) % len(self.fields)
            elif event.key == pygame.K_DOWN:
                self.active_field = (self.active_field + 1) % len(self.fields)
            
            # Left/Right for part selection
            elif event.key == pygame.K_LEFT:
                if field["type"] == "part":
                    opt_count = len(field["options"])
                    self.sel_parts[field["key"]] = (self.sel_parts[field["key"]] - 1) % opt_count
                    self._update_stats()
            elif event.key == pygame.K_RIGHT:
                if field["type"] == "part":
                    opt_count = len(field["options"])
                    self.sel_parts[field["key"]] = (self.sel_parts[field["key"]] + 1) % opt_count
                    self._update_stats()
            
            # Typing for text/num fields
            elif event.key == pygame.K_BACKSPACE:
                if field["type"] != "part":
                    field["val"] = field["val"][:-1]
                    self._update_stats()
            else:
                if field["type"] == "text":
                    if event.unicode.isprintable():
                        field["val"] += event.unicode
                        self._update_stats()
                elif field["type"] == "num":
                    if event.unicode in "0123456789.":
                        field["val"] += event.unicode
                        self._update_stats()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(event.pos):
                    self.active_field = i

        return None

class VehicleSelectScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W, self.H = screen.get_size()

        # Fonts
        self.f_title  = pygame.font.SysFont("Menlo", 28, bold=True)
        self.f_head   = pygame.font.SysFont("Menlo", 16, bold=True)
        self.f_body   = pygame.font.SysFont("Menlo", 13)
        self.f_small  = pygame.font.SysFont("Menlo", 11)
        self.f_tiny   = pygame.font.SysFont("Menlo", 10)
        self.f_art    = pygame.font.SysFont("Courier New", 11)
        self.f_btn    = pygame.font.SysFont("Menlo", 18, bold=True)
        self.f_badge  = pygame.font.SysFont("Menlo", 10, bold=True)

        self.vehicle_ids = list(VEHICLES.keys())
        self.orbit_ids   = list(ORBITS.keys())

        self.sel_vehicle = 0    # index into vehicle_ids
        self.sel_orbit   = 0    # index into orbit_ids

        self.hover_launch = False
        self.anim_t = 0.0       # for pulsing glow

        # Layout constants
        self.CARD_COLS  = 3
        self.CARD_W     = 280
        self.CARD_H     = 195
        self.CARD_GAP   = 14
        self.GRID_X     = 30
        self.GRID_Y     = 90
        self.ORBIT_X    = self.GRID_X + self.CARD_COLS * (self.CARD_W + self.CARD_GAP) + 20
        self.ORBIT_W    = self.W - self.ORBIT_X - 20
        self.BTN_W      = 240
        self.BTN_H      = 54
        self.BTN_X      = self.W // 2 - self.BTN_W // 2
        self.BTN_Y      = self.H - 80

    # ── Card rect ────────────────────────────────────────
    def _card_rect(self, idx):
        col = idx % self.CARD_COLS
        row = idx // self.CARD_COLS
        x = self.GRID_X + col * (self.CARD_W + self.CARD_GAP)
        y = self.GRID_Y + row * (self.CARD_H + self.CARD_GAP)
        return pygame.Rect(x, y, self.CARD_W, self.CARD_H)

    def _orbit_rect(self, idx):
        x = self.ORBIT_X
        y = self.GRID_Y + idx * 110
        return pygame.Rect(x, y, self.ORBIT_W, 100)

    def _btn_rect(self):
        return pygame.Rect(self.BTN_X, self.BTN_Y, self.BTN_W, self.BTN_H)

    # ── Draw helpers ─────────────────────────────────────
    def _draw_orbit_badge(self, surf, orbit_id, x, y):
        col = ORBIT_COLORS.get(orbit_id, (150, 150, 150))
        w = self.f_badge.size(orbit_id)[0] + 10
        pygame.draw.rect(surf, (*col, 60), (x, y, w, 16), border_radius=3)
        pygame.draw.rect(surf, col, (x, y, w, 16), 1, border_radius=3)
        surf.blit(self.f_badge.render(orbit_id, True, col), (x + 5, y + 3))
        return w + 4

    def _draw_vehicle_card(self, idx, veh_id):
        veh  = VEHICLES[veh_id]
        rect = self._card_rect(idx)
        selected = (idx == self.sel_vehicle)

        bg    = (20, 28, 45) if selected else PANEL_BG
        bord  = BORDER_SEL   if selected else BORDER
        bw    = 2             if selected else 1

        # Card background
        draw_rounded_rect(self.screen, bg, rect, radius=10, border_color=bord, border_w=bw)

        # Glow effect for selected
        if selected:
            glow = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
            glow_alpha = int(40 + 25 * math.sin(self.anim_t * 3))
            pygame.draw.rect(glow, (*BORDER_SEL, glow_alpha),
                             (0, 0, rect.w + 20, rect.h + 20), border_radius=14)
            self.screen.blit(glow, (rect.x - 10, rect.y - 10))

        x, y = rect.x + 12, rect.y + 10

        # Icon badge
        icon = veh.get("icon_char", "??")
        icon_rect = pygame.Rect(x, y, 36, 36)
        icon_col = BORDER_SEL if selected else (50, 70, 100)
        draw_rounded_rect(self.screen, (20, 30, 50), icon_rect, radius=6,
                          border_color=icon_col, border_w=1)
        ic_surf = self.f_head.render(icon, True, BORDER_SEL if selected else TEXT_DIM)
        self.screen.blit(ic_surf, (x + 18 - ic_surf.get_width() // 2,
                                   y + 18 - ic_surf.get_height() // 2))

        # Name
        name_col = ACCENT_CYAN if selected else TEXT_HI
        self.screen.blit(self.f_head.render(veh["name"], True, name_col), (x + 44, y + 2))
        # Manufacturer / country
        mfr = f"{veh.get('manufacturer','?')} · {veh.get('country','?')}"
        self.screen.blit(self.f_small.render(mfr, True, TEXT_DIM), (x + 44, y + 20))

        y += 46
        # Description (wrapped at ~38 chars)
        desc = veh.get("description", "")
        words = desc.split()
        line, lines = "", []
        for w in words:
            if len(line) + len(w) + 1 <= 38:
                line += (" " if line else "") + w
            else:
                lines.append(line); line = w
        if line: lines.append(line)
        for ln in lines[:2]:
            self.screen.blit(self.f_tiny.render(ln, True, TEXT_DIM), (x, y))
            y += 13

        y += 4
        # Payload stats
        pleo = veh.get("payload_leo_kg", 0)
        pgeo = veh.get("payload_geo_kg", 0)
        self.screen.blit(self.f_small.render(f"LEO: {pleo:,} kg", True, ACCENT_GRN), (x, y))
        if pgeo:
            self.screen.blit(self.f_small.render(f"GEO: {pgeo:,} kg", True, ACCENT_GOLD),
                             (x + 110, y))
        y += 16

        # Orbit type badges
        bx = x
        for oid in veh.get("orbit_types", []):
            bx += self._draw_orbit_badge(self.screen, oid, bx, y)
        y += 22

        # Stage count line
        ns = len(veh.get("stages", []))
        self.screen.blit(self.f_tiny.render(f"{ns}-stage vehicle", True, TEXT_TINY), (x, y))

        if veh_id == "CUSTOM":
            y += 14
            edit_txt = "Press E or Click to Edit Parameters"
            self.screen.blit(self.f_tiny.render(edit_txt, True, ACCENT_GOLD), (x, y))

    def _draw_orbit_panel(self, idx, orbit_id):
        orb  = ORBITS[orbit_id]
        rect = self._orbit_rect(idx)
        selected = (idx == self.sel_orbit)

        # Check compatibility with selected vehicle
        veh_id = self.vehicle_ids[self.sel_vehicle]
        veh    = VEHICLES[veh_id]
        compatible = orbit_id in veh.get("orbit_types", [])

        bg    = (18, 28, 42) if selected else PANEL_DARK
        bord  = orb.get("color", BORDER_SEL) if selected else BORDER
        bw    = 2 if selected else 1
        alpha = 255 if compatible else 140

        draw_rounded_rect(self.screen, bg, rect, radius=8, border_color=bord, border_w=bw)

        x, y = rect.x + 12, rect.y + 10
        col = orb.get("color", TEXT_HI)

        # Orbit name
        name_surf = self.f_head.render(orb["name"], True, col if compatible else TEXT_TINY)
        self.screen.blit(name_surf, (x, y)); y += 20

        # Altitude and velocity
        alt_km = orb["target_altitude_m"] / 1000.0
        vel = orb["target_velocity_m_s"]
        inc = orb.get("inclination_deg", 0)
        self.screen.blit(self.f_small.render(
            f"Alt: {alt_km:,.0f} km  |  V: {vel:,.0f} m/s  |  i: {inc}°",
            True, TEXT_DIM if compatible else TEXT_TINY), (x, y)); y += 16

        # Description
        self.screen.blit(self.f_tiny.render(orb.get("description",""), True,
                         TEXT_DIM if compatible else TEXT_TINY), (x, y))

        # Incompatible badge
        if not compatible:
            warn = self.f_small.render("✗ Incompatible with selected vehicle", True, ACCENT_RED)
            self.screen.blit(warn, (rect.right - warn.get_width() - 10, rect.y + 10))
        elif selected:
            ok = self.f_small.render("✓ SELECTED", True, ACCENT_GRN)
            self.screen.blit(ok, (rect.right - ok.get_width() - 10, rect.y + 10))

    def _draw_background(self):
        self.screen.fill(BG)
        # Grid lines
        for i in range(0, self.W, 60):
            pygame.draw.line(self.screen, (14, 20, 30), (i, 0), (i, self.H))
        for j in range(0, self.H, 60):
            pygame.draw.line(self.screen, (14, 20, 30), (0, j), (self.W, j))

        # Decorative corner brackets
        c = BORDER
        for sx, sy, fx, fy in [(0, 0, 40, 0), (0, 0, 0, 40),
                                (self.W - 40, 0, self.W, 0), (self.W, 0, self.W, 40),
                                (0, self.H - 40, 0, self.H), (0, self.H, 40, self.H),
                                (self.W - 40, self.H, self.W, self.H), (self.W, self.H - 40, self.W, self.H)]:
            pygame.draw.line(self.screen, c, (sx, sy), (fx, fy), 2)

    def _draw_header(self):
        # Title
        title = "◈  SATELLITE MISSION  —  VEHICLE SELECTION"
        t = self.f_title.render(title, True, ACCENT_CYAN)
        self.screen.blit(t, (self.W // 2 - t.get_width() // 2, 18))

        sub = "Select launch vehicle and target orbit  ·  SPACE / ENTER to launch  ·  ESC to quit"
        s = self.f_small.render(sub, True, TEXT_TINY)
        self.screen.blit(s, (self.W // 2 - s.get_width() // 2, 54))

        # Separator line
        pygame.draw.line(self.screen, BORDER, (30, 78), (self.W - 30, 78), 1)

        # Section labels
        self.screen.blit(self.f_head.render("LAUNCH VEHICLES", True, TEXT_DIM), (self.GRID_X, 82))
        self.screen.blit(self.f_head.render("TARGET ORBIT", True, TEXT_DIM), (self.ORBIT_X, 82))

    def _draw_launch_button(self):
        rect = self._btn_rect()
        pulse = 0.5 + 0.5 * math.sin(self.anim_t * 4)
        col = lerp_color((20, 160, 80), (40, 255, 110), pulse)
        bord = lerp_color((30, 200, 90), (100, 255, 150), pulse)

        if self.hover_launch:
            col = (40, 255, 110)
            bord = (150, 255, 180)

        draw_rounded_rect(self.screen, (10, col[1] // 4, 20), rect,
                          radius=12, border_color=bord, border_w=2)

        # Glow
        gsurf = pygame.Surface((rect.w + 30, rect.h + 30), pygame.SRCALPHA)
        ga = int(50 + 40 * pulse)
        pygame.draw.rect(gsurf, (*bord, ga), (0, 0, rect.w + 30, rect.h + 30), border_radius=16)
        self.screen.blit(gsurf, (rect.x - 15, rect.y - 15))

        label = "  ▶  LAUNCH MISSION  "
        lbl = self.f_btn.render(label, True, col)
        self.screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - lbl.get_height() // 2))

        # Vehicle + orbit info below button
        vname = VEHICLES[self.vehicle_ids[self.sel_vehicle]]["name"]
        oname = ORBITS[self.orbit_ids[self.sel_orbit]]["name"]
        info = self.f_small.render(f"{vname}  →  {oname}", True, TEXT_DIM)
        self.screen.blit(info, (self.W // 2 - info.get_width() // 2, rect.bottom + 8))

    def draw(self):
        self._draw_background()
        self._draw_header()

        # Vehicle cards
        for i, vid in enumerate(self.vehicle_ids):
            self._draw_vehicle_card(i, vid)

        # Orbit panels
        for i, oid in enumerate(self.orbit_ids):
            self._draw_orbit_panel(i, oid)

        self._draw_launch_button()
        pygame.display.flip()

    def handle_event(self, event):
        """Returns (vid, oid) if launch confirmed, else 'BUILD' if custom edit requested, else None."""
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._do_launch()
            elif event.key == pygame.K_e: # Shortcut for edit
                if self.vehicle_ids[self.sel_vehicle] == "CUSTOM":
                    return "BUILD"
            elif event.key == pygame.K_RIGHT:
                self.sel_vehicle = (self.sel_vehicle + 1) % len(self.vehicle_ids)
            elif event.key == pygame.K_LEFT:
                self.sel_vehicle = (self.sel_vehicle - 1) % len(self.vehicle_ids)
            elif event.key == pygame.K_DOWN:
                self.sel_vehicle = min(self.sel_vehicle + self.CARD_COLS, len(self.vehicle_ids) - 1)
            elif event.key == pygame.K_UP:
                self.sel_vehicle = max(self.sel_vehicle - self.CARD_COLS, 0)
            elif event.key == pygame.K_TAB:
                self.sel_orbit = (self.sel_orbit + 1) % len(self.orbit_ids)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Vehicle cards
            for i, vid in enumerate(self.vehicle_ids):
                if self._card_rect(i).collidepoint(mx, my):
                    self.sel_vehicle = i
                    # If clicking already selected custom rocket, open builder
                    if vid == "CUSTOM":
                        return "BUILD"
            # Orbit panels
            for i, oid in enumerate(self.orbit_ids):
                if self._orbit_rect(i).collidepoint(mx, my):
                    self.sel_orbit = i
            # Launch button
            if self._btn_rect().collidepoint(mx, my):
                return self._do_launch()

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hover_launch = self._btn_rect().collidepoint(mx, my)

        return None

    def _do_launch(self):
        vid = self.vehicle_ids[self.sel_vehicle]
        oid = self.orbit_ids[self.sel_orbit]
        veh = VEHICLES[vid]
        # Force-select a compatible orbit if current is incompatible
        if oid not in veh.get("orbit_types", []):
            for candidate in veh.get("orbit_types", []):
                if candidate in self.orbit_ids:
                    oid = candidate
                    break
        return (vid, oid)

    def tick(self, dt):
        self.anim_t += dt


def run_selection(screen, clock, fps=60) -> tuple:
    """
    Blocking loop that shows the vehicle selection screen.
    Returns (vehicle_id: str, orbit_id: str).
    """
    sel = VehicleSelectScreen(screen)
    builder = None
    
    while True:
        dt = clock.tick(fps) / 1000.0
        
        if builder:
            builder.draw()
            for event in pygame.event.get():
                res = builder.handle_event(event)
                if res == "SAVE" or res == "CANCEL":
                    builder = None
        else:
            sel.tick(dt)
            for event in pygame.event.get():
                result = sel.handle_event(event)
                if result == "BUILD":
                    builder = CustomRocketBuilder(screen, sel.f_body, sel.f_head, sel.f_small, sel.f_tiny)
                elif result is not None:
                    return result
            sel.draw()
