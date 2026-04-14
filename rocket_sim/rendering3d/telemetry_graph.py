# rendering3d/telemetry_graph.py
from panda3d.core import LineSegs, NodePath, TextNode, CardMaker
from direct.gui.OnscreenText import OnscreenText
import collections
import math
from physics.constants import EARTH_RADIUS

class TrajectoryGraph:
    def __init__(self, engine, x, y, width=0.25, height=0.3, title="Trajectory", color=(1, 1, 0, 1), scale_ratio=1.0):
        self.engine = engine
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.scale_ratio = scale_ratio 
        self.data_pts = collections.deque(maxlen=200)
        
        self.root = engine.aspect2d.attachNewNode(f"graph_{title}")
        self.root.setPos(x, 0, y)
        
        ls = LineSegs()
        ls.setColor(0.2, 0.2, 0.2, 0.9)
        ls.setThickness(2.0)
        ls.moveTo(0, 0, 0)
        ls.drawTo(width, 0, 0)
        ls.drawTo(width, 0, height)
        ls.drawTo(0, 0, height)
        ls.drawTo(0, 0, 0)
        self.bg_node = self.root.attachNewNode(ls.create())
        
        if scale_ratio > 1000.0:
            ls2 = LineSegs()
            ls2.setColor(0.1, 0.5, 0.2, 0.5)
            cx, cy = width/2.0, height/2.0
            r = (EARTH_RADIUS/1000.0) / scale_ratio * (width/2)
            for i in range(37):
                a = math.radians(i*10)
                px = cx + r*math.cos(a)
                py = cy + r*math.sin(a)
                if i==0: ls2.moveTo(px,0,py)
                else: ls2.drawTo(px,0,py)
            self.root.attachNewNode(ls2.create())
        else:
            ls2 = LineSegs()
            ls2.setColor(0.1, 0.5, 0.2, 0.5)
            ls2.moveTo(0,0,0)
            ls2.drawTo(width,0,0)
            self.root.attachNewNode(ls2.create())

        self.line_node = self.root.attachNewNode("line")
        self.title_text = OnscreenText(text=title, pos=(x + 0.02, y + height - 0.05), scale=0.035, fg=(1,1,1,1), align=TextNode.ALeft)

    def add_data(self, px, py):
        kx = px / 1000.0
        ky = py / 1000.0
        self.data_pts.append((kx, ky))
        self._redraw()
        
    def _redraw(self):
        self.line_node.getChildren().detach()
        if len(self.data_pts) < 2: return
        
        ls = LineSegs()
        ls.setColor(*self.color)
        ls.setThickness(2.0)
        
        cx, cy = 0.0, 0.0
        if self.scale_ratio > 1000.0:
            cx, cy = self.width/2.0, self.height/2.0
            
        for i, (kx, ky) in enumerate(self.data_pts):
            mx = cx + (kx / self.scale_ratio) * self.width
            if self.scale_ratio > 1000.0:
                my = cy + (ky / self.scale_ratio) * self.height
            else:
                my = cy + ((ky - (EARTH_RADIUS/1000.0)) / self.scale_ratio) * self.height
                
            if i == 0:
                 ls.moveTo(mx, 0, my)
            else:
                 ls.drawTo(mx, 0, my)
                 
        geom = ls.create()
        self.line_node.attachNewNode(geom)
        
    def destroy(self):
        self.root.removeNode()
        self.title_text.destroy()


class RollingGraph:
    def __init__(self, engine, x, y, width=0.25, height=0.25, title="Graph", color=(0, 1, 0, 1), max_val=100.0, max_pts=50):
        self.engine = engine
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.max_val = max_val
        self.max_pts = max_pts
        
        self.data = collections.deque(maxlen=max_pts)
        
        self.root = engine.aspect2d.attachNewNode(f"graph_{title}")
        self.root.setPos(x, 0, y)
        
        ls = LineSegs()
        ls.setColor(0.3, 0.3, 0.3, 0.9)
        ls.setThickness(2.0)
        ls.moveTo(0, 0, 0)
        ls.drawTo(width, 0, 0)
        ls.drawTo(width, 0, height)
        ls.drawTo(0, 0, height)
        ls.drawTo(0, 0, 0)
        self.bg_node = self.root.attachNewNode(ls.create())
        
        self.line_node = self.root.attachNewNode("line")
        
        self.title_text = OnscreenText(text=title, pos=(x + 0.02, y + height - 0.05), scale=0.035, fg=(1,1,1,1), align=TextNode.ALeft)
        self.val_text = OnscreenText(text="0.0", pos=(x + width - 0.02, y + height - 0.05), scale=0.035, fg=color, align=TextNode.ARight)

    def add_data(self, val):
        self.data.append(val)
        if val > self.max_val * 0.9:
            self.max_val = val * 1.5
            
        self.val_text.setText(f"{val:.2f}")
        self._redraw()
        
    def _redraw(self):
        self.line_node.getChildren().detach()
        if len(self.data) < 2: return
        
        ls = LineSegs()
        ls.setColor(*self.color)
        ls.setThickness(2.0)
        
        step_x = self.width / (len(self.data) - 1)
        for i, val in enumerate(self.data):
            px = i * step_x
            py = max(0, min(self.height, (val / self.max_val) * self.height))
            if i == 0:
                ls.moveTo(px, 0, py)
            else:
                ls.drawTo(px, 0, py)
                
        geom = ls.create()
        self.line_node.attachNewNode(geom)
        
    def destroy(self):
        self.root.removeNode()
        self.title_text.destroy()
        self.val_text.destroy()


class TelemetryDashboard:
    def __init__(self, engine):
        self.engine = engine
        
        cm = CardMaker("dash_bg")
        cm.setFrame(-1.4, 1.4, -1.0, -0.6)
        self.bg = engine.aspect2d.attachNewNode(cm.generate())
        self.bg.setColor(0.1, 0.1, 0.1, 0.95)
        
        self.speed_label = OnscreenText(text="SPEED: 0.0 m/s", pos=(-1.3, -0.75), scale=0.06, fg=(0.2, 1, 0.2, 1), align=TextNode.ALeft)
        self.alt_label = OnscreenText(text="ALT: 0.0 m", pos=(-1.3, -0.85), scale=0.06, fg=(0, 0.8, 1, 1), align=TextNode.ALeft)
        self.g_label = OnscreenText(text="G-LOAD: 1.0", pos=(-1.3, -0.95), scale=0.05, fg=(0.8, 0.2, 0.8, 1), align=TextNode.ALeft)
        
        y_base = -0.95
        h = 0.25
        
        self.graph_alt = RollingGraph(engine, -0.5, y_base, width=0.25, height=h, title="Alt (km)", color=(0, 0.8, 1, 1), max_val=200.0)
        self.graph_vel = RollingGraph(engine, -0.2, y_base, width=0.25, height=h, title="Vel (km/s)", color=(1, 0.5, 0, 1), max_val=8.0)
        self.graph_q   = RollingGraph(engine, 0.1, y_base, width=0.25, height=h, title="Max-Q (kPa)", color=(1, 0, 0, 1), max_val=50.0)
        
        self.traj_local = TrajectoryGraph(engine, 0.45, y_base, width=0.35, height=h, title="Ascent Profile", scale_ratio=500.0, color=(1, 1, 0, 1))
        self.traj_orbit = TrajectoryGraph(engine, 0.85, y_base, width=0.35, height=h, title="Global Orbit", scale_ratio=15000.0, color=(1, 0.2, 0.8, 1))
        
        self.last_vel = 0.0
        self.update_timer = 0.0
        
    def update(self, dt, rocket):
        alt = rocket.get_altitude()
        vel = rocket.get_velocity_mag()
        
        self.speed_label.setText(f"SPEED: {vel:.1f} m/s")
        self.alt_label.setText(f"ALT: {alt:.1f} m")
        
        self.update_timer += dt
        if self.update_timer < 0.2: 
            return
            
        dt_t = self.update_timer
        self.update_timer = 0.0
        
        if dt_t > 0:
            accel = (vel - self.last_vel) / dt_t
        else:
            accel = 0.0
        self.last_vel = vel
        
        g_force = accel / 9.81
        if alt < 10 and g_force < 0: g_force = 1.0 
        elif alt > 10: g_force += max(0, 1.0 - (alt/200000.0)) 
        
        self.g_label.setText(f"G-LOAD: {abs(g_force):.2f}")
        
        rho = 1.225 * math.exp(-alt / 8500.0) if alt > 0 else 1.225
        q = 0.5 * rho * vel**2
        
        self.graph_alt.add_data(alt / 1000.0)
        self.graph_vel.add_data(vel / 1000.0)
        self.graph_q.add_data(q / 1000.0) 
        
        self.traj_local.add_data(rocket.x, rocket.y)
        self.traj_orbit.add_data(rocket.x, rocket.y)
        
    def destroy(self):
        self.bg.removeNode()
        self.speed_label.destroy()
        self.alt_label.destroy()
        self.g_label.destroy()
        self.graph_alt.destroy()
        self.graph_vel.destroy()
        self.graph_q.destroy()
        self.traj_local.destroy()
        self.traj_orbit.destroy()
