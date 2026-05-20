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


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def scale_color(c, f):
    return (
        int(clamp(c[0] * f, 0, 255)),
        int(clamp(c[1] * f, 0, 255)),
        int(clamp(c[2] * f, 0, 255)),
    )


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
            {"label": "S1 Fuel Load (%)", "key": "s1_fuel_load", "type": "num", "val": str(self.custom_data.get("s1_fuel_load", 100))},
            {"label": "S1 Engine", "key": "s1_engine", "type": "part", "options": self.engine_ids, "db": ENGINES},
            {"label": "S1 Engine HP (%)", "key": "s1_hp_tune", "type": "num", "val": str(self.custom_data.get("s1_hp_tune", 100))},
            {"label": "S1 Engine Count", "key": "s1_engine_count", "type": "num", "val": "1"},
            {"label": "S2 Fuel Tank", "key": "s2_tank", "type": "part", "options": self.tank_ids, "db": FUEL_TANKS},
            {"label": "S2 Fuel Load (%)", "key": "s2_fuel_load", "type": "num", "val": str(self.custom_data.get("s2_fuel_load", 100))},
            {"label": "S2 Engine", "key": "s2_engine", "type": "part", "options": self.engine_ids, "db": ENGINES},
            {"label": "S2 Engine HP (%)", "key": "s2_hp_tune", "type": "num", "val": str(self.custom_data.get("s2_hp_tune", 100))},
            {"label": "Fairing Type", "key": "fairing", "type": "part", "options": self.fairing_ids, "db": FAIRINGS},
            {"label": "Drag Coeff (Cd)", "key": "drag_coefficient", "type": "num", "val": str(self.custom_data["drag_coefficient"])},
            {"label": "Rocket Area (m2)", "key": "cross_sectional_area", "type": "num", "val": str(self.custom_data["cross_sectional_area"])},
        ]
        
        self.active_field = 0
        self.rects = []
        self.compat_issues = {}
        self._update_stats()

    def _field_float(self, idx, default=0.0):
        try:
            return float(self.fields[idx]["val"])
        except (TypeError, ValueError):
            return default

    def _field_int(self, idx, default=0):
        try:
            return int(float(self.fields[idx]["val"]))
        except (TypeError, ValueError):
            return default

    def _mark_issue(self, issues, idx, reason):
        issues.setdefault(idx, reason)

    def _build_compatibility_issues(self):
        """Return field-index issues that can stop the custom rocket from climbing."""
        issues = {}

        s1_fuel_pct = self._field_float(2, 100.0)
        s1_hp_pct = self._field_float(4, 100.0)
        s1_engine_count = self._field_int(5, 1)
        s2_fuel_pct = self._field_float(7, 100.0)
        s2_hp_pct = self._field_float(9, 100.0)
        cd = self._field_float(11, self.custom_data.get("drag_coefficient", 0.4))
        area = self._field_float(12, self.custom_data.get("cross_sectional_area", 10.0))

        e1 = ENGINES[self.engine_ids[self.sel_parts["s1_engine"]]]
        e2 = ENGINES[self.engine_ids[self.sel_parts["s2_engine"]]]

        if s1_fuel_pct <= 0:
            self._mark_issue(issues, 2, "Stage 1 has no propellant.")
        elif s1_fuel_pct > 150:
            self._mark_issue(issues, 2, "Stage 1 fuel load is unrealistically heavy.")

        if s2_fuel_pct <= 0:
            self._mark_issue(issues, 7, "Stage 2 has no propellant.")
        elif s2_fuel_pct > 150:
            self._mark_issue(issues, 7, "Stage 2 fuel load is too heavy for ascent.")

        if s1_hp_pct <= 0:
            self._mark_issue(issues, 4, "Stage 1 engines are disabled.")
        if s2_hp_pct <= 0:
            self._mark_issue(issues, 9, "Stage 2 engine is disabled.")

        if s1_engine_count < 1:
            self._mark_issue(issues, 5, "Stage 1 needs at least one engine.")
        elif s1_engine_count > 9:
            self._mark_issue(issues, 5, "Too many first-stage engines for this model.")

        if e1.get("thrust_sl", 0.0) <= 0:
            self._mark_issue(issues, 3, "Vacuum engine cannot lift off at sea level.")
        if e2.get("thrust_vac", 0.0) <= 0:
            self._mark_issue(issues, 8, "Upper stage needs vacuum thrust.")

        if cd <= 0:
            self._mark_issue(issues, 11, "Drag coefficient must be positive.")
        elif cd > 0.75:
            self._mark_issue(issues, 11, "High drag coefficient can prevent climb.")

        if area <= 0:
            self._mark_issue(issues, 12, "Cross-section area must be positive.")
        elif area > 25.0:
            self._mark_issue(issues, 12, "Large area creates excessive drag.")

        if self.s1_twr < 1.0:
            self._mark_issue(issues, 3, "Not enough sea-level thrust for liftoff.")
            self._mark_issue(issues, 4, "Increase Stage 1 engine power.")
            self._mark_issue(issues, 5, "Add Stage 1 engines or reduce mass.")
            self._mark_issue(issues, 1, "Stage 1 tank may be too heavy.")
            self._mark_issue(issues, 2, "Stage 1 propellant mass is too heavy.")
            self._mark_issue(issues, 6, "Upper stage tank is too heavy for Stage 1.")
            self._mark_issue(issues, 7, "Upper stage fuel is overloading liftoff.")
            self._mark_issue(issues, 10, "Fairing mass contributes to low TWR.")
        elif self.s1_twr < 1.2:
            self._mark_issue(issues, 3, "Liftoff TWR is marginal.")
            self._mark_issue(issues, 4, "More Stage 1 thrust recommended.")
            self._mark_issue(issues, 5, "More engines may be needed.")

        target_dv = 7600.0
        if self.total_dv < target_dv:
            self._mark_issue(issues, 2, "Low total delta-v.")
            self._mark_issue(issues, 7, "Low total delta-v.")
            self._mark_issue(issues, 8, "Upper stage may lack orbital energy.")

        return issues

    def _update_stats(self):
        """Calculate dry mass, propellant mass, thrust, and delta-v based on selected parts."""
        # S1
        t1 = FUEL_TANKS[self.tank_ids[self.sel_parts["s1_tank"]]]
        e1 = ENGINES[self.engine_ids[self.sel_parts["s1_engine"]]]
        
        # Tuning Values
        s1_fuel_pct = float(self.fields[2]["val"]) / 100.0 if self.fields[2]["val"].replace('.','',1).isdigit() else 1.0
        s1_hp_tune = float(self.fields[4]["val"]) / 100.0 if self.fields[4]["val"].replace('.','',1).isdigit() else 1.0
        ec1 = int(self.fields[5]["val"]) if self.fields[5]["val"].isdigit() else 1
        
        s1_dry = t1["dry_mass"] + (e1["mass"] * ec1)
        s1_fuel = t1["propellant_mass"] * s1_fuel_pct
        s1_t_sl = e1["thrust_sl"] * ec1 * s1_hp_tune
        s1_t_vac = e1["thrust_vac"] * ec1 * s1_hp_tune
        s1_isp = e1["isp_vac"]
        s1_power = e1.get("power_draw_kw", 0) * ec1 * s1_hp_tune
        s1_batt = t1.get("battery_capacity_kwh", 0)
        
        # S2
        t2 = FUEL_TANKS[self.tank_ids[self.sel_parts["s2_tank"]]]
        e2 = ENGINES[self.engine_ids[self.sel_parts["s2_engine"]]]
        
        s2_fuel_pct = float(self.fields[7]["val"]) / 100.0 if self.fields[7]["val"].replace('.','',1).isdigit() else 1.0
        s2_hp_tune = float(self.fields[9]["val"]) / 100.0 if self.fields[9]["val"].replace('.','',1).isdigit() else 1.0
        
        s2_dry = t2["dry_mass"] + e2["mass"]
        s2_fuel = t2["propellant_mass"] * s2_fuel_pct
        s2_t_vac = e2["thrust_vac"] * s2_hp_tune
        s2_isp = e2["isp_vac"]
        s2_power = e2.get("power_draw_kw", 0) * s2_hp_tune
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
        self.custom_data["stages"][0]["engine_count"] = ec1
        
        self.custom_data["stages"][1]["dry_mass"] = s2_dry
        self.custom_data["stages"][1]["propellant_mass"] = s2_fuel
        self.custom_data["stages"][1]["thrust_sl"] = 0
        self.custom_data["stages"][1]["thrust_vac"] = s2_t_vac
        self.custom_data["stages"][1]["burn_time"] = s2_fuel / (s2_t_vac / (s2_isp * g0)) if s2_isp > 0 and s2_t_vac > 0 else 300
        self.custom_data["stages"][1]["engine_count"] = 1 # Upper stage usually 1

        self.custom_data["fairing"]["mass"] = f["mass"]
        self.custom_data["fairing"]["jettison_altitude"] = f["jettison_altitude"]
        
        self.custom_data["drag_coefficient"] = float(self.fields[11]["val"]) if self.fields[11]["val"].replace('.','',1).isdigit() else 0.4
        self.custom_data["cross_sectional_area"] = float(self.fields[12]["val"]) if self.fields[12]["val"].replace('.','',1).isdigit() else 10.0
        self.custom_data["name"] = self.fields[0]["val"]
        
        # Save tuning values
        self.custom_data["s1_fuel_load"] = float(self.fields[2]["val"]) if self.fields[2]["val"].replace('.','',1).isdigit() else 100.0
        self.custom_data["s1_hp_tune"] = float(self.fields[4]["val"]) if self.fields[4]["val"].replace('.','',1).isdigit() else 100.0
        self.custom_data["s2_fuel_load"] = float(self.fields[7]["val"]) if self.fields[7]["val"].replace('.','',1).isdigit() else 100.0
        self.custom_data["s2_hp_tune"] = float(self.fields[9]["val"]) if self.fields[9]["val"].replace('.','',1).isdigit() else 100.0
        
        self.custom_data["analysis"] = {
            "twr": float(self.s1_twr),
            "delta_v_m_s": float(self.total_dv),
            "total_mass_kg": float(self.total_mass),
        }
        self.compat_issues = self._build_compatibility_issues()

    def _draw_rocket_preview(self, rect):
        """Draw a simple 2D visualization of the rocket based on selected parts."""
        cx, cy = rect.centerx, rect.bottom - 100
        
        # Part Data
        t1 = FUEL_TANKS[self.tank_ids[self.sel_parts["s1_tank"]]]
        e1 = ENGINES[self.engine_ids[self.sel_parts["s1_engine"]]]
        t2 = FUEL_TANKS[self.tank_ids[self.sel_parts["s2_tank"]]]
        e2 = ENGINES[self.engine_ids[self.sel_parts["s2_engine"]]]
        fairing = FAIRINGS[self.fairing_ids[self.sel_parts["fairing"]]]

        # Visual Material Colors
        def get_tank_color(name):
            name = name.upper()
            if "KEROLOX" in name: return (230, 230, 235) # White
            if "ALLOY" in name: return (160, 165, 175) # Metallic Grey
            if "COMPOSITE" in name: return (45, 45, 50) # Dark Carbon
            if "CRYOGENIC" in name: return (255, 150, 50) # Orange Foam
            return (200, 200, 210)

        c1 = get_tank_color(t1["name"])
        c2 = get_tank_color(t2["name"])

        # Scaling
        s1_h = 180 if "LARGE" in t1["name"].upper() else 140 if "MEDIUM" in t1["name"].upper() else 90
        s2_h = 110 if "LARGE" in t2["name"].upper() else 80 if "MEDIUM" in t2["name"].upper() else 50
        w = 46 if "LARGE" in t1["name"].upper() else 34
        
        # Stage 1
        s1_rect = pygame.Rect(cx - w // 2, cy - s1_h, w, s1_h)
        draw_rounded_rect(self.screen, c1, s1_rect, radius=2, border_color=scale_color(c1, 0.5), border_w=2)
        
        # Stage 2
        s2_rect = pygame.Rect(cx - w // 2, cy - s1_h - s2_h, w, s2_h)
        draw_rounded_rect(self.screen, c2, s2_rect, radius=2, border_color=scale_color(c2, 0.5), border_w=2)
        
        # Fairing (Nose cone)
        f_h = 60 if "HEAVY" in fairing["name"].upper() else 50
        f_w = w + 10 if "HEAVY" in fairing["name"].upper() else w
        pts = [(cx - f_w // 2, cy - s1_h - s2_h), (cx + f_w // 2, cy - s1_h - s2_h), (cx, cy - s1_h - s2_h - f_h)]
        pygame.draw.polygon(self.screen, (220, 220, 230), pts)
        pygame.draw.polygon(self.screen, (100, 100, 110), pts, 2)
        
        # Engine Visualization
        ec1 = int(self.fields[5]["val"]) if self.fields[5]["val"].isdigit() else 1
        
        # Engine size/shape based on type
        def draw_engine_bell(ex, ey, e_data, is_vacuum=False):
            e_name = e_data["name"].upper()
            bw = 8; bh = 10
            if "RD-180" in e_name: bw = 12; bh = 14
            elif "RUTHERFORD" in e_name: bw = 6; bh = 7
            elif "VULCAIN" in e_name: bw = 10; bh = 12
            
            if is_vacuum: bw *= 1.5; bh *= 1.2 # Vacuum engines have larger bells
            
            pygame.draw.polygon(self.screen, (50, 50, 55), [
                (ex, ey), (ex + bw, ey), 
                (ex + bw + 2, ey + bh), (ex - 2, ey + bh)
            ])
            pygame.draw.polygon(self.screen, (30, 30, 35), [
                (ex, ey), (ex + bw, ey), 
                (ex + bw + 2, ey + bh), (ex - 2, ey + bh)
            ], 1)

        # Draw S1 Engines
        cols = 3
        gap = 10
        for i in range(min(ec1, 9)):
            row = i // cols
            col = i % cols
            ex = cx - (min(ec1, cols) * gap) // 2 + col * gap - 4
            ey = cy + row * 6
            draw_engine_bell(ex, ey, e1)

        # Draw S2 Engine (Internal/Hidden partially)
        draw_engine_bell(cx - 6, cy - s1_h + 2, e2, is_vacuum=True)

        # Labels
        self.screen.blit(self.f_tiny.render(f"FAIRING: {fairing['name']}", True, TEXT_DIM), (cx + w // 2 + 15, cy - s1_h - s2_h - f_h // 2))
        self.screen.blit(self.f_tiny.render(f"S2: {t2['name']}", True, TEXT_DIM), (cx + w // 2 + 15, cy - s1_h - s2_h // 2))
        self.screen.blit(self.f_tiny.render(f"S1: {t1['name']}", True, TEXT_DIM), (cx + w // 2 + 15, cy - s1_h // 2))

    def _draw_wrapped_text(self, text, font, color, x, y, max_width, line_h):
        words = text.split()
        line = ""
        for word in words:
            trial = word if not line else f"{line} {word}"
            if font.size(trial)[0] <= max_width:
                line = trial
            else:
                if line:
                    self.screen.blit(font.render(line, True, color), (x, y))
                    y += line_h
                line = word
        if line:
            self.screen.blit(font.render(line, True, color), (x, y))
            y += line_h
        return y

    def _draw_ascent_physics_box(self, rect):
        has_issues = bool(self.compat_issues)
        border = ACCENT_RED if has_issues else ACCENT_GRN
        bg = (18, 10, 16) if has_issues else PANEL_DARK

        if has_issues:
            pulse = 0.55 + 0.45 * math.sin(pygame.time.get_ticks() * 0.006)
            glow = pygame.Surface((rect.w + 28, rect.h + 28), pygame.SRCALPHA)
            pygame.draw.rect(
                glow,
                (*ACCENT_RED, int(60 + 50 * pulse)),
                (0, 0, rect.w + 28, rect.h + 28),
                border_radius=14,
            )
            self.screen.blit(glow, (rect.x - 14, rect.y - 14))

        draw_rounded_rect(self.screen, bg, rect, radius=10, border_color=border, border_w=2 if has_issues else 1)

        x = rect.x + 16
        y = rect.y + 16
        max_w = rect.w - 32

        title = "ASCENT PHYSICS CHECK"
        self.screen.blit(self.f_head.render(title, True, border), (x, y)); y += 30

        status = "NOT COMPATIBLE" if has_issues else "READY TO CLIMB"
        self.screen.blit(self.f_body.render(status, True, border), (x, y)); y += 26

        twr_col = ACCENT_GRN if self.s1_twr >= 1.2 else ACCENT_RED
        stats = [
            ("T/W = Thrust / Weight", f"{self.s1_twr:.2f}"),
            ("Mass", f"{self.total_mass:,.0f} kg"),
            ("Delta-v", f"{self.total_dv:,.0f} m/s"),
        ]
        for label, value in stats:
            self.screen.blit(self.f_tiny.render(label, True, TEXT_DIM), (x, y))
            self.screen.blit(self.f_small.render(value, True, twr_col if label.startswith("T/W") else TEXT_HI), (x + 150, y - 1))
            y += 18

        y += 8
        self.screen.blit(self.f_small.render("WHY IT FAILS", True, ACCENT_RED if has_issues else TEXT_DIM), (x, y)); y += 20

        if has_issues:
            unique_reasons = list(dict.fromkeys(self.compat_issues.values()))
            for reason in unique_reasons[:8]:
                y = self._draw_wrapped_text(f"! {reason}", self.f_small, ACCENT_RED, x, y, max_w, 15)
                y += 4
        else:
            y = self._draw_wrapped_text(
                "The first stage has enough thrust to overcome weight, and the selected mass/drag values are within the current simulation limits.",
                self.f_small,
                ACCENT_GRN,
                x,
                y,
                max_w,
                15,
            )

        y += 10
        self.screen.blit(self.f_small.render("WHAT TO CHANGE", True, ACCENT_GOLD), (x, y)); y += 20
        if self.s1_twr < 1.0:
            tips = [
                "Increase S1 engine HP or engine count.",
                "Reduce S2 fuel load or use a lighter upper tank.",
                "Reduce fairing, area, or drag coefficient.",
            ]
        elif self.compat_issues:
            tips = [
                "Fix the red glowing fields first.",
                "Aim for liftoff T/W above 1.20.",
                "Keep fuel load near 100% unless testing extremes.",
            ]
        else:
            tips = [
                "Use the launch view to inspect Max-Q and acceleration.",
                "For orbit, keep building horizontal velocity after ascent.",
            ]

        for tip in tips:
            y = self._draw_wrapped_text(f"- {tip}", self.f_tiny, TEXT_HI, x, y, max_w, 13)
            y += 3

    def draw(self):
        self.screen.fill(BG)
        # Header
        title = "◈   R O C K E T   A S S E M B L Y   H A N G A R   ◈"
        t_surf = self.f_title.render(title, True, ACCENT_CYAN)
        self.screen.blit(t_surf, (self.W // 2 - t_surf.get_width() // 2, 30))

        # 1. Physics Dashboard (Left)
        lx = 40
        ly = 110
        draw_rounded_rect(self.screen, PANEL_DARK, (lx - 10, ly - 10, 310, self.H - 220), radius=10, border_color=BORDER, border_w=1)
        self.screen.blit(self.f_head.render("PHYSICS DASHBOARD", True, ACCENT_GOLD), (lx, ly)); ly += 35
        
        s1 = self.custom_data["stages"][0]
        s2 = self.custom_data["stages"][1]
        
        # Get base thrust for HP display
        e1_base = ENGINES[self.engine_ids[self.sel_parts["s1_engine"]]]
        e2_base = ENGINES[self.engine_ids[self.sel_parts["s2_engine"]]]
        s1_base_hp = e1_base["thrust_vac"] / 1000.0
        s2_base_hp = e2_base["thrust_vac"] / 1000.0

        physics_stats = [
            ("Total Mass", f"{self.total_mass:,.0f} kg", TEXT_HI),
            ("Liftoff TWR", f"{self.s1_twr:.2f}", ACCENT_GRN if self.s1_twr > 1.2 else ACCENT_RED),
            ("Total Delta-V", f"{self.total_dv:,.0f} m/s", ACCENT_CYAN),
            ("", "", TEXT_DIM),
            ("S1 Base HP", f"{s1_base_hp:,.0f} hp", ACCENT_CYAN),
            ("S1 Propellant", f"{s1['propellant_mass']:,.0f} kg", TEXT_HI),
            ("S1 Thrust (SL)", f"{s1['thrust_sl']/1000:,.0f} kN", TEXT_HI),
            ("S1 Burn Time", f"{s1['burn_time']:.1f} s", TEXT_HI),
            ("", "", TEXT_DIM),
            ("S2 Base HP", f"{s2_base_hp:,.0f} hp", ACCENT_CYAN),
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
                self.screen.blit(self.f_body.render(val, True, col), (lx + 130, ly))
            ly += 22

        # 2. Visualization (Center-Left)
        preview_rect = pygame.Rect(360, 100, 280, self.H - 200)
        self._draw_rocket_preview(preview_rect)

        # 3. Stage 1 Components (Center-Right)
        sx1 = 660
        sy1 = 110
        draw_rounded_rect(self.screen, PANEL_DARK, (sx1 - 10, sy1 - 10, 360, self.H - 220), radius=10, border_color=BORDER, border_w=1)
        self.screen.blit(self.f_head.render("STAGE 1 CONFIG", True, ACCENT_CYAN), (sx1, sy1)); sy1 += 35
        
        # 4. Stage 2 & Aero (Far Right)
        sx2 = 1040
        sy2 = 110
        draw_rounded_rect(self.screen, PANEL_DARK, (sx2 - 10, sy2 - 10, 360, self.H - 220), radius=10, border_color=BORDER, border_w=1)
        self.screen.blit(self.f_head.render("STAGE 2 & AERO", True, ACCENT_MAG), (sx2, sy2)); sy2 += 35

        physics_rect = pygame.Rect(1425, 100, max(260, self.W - 1455), self.H - 220)
        self._draw_ascent_physics_box(physics_rect)

        self.rects = []
        field_gap = 45
        
        # Indices for Box 1: 0, 1, 2, 3, 4, 5
        # Indices for Box 2: 6, 7, 8, 9, 10, 11, 12
        
        for i, field in enumerate(self.fields):
            is_box1 = (i <= 5)
            rx = sx1 if is_box1 else sx2
            ry_base = sy1 if is_box1 else sy2
            
            # Local index within the box
            idx_in_box = i if is_box1 else (i - 6)
            y = ry_base + idx_in_box * field_gap
            
            label_surf = self.f_small.render(field["label"], True, TEXT_DIM)
            self.screen.blit(label_surf, (rx, y))

            # Input/Select box
            rect = pygame.Rect(rx + 140, y - 5, 200, 32)
            self.rects.append(rect)
            
            is_active = (i == self.active_field)
            has_issue = i in self.compat_issues
            bg_col = (20, 35, 60) if is_active else (14, 20, 32)
            if has_issue:
                bg_col = (44, 13, 18) if not is_active else (60, 20, 28)
            bord_col = ACCENT_RED if has_issue else BORDER_SEL if is_active else BORDER

            if has_issue:
                pulse = 0.55 + 0.45 * math.sin(pygame.time.get_ticks() * 0.008)
                glow = pygame.Surface((rect.w + 26, rect.h + 26), pygame.SRCALPHA)
                pygame.draw.rect(
                    glow,
                    (*ACCENT_RED, int(75 + 65 * pulse)),
                    (0, 0, rect.w + 26, rect.h + 26),
                    border_radius=8,
                )
                self.screen.blit(glow, (rect.x - 13, rect.y - 13))

            draw_rounded_rect(self.screen, bg_col, rect, radius=4, border_color=bord_col, border_w=2 if (is_active or has_issue) else 1)
            
            if field["type"] == "part":
                sel_idx = self.sel_parts[field["key"]]
                part_name = field["db"][field["options"][sel_idx]]["name"]
                # Trim long names
                if len(part_name) > 18: part_name = part_name[:16] + ".."
                val_surf = self.f_body.render(f"< {part_name} >", True, (255, 255, 255) if is_active else TEXT_DIM)
            else:
                val_surf = self.f_body.render(field["val"], True, (255, 255, 255) if is_active else TEXT_DIM)
            
            self.screen.blit(val_surf, (rect.x + 8, rect.y + 6))

            if has_issue and is_active:
                warn = self.compat_issues[i]
                self.screen.blit(self.f_tiny.render(warn[:42], True, ACCENT_RED), (rect.x, rect.bottom + 3))

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
        self.confirm_open = False
        self.confirm_title = ""
        self.confirm_body = ""
        self.confirm_launch = None
        self.confirm_btn_go = None
        self.confirm_btn_back = None

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
        if self.confirm_open:
            self._draw_confirm_overlay()
        pygame.display.flip()

    def _custom_launch_warning(self, veh):
        stages = veh.get("stages", [])
        if not stages:
            return "No stages defined."

        g0 = 9.80665
        s1 = stages[0]
        thrust_sl = float(s1.get("thrust_sl", 0.0) or 0.0)
        if thrust_sl <= 0:
            return "Stage 1 sea-level thrust is 0 N."

        total_mass = 0.0
        for st in stages:
            total_mass += float(st.get("dry_mass", 0.0) or 0.0) + float(st.get("propellant_mass", 0.0) or 0.0)
        total_mass += float(veh.get("fairing", {}).get("mass", 0.0) or 0.0)
        if total_mass <= 0:
            return "Total mass is 0 kg."

        twr = thrust_sl / (total_mass * g0)
        dv = float(veh.get("analysis", {}).get("delta_v_m_s", 0.0) or 0.0)

        if twr < 1.0:
            return f"Liftoff TWR is too low ({twr:.2f} < 1.00). Rocket will not lift off."
        if twr < 1.15:
            return f"Liftoff TWR is low ({twr:.2f}). Rocket may fail to lift off safely."
        if dv > 0 and dv < 7500:
            return f"Total Δv is low ({dv:,.0f} m/s). Rocket may fail to reach orbit."
        return None

    def _open_confirm(self, title, body, launch_tuple):
        self.confirm_open = True
        self.confirm_title = title
        self.confirm_body = body
        self.confirm_launch = launch_tuple
        self.confirm_btn_go = None
        self.confirm_btn_back = None

    def _draw_confirm_overlay(self):
        shade = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 170))
        self.screen.blit(shade, (0, 0))

        w = 760
        h = 260
        x = self.W // 2 - w // 2
        y = self.H // 2 - h // 2
        panel = pygame.Rect(x, y, w, h)
        draw_rounded_rect(self.screen, (12, 16, 24), panel, radius=12, border_color=ACCENT_GOLD, border_w=2)

        t = self.f_head.render(self.confirm_title, True, ACCENT_GOLD)
        self.screen.blit(t, (x + 22, y + 18))

        body_lines = []
        words = (self.confirm_body or "").split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= 62:
                line += (" " if line else "") + word
            else:
                body_lines.append(line)
                line = word
        if line:
            body_lines.append(line)
        by = y + 58
        for ln in body_lines[:4]:
            self.screen.blit(self.f_small.render(ln, True, TEXT_HI), (x + 22, by))
            by += 18

        hint = self.f_tiny.render("ENTER: launch anyway   |   ESC: go back", True, TEXT_DIM)
        self.screen.blit(hint, (x + 22, y + h - 58))

        btn_w = 250
        btn_h = 44
        btn_go = pygame.Rect(x + 22, y + h - 44 - 18, btn_w, btn_h)
        btn_back = pygame.Rect(x + w - btn_w - 22, y + h - 44 - 18, btn_w, btn_h)
        self.confirm_btn_go = btn_go
        self.confirm_btn_back = btn_back

        draw_rounded_rect(self.screen, (14, 55, 28), btn_go, radius=10, border_color=ACCENT_GRN, border_w=2)
        draw_rounded_rect(self.screen, (45, 18, 18), btn_back, radius=10, border_color=ACCENT_RED, border_w=2)

        go_lbl = self.f_btn.render("LAUNCH ANYWAY", True, ACCENT_GRN)
        bk_lbl = self.f_btn.render("GO BACK", True, ACCENT_RED)
        self.screen.blit(go_lbl, (btn_go.centerx - go_lbl.get_width() // 2, btn_go.centery - go_lbl.get_height() // 2))
        self.screen.blit(bk_lbl, (btn_back.centerx - bk_lbl.get_width() // 2, btn_back.centery - bk_lbl.get_height() // 2))

    def handle_event(self, event):
        """Returns (vid, oid) if launch confirmed, else 'BUILD' if custom edit requested, else None."""
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if self.confirm_open:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.confirm_open = False
                    self.confirm_launch = None
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.confirm_launch is not None:
                        out = self.confirm_launch
                        self.confirm_open = False
                        self.confirm_launch = None
                        return out
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if self.confirm_btn_go and self.confirm_btn_go.collidepoint(mx, my) and self.confirm_launch is not None:
                    out = self.confirm_launch
                    self.confirm_open = False
                    self.confirm_launch = None
                    return out
                if self.confirm_btn_back and self.confirm_btn_back.collidepoint(mx, my):
                    self.confirm_open = False
                    self.confirm_launch = None
            return None

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
        launch_tuple = (vid, oid)
        if vid == "CUSTOM":
            warn = self._custom_launch_warning(veh)
            if warn:
                self._open_confirm("WARNING: CUSTOM ROCKET MAY FAIL", warn, launch_tuple)
                return None
        return launch_tuple

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
