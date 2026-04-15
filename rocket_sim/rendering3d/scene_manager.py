# rendering3d/scene_manager.py
from panda3d.core import DirectionalLight, AmbientLight, TextNode, Fog
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton
from mission.flight_phases import PHASE_NAMES
from mission.telemetry import format_time
from rendering3d.telemetry_graph import TelemetryDashboard

class SceneManager:
    def __init__(self, engine):
        self.engine = engine

        # --- Sunlight (strong directional from upper-left) ---
        dlight = DirectionalLight('sun')
        dlight.setColor((1.2, 1.15, 1.0, 1))
        dlnp = engine.render.attachNewNode(dlight)
        dlnp.setHpr(30, -50, 0)
        engine.render.setLight(dlnp)

        # secondary fill light
        dlight2 = DirectionalLight('fill')
        dlight2.setColor((0.3, 0.35, 0.4, 1))
        dlnp2 = engine.render.attachNewNode(dlight2)
        dlnp2.setHpr(-120, -20, 0)
        engine.render.setLight(dlnp2)

        # --- Ambient light ---
        alight = AmbientLight('ambient')
        alight.setColor((0.35, 0.38, 0.45, 1))
        alnp = engine.render.attachNewNode(alight)
        engine.render.setLight(alnp)

        # --- Atmospheric fog for ground-level depth ---
        self.fog = Fog("atmo_fog")
        self.fog.setLinearRange(5000, 80000)
        self.fog.setColor(0.6, 0.7, 0.85)
        engine.render.setFog(self.fog)

        # --- Sky color starts as deep blue ---
        engine.setBackgroundColor(0.4, 0.55, 0.78)

        # --- HUD / UI elements ---
        self.ui_time = OnscreenText(
            text="", pos=(-1.25, 0.92), scale=0.06,
            fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.8), align=TextNode.ALeft
        )
        self.ui_event_box = OnscreenText(
            text="SYSTEM READY", pos=(0, 0.82), scale=0.07,
            fg=(1, 1, 0, 1), bg=(0.05, 0.05, 0.05, 0.85), align=TextNode.ACenter
        )
        self.ui_instruction = OnscreenText(
            text="[Spacebar] LAUNCH  |  C CAMERA  |  \u2190 / \u2192 WARP",
            pos=(0, 0.93), scale=0.045,
            fg=(0.9, 0.9, 0.9, 1), shadow=(0, 0, 0, 0.6)
        )
        self.btn_restart = DirectButton(
            text="RESTART", scale=0.06,
            pos=(1.2, 0, 0.92), command=engine.restart_mission, relief=1
        )

        self.dashboard = TelemetryDashboard(engine)

    def update_atmosphere(self, altitude):
        """Smoothly transition sky from NASA-blue to pitch-black space."""
        t = min(1.0, altitude / 120000.0)  # fully space by 120 km

        # blue sky -> black void
        r = 0.4 * (1.0 - t)
        g = 0.55 * (1.0 - t)
        b = 0.78 * (1.0 - t)
        self.engine.setBackgroundColor(r, g, b)

        # fade fog out as we leave atmosphere
        fog_end = 80000 + altitude * 2
        self.fog.setLinearRange(5000, fog_end)
        if altitude > 50000:
            self.engine.render.clearFog()

    def update_ui(self, elapsed, alt, vel, phase, time_warp, rocket, dt):
        self.ui_time.setText(f"T: {format_time(elapsed)} | WARP: {time_warp:.0f}x")

        event_str = PHASE_NAMES.get(phase, 'UNKNOWN')
        if phase == 0: event_str = "T-MINUS (PRELAUNCH)"
        elif phase == 1: event_str = "LIFTOFF"
        elif phase == 2: event_str = "MAX-Q (MAX DYNAMIC PRESSURE)"
        elif phase == 3: event_str = "GRAVITY TURN"
        elif phase == 4: event_str = "SRB SEPARATION"
        elif phase == 5: event_str = "CORE BURN / FAIRING SEP"
        elif phase == 6: event_str = "CORE SEPARATION / SES"
        elif phase == 7: event_str = "SECO (ORBITAL INSERTION)"

        self.ui_event_box.setText(f"  PHASE: {event_str}  ")

        self.dashboard.update(dt, rocket)

    def destroy(self):
        self.ui_time.destroy()
        self.ui_event_box.destroy()
        self.ui_instruction.destroy()
        self.btn_restart.destroy()
        self.dashboard.destroy()
