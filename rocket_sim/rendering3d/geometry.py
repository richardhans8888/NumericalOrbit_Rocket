# rendering3d/geometry.py
from panda3d.core import Geom, GeomNode, GeomVertexData, GeomVertexFormat, GeomVertexWriter
from panda3d.core import GeomTriangles, NodePath
from panda3d.core import LineSegs
import math

def create_cylinder(name, radius=1.0, height=2.0, segments=16):
    format = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("vdata", format, Geom.UHStatic)
    vwriter = GeomVertexWriter(vdata, "vertex")
    nwriter = GeomVertexWriter(vdata, "normal")
    cwriter = GeomVertexWriter(vdata, "color")
    
    tris = GeomTriangles(Geom.UHStatic)
    
    for i in range(segments + 1):
        angle = 2.0 * math.pi * i / segments
        ca = math.cos(angle)
        sa = math.sin(angle)
        
        vwriter.addData3(radius * ca, radius * sa, 0)
        nwriter.addData3(ca, sa, 0)
        cwriter.addData4(1, 1, 1, 1)
        
        vwriter.addData3(radius * ca, radius * sa, height)
        nwriter.addData3(ca, sa, 0)
        cwriter.addData4(1, 1, 1, 1)
        
    for i in range(segments):
        b1 = i * 2
        t1 = i * 2 + 1
        b2 = (i + 1) * 2
        t2 = (i + 1) * 2 + 1
        
        tris.addVertices(b1, b2, t1)
        tris.addVertices(b2, t2, t1)
        
    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    return NodePath(node)

def create_cone(name, radius=1.0, height=2.0, segments=16):
    format = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("vdata", format, Geom.UHStatic)
    vwriter = GeomVertexWriter(vdata, "vertex")
    nwriter = GeomVertexWriter(vdata, "normal")
    cwriter = GeomVertexWriter(vdata, "color")
    
    tris = GeomTriangles(Geom.UHStatic)
    
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        ca = math.cos(angle)
        sa = math.sin(angle)
        
        vwriter.addData3(radius * ca, radius * sa, 0)
        slant_len = math.sqrt(radius*radius + height*height)
        nx = ca * (height / slant_len)
        ny = sa * (height / slant_len)
        nz = radius / slant_len
        nwriter.addData3(nx, ny, nz)
        cwriter.addData4(1, 1, 1, 1)
        
    tip_idx = segments
    vwriter.addData3(0, 0, height)
    nwriter.addData3(0, 0, 1)
    cwriter.addData4(1, 1, 1, 1)
    
    for i in range(segments):
        v1 = i
        v2 = (i + 1) % segments
        tris.addVertices(v1, v2, tip_idx)
        
    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    return NodePath(node)
