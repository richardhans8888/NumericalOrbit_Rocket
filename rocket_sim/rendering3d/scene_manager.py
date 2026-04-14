# rendering3d/scene_manager.py
from panda3d.core import DirectionalLight, AmbientLight, TextNode
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton
from mission.flight_phases import PHASE_NAMES
from mission.telemetry import format_time
from rendering3d.telemetry_graph import TelemetryDashboard

class SceneManager:
    def __init__(self, engine):
        self.engine = engine
        
        dlight = DirectionalLight('sun')
        dlight.setColor((1.0, 1.0, 1.0, 1))
        dlnp = engine.render.attachNewNode(dlight)
        dlnp.setHpr(45, -45, 0)
        engine.render.setLight(dlnp)
        
        alight = AmbientLight('ambient')
        alight.setColor((0.5, 0.5, 0.5, 1))
        alnp = engine.render.attachNewNode(alight)
        engine.render.setLight(alnp)
        
        self.ui_time = OnscreenText(text="", pos=(-1.25, 0.9), scale=0.07, fg=(1,1,1,1), align=TextNode.ALeft)
        self.ui_event_box = OnscreenText(text="SYSTEM READY", pos=(0, 0.85), scale=0.08, fg=(1, 1, 0, 1), bg=(0.1,0.1,0.1,0.8), align=TextNode.ACenter)
        
        self.ui_instruction = OnscreenText(text="[SPACE] Launch | [C] Cam | [Arrows] Warp", pos=(0, 0.95), scale=0.05, fg=(1,1,1,1))
        self.btn_restart = DirectButton(text=("RESTART"), scale=0.06, pos=(1.2, 0, 0.9), command=engine.restart_mission, relief=1)
        
        self.dashboard = TelemetryDashboard(engine)
        
    def update_atmosphere(self, altitude):
        self.engine.setBackgroundColor(0.2, 0.2, 0.2) 
        
    def update_ui(self, elapsed, alt, vel, phase, time_warp, rocket, dt):
        self.ui_time.setText(f"T: {format_time(elapsed)} | WARP: {time_warp}x")
        
        event_str = PHASE_NAMES.get(phase, 'UNKNOWN')
        if phase == 0: event_str = "T-MINUS (PRELAUNCH)"
        elif phase == 2: event_str = "MAX-Q (MAX DYNAMIC PRESSURE)"
        elif phase == 3: event_str = "GRAVITY TURN"
        elif phase == 4: event_str = "SRB SEPARATION"
        elif phase == 5: event_str = "CORE BURN / FAIRING SEP"
        elif phase == 6: event_str = "CORE SEPARATION / SES"
        elif phase == 7: event_str = "SECO (ORBITAL INSERTION)"
        
        self.ui_event_box.setText(f" PHASE: {event_str} ")
        
        self.dashboard.update(dt, rocket)
        
    def destroy(self):
        self.ui_time.destroy()
        self.ui_event_box.destroy()
        self.ui_instruction.destroy()
        self.btn_restart.destroy()
        self.dashboard.destroy()
