# rendering3d/scene_manager.py
from panda3d.core import DirectionalLight, AmbientLight
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton
from mission.flight_phases import PHASE_NAMES
from mission.telemetry import format_time

class SceneManager:
    def __init__(self, engine):
        self.engine = engine
        
        dlight = DirectionalLight('sun')
        dlight.setColor((1.0, 1.0, 0.9, 1))
        dlnp = engine.render.attachNewNode(dlight)
        dlnp.setHpr(45, -45, 0)
        engine.render.setLight(dlnp)
        
        alight = AmbientLight('ambient')
        alight.setColor((0.4, 0.4, 0.5, 1))
        alnp = engine.render.attachNewNode(alight)
        engine.render.setLight(alnp)
        
        self.ui_time = OnscreenText(text="", pos=(-1.25, 0.9), scale=0.07, fg=(0,1,0,1), align=0)
        self.ui_phase = OnscreenText(text="", pos=(-1.25, 0.8), scale=0.07, fg=(0,1,0,1), align=0)
        self.ui_alt = OnscreenText(text="", pos=(-1.25, 0.7), scale=0.07, fg=(0,1,0,1), align=0)
        self.ui_vel = OnscreenText(text="", pos=(-1.25, 0.6), scale=0.07, fg=(0,1,0,1), align=0)
        self.ui_warp = OnscreenText(text="Time Warp: 1.0x", pos=(0.8, 0.9), scale=0.07, fg=(1,1,0,1), align=0)
        self.ui_instruction = OnscreenText(text="[SPACE] Launch | [C] Orbit Cam | [Arrows] Warp | [ESC] Exit", pos=(0, -0.9), scale=0.05, fg=(1,1,1,1))
        
        self.btn_restart = DirectButton(text=("RESTART"), scale=0.08, pos=(1.0, 0, -0.8), 
                                        command=engine.restart_mission, 
                                        relief=1, frameColor=(0.8, 0.2, 0.2, 1), text_fg=(1,1,1,1))
        
    def update_atmosphere(self, altitude):
        ratio = max(0.0, 1.0 - (altitude / 100000.0)) 
        r_base = 0.15 * ratio
        g_base = 0.45 * ratio
        b_base = 0.75 * ratio
        self.engine.setBackgroundColor(r_base, g_base, b_base) 
        
    def update_ui(self, elapsed, alt, vel, phase, time_warp):
        self.ui_time.setText(f"T: {format_time(elapsed)}")
        self.ui_phase.setText(f"PHASE: {PHASE_NAMES.get(phase, '')}")
        self.ui_alt.setText(f"ALT: {alt/1000.0:.1f} km")
        self.ui_vel.setText(f"VEL: {vel/1000.0:.2f} km/s")
        self.ui_warp.setText(f"WARP: {time_warp}x")
        
    def destroy(self):
        self.ui_time.destroy()
        self.ui_phase.destroy()
        self.ui_alt.destroy()
        self.ui_vel.destroy()
        self.ui_warp.destroy()
        self.ui_instruction.destroy()
        self.btn_restart.destroy()
