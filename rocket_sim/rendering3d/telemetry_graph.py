# rendering3d/telemetry_graph.py
from panda3d.core import LineSegs, NodePath, TextNode
from direct.gui.OnscreenText import OnscreenText
import collections
import math

class RollingGraph:
    def __init__(self, engine, x, y, width=0.6, height=0.3, title="Graph", color=(0, 1, 0, 1), max_val=100.0, max_pts=50):
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
        ls.setColor(0.1, 0.1, 0.1, 0.8)
        ls.setThickness(2.0)
        ls.moveTo(0, 0, 0)
        ls.drawTo(width, 0, 0)
        ls.drawTo(width, 0, height)
        ls.drawTo(0, 0, height)
        ls.drawTo(0, 0, 0)
        self.bg_node = self.root.attachNewNode(ls.create())
        
        self.line_node = self.root.attachNewNode("line")
        
        self.title_text = OnscreenText(text=title, pos=(x + 0.02, y + height - 0.05), scale=0.04, fg=(1,1,1,1), align=TextNode.ALeft)
        self.val_text = OnscreenText(text="0.0", pos=(x + width - 0.02, y + height - 0.05), scale=0.04, fg=color, align=TextNode.ARight)

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
        
        base_x = 0.6
        self.graph_alt = RollingGraph(engine, base_x, 0.55, title="Altitude (km)", color=(0, 0.8, 1, 1), max_val=200.0)
        self.graph_vel = RollingGraph(engine, base_x, 0.20, title="Velocity (km/s)", color=(1, 0.5, 0, 1), max_val=8.0)
        self.graph_q   = RollingGraph(engine, base_x, -0.15, title="Dyn Pressure (kPa)", color=(1, 0, 0, 1), max_val=50.0)
        self.graph_g   = RollingGraph(engine, base_x, -0.50, title="Acceleration (G)", color=(0.8, 0.2, 0.8, 1), max_val=5.0)
        
        self.last_vel = 0.0
        self.update_timer = 0.0
        
    def update(self, dt, rocket):
        self.update_timer += dt
        if self.update_timer < 0.2: 
            return
        dt_t = self.update_timer
        self.update_timer = 0.0
            
        alt = rocket.get_altitude()
        vel = rocket.get_velocity_mag()
        
        if dt_t > 0:
            accel = (vel - self.last_vel) / dt_t
        else:
            accel = 0.0
        self.last_vel = vel
        
        g_force = accel / 9.81
        if alt < 10 and g_force < 0: g_force = 1.0 
        elif alt > 10: g_force += max(0, 1.0 - (alt/200000.0)) 
        
        rho = 1.225 * math.exp(-alt / 8500.0) if alt > 0 else 1.225
        q = 0.5 * rho * vel**2
        
        self.graph_alt.add_data(alt / 1000.0)
        self.graph_vel.add_data(vel / 1000.0)
        self.graph_q.add_data(q / 1000.0) 
        self.graph_g.add_data(abs(g_force))
        
    def destroy(self):
        self.graph_alt.destroy()
        self.graph_vel.destroy()
        self.graph_q.destroy()
        self.graph_g.destroy()
