# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MoniQueDialog
                                 A QGIS plugin
 Monoplotting oblique images.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-02-07
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Sebastian Mikolka-Flöry
        email                : s.floery@gmx.at
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.gui import QgsMapCanvas
from wgpu.gui.qt import WgpuCanvas
import pygfx as gfx
import open3d as o3d
import numpy as np
from PIL import Image

from qgis.core import QgsFeature, QgsFeatureRequest, QgsRasterLayer, QgsProject

from .dlg_create import CreateDialog
from .dlg_orient import OrientDialog
from .dlg_meta_gcp import GcpMetaDialog
from ..tools.ImgPickerTool import ImgPickerTool

from ..camera import Camera

class MainDialog(QtWidgets.QDialog):
    
    load_project_signal = QtCore.pyqtSignal(object)
    close_dialog_signal = QtCore.pyqtSignal()
    
    def __init__(self, parent=None, plugin_dir=None):
        """Constructor."""
        super(MainDialog, self).__init__()
        
        self.plugin_dir = plugin_dir
        self.icon_dir = os.path.join(self.plugin_dir, "gfx", "icon")
        
        #will be set from monique.py
        self.camera_collection = None
        
        self.setWindowTitle("moniQue")
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.plugin_dir, "icon.png")))

        self.menu = QtWidgets.QMenuBar(self)
        self.file_menu = QtWidgets.QMenu("&File", self)
        self.menu.addMenu(self.file_menu)
        
        self.img_menu = QtWidgets.QMenu("&Images", self)
        self.img_menu.setEnabled(False)
        self.menu.addMenu(self.img_menu)
        
        self.create_action = QtWidgets.QAction("&New project", self)
        self.create_action.triggered.connect(self.show_create_dlg)
        self.file_menu.addAction(self.create_action)
        
        self.load_action = QtWidgets.QAction("&Load project", self)
        self.load_action.triggered.connect(self.load_project)
        self.file_menu.addAction(self.load_action)
        
        self.save_as_action = QtWidgets.QAction("&Save project as", self)
        self.save_as_action.triggered.connect(self.save_project_as)
        self.file_menu.addAction(self.save_as_action)
        
        self.import_action = QtWidgets.QAction("&Import images", self)
        self.import_action.triggered.connect(self.import_images)
        self.img_menu.addAction(self.import_action)
        
        self.main_toolbar = QtWidgets.QToolBar("My main toolbar")
        self.main_toolbar.setIconSize(QtCore.QSize(20, 20))

        self.btn_ori_tool = QtWidgets.QAction("Open orientation dialog", self)
        self.btn_ori_tool.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "camera.png")))
        self.btn_ori_tool.triggered.connect(self.show_orient_dlg)
        self.btn_ori_tool.setCheckable(True)
        self.btn_ori_tool.setEnabled(False)
        self.main_toolbar.addAction(self.btn_ori_tool)
        
        self.main_toolbar.addSeparator()
        
        self.btn_mono_tool = QtWidgets.QAction("Activate monoplotting tool", self)
        self.btn_mono_tool.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionAddPolyline.png")))
        self.btn_mono_tool.setEnabled(False)
        # # button_action.triggered.connect(self.load_mesh)
        self.main_toolbar.addAction(self.btn_mono_tool)
        
        self.btn_mono_select = QtWidgets.QAction("Select monoplotted lines", self)
        self.btn_mono_select.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionSelectRectangle.png")))
        self.btn_mono_select.setEnabled(False)
        # button_action.triggered.connect(self.load_mesh)
        self.main_toolbar.addAction(self.btn_mono_select)
        
        btn_mono_vertex = QtWidgets.QAction("Edit monoplotted lines", self)
        btn_mono_vertex.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionVertexToolActiveLayer.png")))
        btn_mono_vertex.setEnabled(False)
        # button_action.triggered.connect(self.load_mesh)
        self.main_toolbar.addAction(btn_mono_vertex)
        
        self.img_toolbar = QtWidgets.QToolBar()
        self.img_toolbar.setIconSize(QtCore.QSize(20, 20))
        self.img_canvas = QgsMapCanvas(parent=self)
        self.img_canvas.setMinimumSize(QtCore.QSize(300, 16777215))
        
        btn_img_pan = QtWidgets.QAction("Pan (Image)", self)
        btn_img_pan.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionPan.png")))
        btn_img_pan.setCheckable(True)
        # btn_img_pan.triggered.connect(self.load_mesh)
        self.img_toolbar.addAction(btn_img_pan)
        
        btn_img_extent = QtWidgets.QAction("Zoom to image extent.", self)
        btn_img_extent.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionZoomFullExtent.png")))
        btn_img_extent.triggered.connect(self.set_img_canvas_extent)
        self.img_toolbar.addAction(btn_img_extent)
        
        self.obj_toolbar = QtWidgets.QToolBar()
        self.obj_toolbar.setIconSize(QtCore.QSize(20, 20))
        self.obj_canvas = WgpuCanvas(parent=self)
        self.obj_canvas.setMinimumSize(QtCore.QSize(300, 16777215))
        
        btn_obj_extent = QtWidgets.QAction("Zoom to image extent.", self)
        btn_obj_extent.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionZoomFullExtent.png")))
        self.obj_toolbar.addAction(btn_obj_extent)
        # btn_img_pan.triggered.connect(self.load_mesh)
        
        self.obj_renderer = gfx.WgpuRenderer(self.obj_canvas)
        self.obj_scene = gfx.Scene()
        self.obj_camera = gfx.PerspectiveCamera()

        self.obj_canvas.request_draw(self.animate)
        self.obj_controller = gfx.TrackballController(self.obj_camera, register_events=self.obj_renderer)
        
        self.list_toolbar = QtWidgets.QToolBar()
        self.list_toolbar.setIconSize(QtCore.QSize(20, 20))
        
        self.img_list = QtWidgets.QListWidget()
        self.img_list.setAlternatingRowColors(True)
        self.img_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        # self.img_list.itemChanged.connect(self.toggle_camera)
        self.img_list.itemSelectionChanged.connect(self.toggle_camera)
        self.img_list.setEnabled(False)
        
        self.split_canvas = QtWidgets.QSplitter()
        split_max_width = QtWidgets.QApplication.primaryScreen().size().width()
        
        self.img_split = QtWidgets.QWidget()
        img_split_layout = QtWidgets.QVBoxLayout()
        img_split_layout.setSpacing(0)
        img_split_layout.setContentsMargins(0, 0, 0, 0)
        img_split_layout.addWidget(self.img_toolbar)
        img_split_layout.addWidget(self.img_canvas)
        self.img_split.setLayout(img_split_layout)
        
        self.obj_split = QtWidgets.QWidget()
        obj_split_layout = QtWidgets.QVBoxLayout()
        obj_split_layout.setSpacing(0)
        obj_split_layout.setContentsMargins(0, 0, 5, 0)
        obj_split_layout.addWidget(self.obj_toolbar)
        obj_split_layout.addWidget(self.obj_canvas)
        self.obj_split.setLayout(obj_split_layout)
        
        self.split_canvas.addWidget(self.img_split)
        self.split_canvas.addWidget(self.obj_split)
        self.split_canvas.setSizes([split_max_width, split_max_width])
        
        self.list_widget = QtWidgets.QWidget()
        self.list_widget.setMinimumSize(QtCore.QSize(150, 16777215))
        self.list_widget.setMaximumSize(QtCore.QSize(150, 16777215))
        list_widget_layout = QtWidgets.QVBoxLayout()
        list_widget_layout.setSpacing(0)
        list_widget_layout.setContentsMargins(0, 16, 0, 0)
        list_widget_layout.addWidget(self.list_toolbar)
        list_widget_layout.addWidget(self.img_list)
        self.list_widget.setLayout(list_widget_layout)
        
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(5, 0, 5, 0)
        main_layout.addWidget(self.split_canvas)
        main_layout.addWidget(self.list_widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setMenuBar(self.menu)
        layout.addWidget(self.main_toolbar)
        layout.addLayout(main_layout)
        self.setLayout(layout)
        
    def set_layers(self, lyr_dict):
        self.reg_lyr = lyr_dict["reg_lyr"]
        self.cam_lyr = lyr_dict["cam_lyr"]        
        self.img_lyr = lyr_dict["img_lyr"]
        self.img_line_lyr = lyr_dict["img_line_lyr"]
        self.img_gcps_lyr = lyr_dict["img_gcps_lyr"]
        self.map_line_lyr = lyr_dict["map_line_lyr"]
        self.map_gcps_lyr = lyr_dict["map_gcps_lyr"]
        
    def show_create_dlg(self):
        self.create_dlg = CreateDialog(parent=self, icon_dir=self.icon_dir)
        self.create_dlg.created_signal.connect(self.on_created_signal)
        self.create_dlg.show()
    
    def show_orient_dlg(self):
        if self.btn_ori_tool.isChecked():
            self.orient_dlg = OrientDialog(parent=self, icon_dir=self.icon_dir, active_iid=self.active_camera.iid)
            self.orient_dlg.show()

    def on_created_signal(self, data):
        self.load_project(gpkg_path=data["gpkg_path"])
    
    def load_project(self, gpkg_path=None):
        if not gpkg_path:
            gpkg_path = QtWidgets.QFileDialog.getOpenFileName(None, "Open project", "", ("Geopackage (*.gpkg)"))[0]
        
        #load dialog could be cancled; hence, gkpk_path must not always be defined
        if gpkg_path:
            self.load_project_signal.emit({"gpkg_path":gpkg_path})
    
    def save_project_as(self):
        pass
    
    def closeEvent(self, event):
        self.close_dialog_signal.emit()
    
    def add_mesh_to_obj_canvas(self, o3d_mesh):
        
        verts = np.asarray(o3d_mesh.vertices)
        faces = np.asarray(o3d_mesh.triangles).astype(np.uint32)
        norms = np.asarray(o3d_mesh.vertex_normals).astype(np.float32)
        
        verts_loc = verts - np.min(verts, axis=0)
                        
        print("Loading mesh...")
        mesh_geom = gfx.geometries.Geometry(indices=faces, positions=verts_loc.astype(np.float32), normals=norms)
        mesh_material = gfx.MeshPhongMaterial(color="#BEBEBE", side="FRONT", shininess=10)

        print("Adding mesh to canvas...")
        mesh = gfx.Mesh(mesh_geom, mesh_material)
        # # mesh.add_event_handler(self.mesh_picking, "pointer_down")
        self.obj_scene.add(mesh)
        
        print("Adding lights...")
        self.obj_scene.add(gfx.AmbientLight(intensity=1), gfx.DirectionalLight())
        self.obj_camera.show_object(self.obj_scene)
        
    def animate(self):
        self.obj_renderer.render(self.obj_scene, self.obj_camera)
    
    def import_images(self):
        """Import selected images.
        """
        
        img_paths = QtWidgets.QFileDialog.getOpenFileNames(None, "Load images", "", ("Image (*.tif *.tiff *.png *.jpg *.jpeg)"))[0]
        
        loaded_imgs = [self.img_list.item(x).text() for x in range(self.img_list.count())]
        
        for path in img_paths:
            [img_name, img_ext] = os.path.basename(path).rsplit(".", 1)
            
            if img_name not in loaded_imgs:
                
                
                img = Image.open(path)
                img_h = img.height
                img_w = img.width
                                
                cam = Camera(iid=img_name, path=path, ext=img_ext, is_oriented=False, img_h=img_h, img_w=img_w)
                self.camera_collection[cam.iid] = cam
                
                self.add_camera_to_list(cam)
                self.add_camera_to_cam_lyr(cam)
                
    def add_camera_to_list(self, camera):
        """Add camera to the image list.

        Args:
            camera (_type_): Camera object.
        """
        
        item = QtWidgets.QListWidgetItem(camera.iid)
        item.setSizeHint(QtCore.QSize(24, 24))
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Unchecked)
        self.img_list.addItem(item)

    def add_camera_to_cam_lyr(self, camera):
        """Add camera to the camera GPKG layer.

        Args:
            camera (_type_): Camera object.
        """
        feat = QgsFeature(self.cam_lyr.fields())
        feat["iid"] = camera.iid
        feat["path"] = camera.path
        feat["ext"] = camera.ext
        feat["img_w"] = camera.img_w
        feat["img_h"] = camera.img_h
        
        pr = self.cam_lyr.dataProvider()
        pr.addFeatures([feat])
                
        self.cam_lyr.commitChanges()

    def uncheck_list_items(self, item):
        for ix in range(self.img_list.count()):
            
            curr_item = self.img_list.item(ix)
            
            if (curr_item != item) & (curr_item.checkState() == QtCore.Qt.Checked):
                curr_item.setCheckState(QtCore.Qt.Unchecked)

    def load_img(self, iid, path):
        img_lyr = QgsRasterLayer(path, iid)
                
        if not img_lyr.isValid():
            pass
            # self.msg_bar.pushMessage("Error", "Could not load %s!" % (img_path), level=Qgis.Critical, duration=3)
        else:
            if self.img_lyr is not None:
                QgsProject.instance().removeMapLayer(self.img_lyr.id())
                
            QgsProject.instance().addMapLayer(img_lyr, False) #False --> do not add layer to LayerTree --> not visible in qgis main canvas
            self.img_canvas.setExtent(img_lyr.extent())
            self.img_canvas.setLayers([self.img_gcps_lyr, self.img_line_lyr, img_lyr])
            self.img_canvas.refresh()
            self.img_lyr = img_lyr
    
    def set_img_canvas_extent(self):
        self.img_canvas.setExtent(self.img_lyr.extent())
        self.img_canvas.refresh()
    
    def toggle_camera(self):
        
        #before for the first time an image is loaded
        #into to canvas self.img_lyr is None; Hence, until
        #than the button shall be disabled
        if self.img_lyr is None:
            self.btn_ori_tool.setEnabled(True)
        
        item = self.img_list.selectedItems()[0]
        item.setCheckState(QtCore.Qt.Checked)
        self.uncheck_list_items(item)
        
        # # Get his status when the check status changes.
        # if item.checkState() == QtCore.Qt.Checked:
                    
        iid = item.text()
        iid_path = self.camera_collection[iid].path
        
        self.load_img(iid, iid_path)
        
        expression = "iid = '%s'" % (iid)
        self.img_line_lyr.setSubsetString(expression) #show only those lines which correspond to the currently selected image
        self.img_gcps_lyr.setSubsetString(expression)
        self.map_gcps_lyr.setSubsetString(expression)

        self.active_camera = self.camera_collection[iid]
        self.setWindowTitle("%s - %s" % (self.project_name, iid))
        
        # #     #highlight currently selected camera
        # #     #clear previously highlighter cameras
        # #     self.clear_highlighted_features()
        # #     self.clear_vertex_markers()

        # #     # cam_feat = list(self.cam_lyr.getFeatures(request))[0]
        # #     # self.cam_h = QgsHighlight(self.map_canvas, cam_feat, self.cam_lyr)
        # #     # self.cam_h.setColor(self.highlight_color)
        # #     # self.cam_h.setFillColor(self.highlight_color)
        # #     # self.cam_h.show()
                
        # #     # cam_hfov_feat = list(self.cam_hfov_lyr.getFeatures(request))[0]
        # #     # self.hfov_h = QgsHighlight(self.map_canvas, cam_hfov_feat, self.cam_hfov_lyr)
        # #     # self.hfov_h.setColor(self.highlight_color)
        # #     # self.hfov_h.setFillColor(self.highlight_color)
        # #     # self.hfov_h.show()

        # #     # self.mono_tool.set_camera(self.active_camera)
        # #     # self.vertex_tool.set_camera(self.active_camera)
        # #     # self.orient_tool.set_camera(self.active_camera)
            
        # #     if self.active_camera.is_oriented:
        # #         self.dlg.btn_monotool.setEnabled(True)
        # #         self.dlg.btn_select.setEnabled(True)
        # #         self.dlg.btn_oritool.setEnabled(True)
        # #         # self.dlg.btn_delete.setEnabled(True)
        # #         self.dlg.btn_vertex.setEnabled(True)
        # #     else:
        # #         self.dlg.btn_oritool.setEnabled(True)

        # elif item.checkState() == QtCore.Qt.Unchecked:
        #     QgsProject.instance().removeMapLayer(self.img_lyr.id())
            
        #     self.img_canvas.refresh()
        #     self.active_camera = None
        #     self.img_lyr = None
            
        # #     self.dlg.btn_monotool.setEnabled(False)
        # #     self.dlg.btn_monotool.setChecked(False)
        # #     self.deactivate_plotting()
            
        # #     self.dlg.btn_oritool.setEnabled(False)
        # #     self.dlg.btn_oritool.setChecked(False)
            
        # #     self.dlg.btn_select.setEnabled(False)
        # #     self.dlg.btn_select.setChecked(False)
            
        # #     self.dlg.btn_vertex.setEnabled(False)
        # #     self.dlg.btn_vertex.setChecked(False)
            
        # #     # self.dlg.btn_delete.setEnabled(False)
                        
        # #     self.clear_highlighted_features()
            
        # #     self.clear_meta_fiels()

        #     #use a filter which is not available to not show any lines in img canvas if no image is currently selected
        #     expression = "iid = 'sth_not_existing'"
        #     self.img_line_lyr.setSubsetString(expression) #show only those lines which correspond to the currently selected image
        #     self.img_gcps_lyr.setSubsetString(expression)
        #     self.map_gcps_lyr.setSubsetString(expression)
    
    def activate_gui_elements(self):
        self.img_list.setEnabled(True)
        self.img_menu.setEnabled(True)
        self.project_name = self.windowTitle()
                
    def activate_gcp_picking(self):

        self.img_picker_tool = ImgPickerTool(self.img_canvas, GcpMetaDialog())
        self.img_picker_tool.set_camera(self.active_camera)
        self.img_picker_tool.set_layers(img_lyr=self.img_gcps_lyr, map_lyr=self.map_gcps_lyr)
        self.img_canvas.setMapTool(self.img_picker_tool)

        # self.img_picker_tool.featAdded.connect(self.img_gcp_added)

    
    def deactivate_gcp_picking(self):
        print("Buuuuh")
    # def mesh_picking(self, event):
        
        # if event.button == 1 and "Control" in event.modifiers:
        #     face_ix = event.pick_info["face_index"]
            
        #     #face_coords are not normalized; hence, divide by their sum first before using the further
        #     face_coords = np.array(event.pick_info["face_coord"]).reshape(3, 1) 
        #     face_coords /= np.sum(face_coords)
            
        #     face_vertex_ix = event.pick_info["world_object"].geometry.indices.data[face_ix, :]
        #     face_vertex_pos = event.pick_info["world_object"].geometry.positions.data[face_vertex_ix, :]
            
        #     click_pos = np.sum(face_vertex_pos*face_coords, axis=0)
            
        #     click_geom = gfx.Geometry(positions=click_pos.astype(np.float32).reshape(1, 3))
        #     click_obj = gfx.Points(click_geom, gfx.PointsMaterial(color=(0.78, 0, 0, 1), size=10))
        #     self.obj_scene.add(click_obj)
                        
        #     click_text = gfx.Text(
        #         gfx.TextGeometry(markdown="**1**", font_size=26, anchor="Bottom-Center", screen_space=True),
        #         gfx.TextMaterial(color="#fff", outline_color="#000", outline_thickness=0.15))
        #     click_text.local.position = click_obj.geometry.positions.data[0, :] + [0, 0, 10]
            
        #     click_obj.add(click_text)           
            
        #     self.obj_canvas.request_draw(self.animate)