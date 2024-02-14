from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal

import open3d as o3d
import os
import numpy as np
import pygfx as gfx
from wgpu.gui.qt import WgpuCanvas

IMAGE_SHAPE = (600, 800)  # (height, width)
CANVAS_SIZE = (800, 600)  # (width, height)

class Scene3D(QtWidgets.QWidget):
    
    closed = pyqtSignal()
    
    def __init__(self):
        super().__init__(None)
        self.resize(640, 480)

        self.toolbar = QtWidgets.QToolBar("My main toolbar")
        
        button_action = QtWidgets.QAction("Add mesh", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(self.load_mesh)
        self.toolbar.addAction(button_action)
        
        # button_action = QAction(QIcon("bug.png"), "Your button", self)
        # button_action.setStatusTip("This is your button")
        # button_action.triggered.connect(self.onMyToolBarButtonClick)
        # button_action.setCheckable(True)
        # toolbar.addAction(button_action)
        
         
        # self._button = QtWidgets.QPushButton("Add mesh", self)
        # self._button.clicked.connect(self.load_mesh)        
        
        self._canvas = WgpuCanvas(parent=self)
        self._renderer = gfx.WgpuRenderer(self._canvas)
        self._scene = gfx.Scene()
        self._camera = gfx.PerspectiveCamera()

        self._canvas.request_draw(self.animate)
        
        #use the event called before rendering the scene to check if the camera has changed;
        self._renderer.add_event_handler(self.camera_changed, "before_render")
        
        self._controller = gfx.TrackballController(self._camera, register_events=self._renderer)
        
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.toolbar)
        layout.addWidget(self._canvas)
        
        
    def camera_changed(self, event):
        print(self._camera.camera_matrix)
    
    def animate(self):
        self._renderer.render(self._scene, self._camera)
    
    def mesh_picking(self, event):
        
        if event.button == 1 and "Control" in event.modifiers:
            face_ix = event.pick_info["face_index"]
            
            #face_coords are not normalized; hence, divide by their sum first before using the further
            face_coords = np.array(event.pick_info["face_coord"]).reshape(3, 1) 
            face_coords /= np.sum(face_coords)
            
            face_vertex_ix = event.pick_info["world_object"].geometry.indices.data[face_ix, :]
            face_vertex_pos = event.pick_info["world_object"].geometry.positions.data[face_vertex_ix, :]
            
            click_pos = np.sum(face_vertex_pos*face_coords, axis=0)
            
            click_geom = gfx.Geometry(positions=click_pos.astype(np.float32).reshape(1, 3))
            click_obj = gfx.Points(click_geom, gfx.PointsMaterial(color=(0.78, 0, 0, 1), size=10))
            self._scene.add(click_obj)
                        
            click_text = gfx.Text(
                gfx.TextGeometry(markdown="**1**", font_size=26, anchor="Bottom-Center", screen_space=True),
                gfx.TextMaterial(color="#fff", outline_color="#000", outline_thickness=0.15))
            click_text.local.position = click_obj.geometry.positions.data[0, :] + [0, 0, 10]
            
            click_obj.add(click_text)           
            
            self._canvas.request_draw(self.animate)

    def load_mesh(self):
        mesh_path = QtWidgets.QFileDialog.getOpenFileName(None, "Open mesh", "", ("Mesh (*.ply)"))[0]
        
        if mesh_path:
            if os.path.exists(mesh_path):
                
                print("Reading mesh...")
                o3d_mesh = o3d.io.read_triangle_mesh(mesh_path)
                o3d_mesh.compute_vertex_normals()
                
                verts = np.asarray(o3d_mesh.vertices)
                faces = np.asarray(o3d_mesh.triangles).astype(np.uint32)
                norms = np.asarray(o3d_mesh.vertex_normals).astype(np.float32)
                
                verts_loc = verts - np.min(verts, axis=0)
                                
                print("Loading mesh...")
                mesh_geom = gfx.geometries.Geometry(indices=faces, positions=verts_loc.astype(np.float32), normals=norms)
                mesh_material = gfx.MeshPhongMaterial(color="#BEBEBE", side="FRONT", shininess=10)

                mesh = gfx.Mesh(mesh_geom, mesh_material)
                mesh.add_event_handler(self.mesh_picking, "pointer_down")
                self._scene.add(mesh)
                
                self._scene.add(gfx.AmbientLight(intensity=1), gfx.DirectionalLight())
                
                self._camera.show_object(self._scene)
    
    def closeEvent(self, event):
        self.closed.emit()
        
# # app = QtWidgets.QApplication([])
# # m = Scene3D()
# # m.show()

# if __name__ == "__main__":
#     # app = QtWidgets.QApplication([])
#     m = Scene3D()
#     m.show()
#     # app.exec()
