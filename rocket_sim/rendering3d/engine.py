# rendering3d/engine.py
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
import sys

from mission.mission_profile import MissionProfile
from simulation.world import World
from rendering3d.scene_manager import SceneManager
from rendering3d.camera_controller import CameraController
from rendering3d.earth_model import EarthModel
from rendering3d.launch_pad import LaunchPad
from rendering3d.rocket_visual import RocketVisual

class AppEngine(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        self.camLens.setFar(30000000) 
        
        self.init_simulation()
        
        self.accept("space", self.start_mission)
        self.accept("arrow_right", self.increase_warp)
        self.accept("arrow_left", self.decrease_warp)
        self.accept("c", self.cycle_camera) 
        self.accept("escape", sys.exit)
        
        self.taskMgr.add(self.update_task, "update_task")
        
    def init_simulation(self):
        self.mission = MissionProfile("FALCON_9", "LEO")
        self.world = World(self.mission)
        self.world.time_warp = 1.0
        
        self.scene = SceneManager(self)
        self.earth = EarthModel(self)
        self.pad = LaunchPad(self)
        self.rocket_viz = RocketVisual(self, self.world.rocket)
        self.camera_ctrl = CameraController(self, self.rocket_viz.head_node)
        
    def restart_mission(self):
        self.rocket_viz.head_node.removeNode()
        for dv in self.rocket_viz.debris_visuals:
            dv["node"].removeNode()
        self.earth.destroy()
        self.pad.pad_root.removeNode()
        self.scene.destroy()
        
        self.init_simulation()
        
    def cycle_camera(self):
        if hasattr(self, 'camera_ctrl'):
            self.camera_ctrl.cycle_mode()
        
    def start_mission(self):
        if self.world.phase == 0: 
            self.world.start()
            
    def increase_warp(self):
        if self.world.time_warp < 100.0:
            self.world.time_warp *= 2.0
            
    def decrease_warp(self):
        if self.world.time_warp > 1.0:
            self.world.time_warp /= 2.0
            
    def update_task(self, task):
        dt = globalClock.getDt() 
        
        self.world.update(dt)
        self.rocket_viz.sync(self.world.rocket, self.world.phase, self.world.debris, dt)
        self.camera_ctrl.update()
        
        alt = self.world.rocket.get_altitude()
        self.scene.update_atmosphere(alt)
        self.scene.update_ui(self.world.time_elapsed, alt, self.world.rocket.get_velocity_mag(), self.world.phase, self.world.time_warp)

        return Task.cont
