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
import json
from collections import OrderedDict

from qgis.core import QgsFeature, QgsPoint, QgsFeatureRequest, QgsRasterLayer, QgsProject, QgsJsonUtils, QgsGeometry
from qgis.gui import QgsMapToolPan

from .dlg_create import CreateDialog
from .dlg_orient import OrientDialog
from .dlg_meta_gcp import GcpMetaDialog
from ..tools.ImgPickerTool import ImgPickerTool

from ..camera import Camera
from ..helpers import create_point_3d, proj_mat_to_rkz

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
        self.create_action.triggered.connect(self.show_dlg_create)
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
        self.btn_ori_tool.triggered.connect(self.show_dlg_orient)
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
        
        self.img_pan_tool = QgsMapToolPan(self.img_canvas)
        
        
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
        
        light_gray = np.array((100, 100, 100, 255)) / 255
        background = gfx.Background(None, gfx.BackgroundMaterial([1, 1, 1, 1]))
        self.obj_scene.add(background)
        
        self.obj_camera = gfx.PerspectiveCamera(fov=45)#, depth_range=(10, 10000))

        self.obj_canvas.request_draw(self.animate)
        self.obj_controller = gfx.TrackballController(self.obj_camera, register_events=self.obj_renderer, damping=0)
        
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
        
        self.sel_gid = None
        
    def set_layers(self, lyr_dict):
        self.reg_lyr = lyr_dict["reg_lyr"]
        self.cam_lyr = lyr_dict["cam_lyr"]        
        self.img_lyr = None                     #will be set layer when terrestrial image is loaded
        
        self.img_line_lyr = lyr_dict["img_line_lyr"]
        self.map_line_lyr = lyr_dict["map_line_lyr"]
        
        self.img_gcps_lyr = lyr_dict["img_gcps_lyr"]
        self.map_gcps_lyr = lyr_dict["map_gcps_lyr"]
        
        self.img_gcps_gid_ix = self.img_gcps_lyr.dataProvider().fieldNameIndex('gid')
        
        self.map_gcps_gid_ix = self.map_gcps_lyr.dataProvider().fieldNameIndex('gid')
        self.map_gcps_lyr_obj_x_ix = self.map_gcps_lyr.dataProvider().fieldNameIndex('obj_x')
        self.map_gcps_lyr_obj_y_ix = self.map_gcps_lyr.dataProvider().fieldNameIndex('obj_y')
        self.map_gcps_lyr_obj_z_ix = self.map_gcps_lyr.dataProvider().fieldNameIndex('obj_z')
        
        #define layers which should be shown/considered in which canvas
        self.img_canvas.setLayers([self.img_line_lyr, self.img_gcps_lyr])
        self.img_canvas.setMapTool(self.img_pan_tool)
        
    def show_dlg_create(self):
        self.dlg_create = CreateDialog(parent=self, icon_dir=self.icon_dir)
        self.dlg_create.created_signal.connect(self.on_created_signal)
        self.dlg_create.show()
    
    def show_dlg_orient(self):
        if self.btn_ori_tool.isChecked():
            self.dlg_orient = OrientDialog(parent=self, icon_dir=self.icon_dir, active_iid=self.active_camera.iid)

            self.dlg_orient.gcp_selected_signal.connect(self.select_gcp)
            self.dlg_orient.gcp_deselected_signal.connect(self.deselect_gcp)
            self.dlg_orient.gcp_delete_signal.connect(self.delete_gcp)
            self.dlg_orient.get_camera_signal.connect(self.get_obj_canvas_camera)
            
            self.dlg_orient.add_gcps_from_lyr(self.get_gcps_from_gpkg())
            
            self.dlg_orient.show()

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
        
        if self.img_lyr is not None:
            QgsProject.instance().removeMapLayer(self.img_lyr.id())
            self.img_lyr = None
        
        if self.cam_lyr is not None:
            QgsProject.instance().removeMapLayer(self.cam_lyr.id())
            self.cam_lyr = None
        
        if self.img_line_lyr is not None:
            QgsProject.instance().removeMapLayer(self.img_line_lyr.id())
            self.img_line_lyr = None
        
        if self.img_gcps_lyr is not None:
            QgsProject.instance().removeMapLayer(self.img_gcps_lyr.id())
            self.img_gcps_lyr = None
        
        if self.map_line_lyr is not None:
            QgsProject.instance().removeMapLayer(self.map_line_lyr.id())
            self.map_line_lyr = None
        
        if self.map_gcps_lyr is not None:
            QgsProject.instance().removeMapLayer(self.map_gcps_lyr.id())
            self.map_gcps_lyr = None
        
        if self.reg_lyr is not None:
            QgsProject.instance().removeMapLayer(self.reg_lyr.id())
            self.reg_lyr = None
        
        self.img_canvas.refresh()
        self.close_dialog_signal.emit()
    
    def add_mesh_to_obj_canvas(self, o3d_mesh, min_xyz):
        
        verts = np.asarray(o3d_mesh.vertices)
        faces = np.asarray(o3d_mesh.triangles).astype(np.uint32)
        norms = np.asarray(o3d_mesh.vertex_normals).astype(np.float32)
                        
        # print("Loading mesh...")
        mesh_geom = gfx.geometries.Geometry(indices=faces, positions=verts.astype(np.float32), normals=norms)
        mesh_material = gfx.MeshPhongMaterial(color="#BEBEBE", side="FRONT", shininess=10)

        # print("Adding mesh to canvas...")
        self.mesh = gfx.Mesh(mesh_geom, mesh_material)
        self.obj_scene.add(self.mesh)
        
        #group that will hold all the GCPs on object space
        self.obj_gcps_grp = gfx.Group()
        self.obj_scene.add(self.obj_gcps_grp)
        
        # print("Adding lights...")
        self.obj_scene.add(gfx.AmbientLight(intensity=1), gfx.DirectionalLight())
        self.obj_camera.show_object(self.obj_scene)
        
        self.min_xyz = min_xyz
        
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
    
    def get_gcps_from_gpkg(self):
        gcps = OrderedDict()
        gcp_data = {"obj_x":None, "obj_y":None, "obj_z":None, "img_x":None, "img_y":None, "img_dx":None, "img_dy":None, "active":None}
        
        for feat in self.img_gcps_lyr.getFeatures():
            curr_gcp = gcp_data.copy()
            img_gcp = json.loads(QgsJsonUtils.exportAttributes(feat))
            
            curr_gid = img_gcp["gid"]
            
            curr_gcp["img_x"] = img_gcp["img_x"]
            curr_gcp["img_y"] = img_gcp["img_y"]
            curr_gcp["img_dx"] = img_gcp["img_dx"]
            curr_gcp["img_dy"] = img_gcp["img_dy"]
            curr_gcp["active"] = img_gcp["active"]
            
            gcps[curr_gid] = curr_gcp
        
        for feat in self.map_gcps_lyr.getFeatures():
            map_gcp = json.loads(QgsJsonUtils.exportAttributes(feat))
            curr_gid = map_gcp["gid"]
            
            if curr_gid in gcps.keys():
                gcps[curr_gid]["obj_x"] = map_gcp["obj_x"]
                gcps[curr_gid]["obj_y"] = map_gcp["obj_y"]
                gcps[curr_gid]["obj_z"] = map_gcp["obj_z"]
            else:
                curr_gcp = gcp_data.copy()
                curr_gcp["obj_x"] = map_gcp["obj_x"]
                curr_gcp["obj_y"] = map_gcp["obj_y"]
                curr_gcp["obj_z"] = map_gcp["obj_z"]
                curr_gcp["active"] = map_gcp["active"]
                
                gcps[curr_gid] = curr_gcp

        return gcps
    
    def select_gcp(self, data):
        self.sel_gid = data["gid"]
        self.map_gcps_lyr.selectByExpression("\"gid\"=%s"%(data["gid"]))
        self.img_gcps_lyr.selectByExpression("\"gid\"=%s"%(data["gid"]))
        
        for pnts in self.obj_gcps_grp.children:
            if int(data["gid"]) == int(pnts.geometry.gid.data[0]):
                pnts.material = gfx.PointsMaterial(color=(1, 0.98, 0, 1), size=10)
            else:
                pnts.material = gfx.PointsMaterial(color=(0.78, 0, 0, 1), size=10)
        
        self.obj_canvas.request_draw(self.animate)
    
    def deselect_gcp(self):
        self.sel_gid = None
        self.map_gcps_lyr.removeSelection()
        self.img_gcps_lyr.removeSelection()

        for pnts in self.obj_gcps_grp.children:
            pnts.material = gfx.PointsMaterial(color=(0.78, 0, 0, 1), size=10)
        
        self.obj_canvas.request_draw(self.animate)
        
    def delete_gcp(self, data):
        if self.map_gcps_lyr.selectedFeatureCount() > 0:
            self.map_gcps_lyr.startEditing()
            self.map_gcps_lyr.deleteSelectedFeatures() 
            self.map_gcps_lyr.commitChanges()
        
        if self.img_gcps_lyr.selectedFeatureCount() > 0:
            self.img_gcps_lyr.startEditing()
            self.img_gcps_lyr.deleteSelectedFeatures()
            self.img_gcps_lyr.commitChanges()

        del_gcp_obj = None
        for gcp_obj in self.obj_gcps_grp.children:
            if int(data["gid"]) == int(gcp_obj.geometry.gid.data[0]):
                del_gcp_obj = gcp_obj
                
        if del_gcp_obj:
            self.obj_gcps_grp.remove(del_gcp_obj)
            self.obj_canvas.request_draw(self.animate)
            
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
            
            self.img_lyr = img_lyr
                
            # QgsProject.instance().addMapLayer(self.img_lyr, False) #False --> do not add layer to LayerTree --> not visible in qgis main canvas
            self.img_canvas.setExtent(self.img_lyr.extent())
            self.img_canvas.setLayers([self.img_gcps_lyr, self.img_line_lyr, self.img_lyr])
            self.img_canvas.refresh()
            
    def set_img_canvas_extent(self):
        self.img_canvas.setExtent(self.img_lyr.extent())
        self.img_canvas.refresh()
    
    def get_obj_canvas_camera(self):
        cam_state = self.obj_camera.get_state()
        print(cam_state)
        
        view_mat = self.obj_camera.view_matrix
        
        #opengl might be column order and not row ordre; hence, transpose
        rot_mat = view_mat[:3, :3].T
        #opengl coordinate systems is rotated by 180 degrees around x axis
        rot_mat = rot_mat@np.array([[1, 0, 0], 
                                    [0, np.cos(np.pi), -np.sin(np.pi)], 
                                    [0, np.sin(np.pi), np.cos(np.pi)]])
        print(rot_mat)
        
        #last column contains the negative position of the camera
        cam_pos = view_mat[:3, -1]*(-1)
        
        
        print(cam_pos)
        
        
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
        
        #remove all children from the group --> removes all prevously loaded GCPs
        self.obj_gcps_grp.clear()
        
        for feat in self.map_gcps_lyr.getFeatures():
            feat_pos = [feat["obj_x"]-self.min_xyz[0], 
                        feat["obj_y"]-self.min_xyz[1], 
                        feat["obj_z"]-self.min_xyz[2]]
            feat_gfx = create_point_3d(feat_pos, feat["gid"])
            self.obj_gcps_grp.add(feat_gfx)
        
        self.obj_canvas.request_draw(self.animate)
        
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

        #GCP picking in image space
        self.img_picker_tool = ImgPickerTool(self.img_canvas, GcpMetaDialog())
        self.img_picker_tool.set_camera(self.active_camera)
        self.img_picker_tool.set_layers(img_gcps_lyr=self.img_gcps_lyr, map_gcps_lyr=self.map_gcps_lyr)
        
        self.img_picker_tool.gcpAdded.connect(self.img_gcp_added)
        self.img_picker_tool.gcpUpdated.connect(self.img_gcp_updated)

        self.img_canvas.setMapTool(self.img_picker_tool)
        
        #GCP picking ib object space
        self.mesh.add_event_handler(self.mesh_picking, "click")

    def deactivate_gcp_picking(self):
        self.mesh.remove_event_handler(self.mesh_picking, "click")
        self.img_canvas.setMapTool(self.img_pan_tool)
        
    def img_gcp_added(self, data):
        self.dlg_orient.add_gcp_to_table(data, gcp_type="img_space")
    
    def img_gcp_updated(self, data):
        self.dlg_orient.update_selected_gcp(data, gcp_type="img_space")
    
    def mesh_picking(self, event):
            
        if event.button == 1 and "Control" in event.modifiers:
            face_ix = event.pick_info["face_index"]
            
            #face_coords are not normalized; hence, divide by their sum first before using the further
            face_coords = np.array(event.pick_info["face_coord"]).reshape(3, 1) 
            face_coords /= np.sum(face_coords)
            
            face_vertex_ix = event.pick_info["world_object"].geometry.indices.data[face_ix, :]
            face_vertex_pos = event.pick_info["world_object"].geometry.positions.data[face_vertex_ix, :]
            
            click_pos = np.sum(face_vertex_pos*face_coords, axis=0) 
            click_pos_global = click_pos + self.min_xyz
            
            feat_geom = QgsPoint(click_pos_global[0], click_pos_global[1])

            #TODO change feature attributes as well
            if self.map_gcps_lyr.selectedFeatureCount() > 0:
                sel_fid = self.map_gcps_lyr.selectedFeatureIds()[0]
                self.map_gcps_lyr.startEditing()
                self.map_gcps_lyr.changeGeometry(sel_fid, QgsGeometry.fromPoint(feat_geom))
                self.map_gcps_lyr.changeAttributeValue(sel_fid, self.map_gcps_lyr_obj_x_ix, float(click_pos_global[0]))
                self.map_gcps_lyr.changeAttributeValue(sel_fid, self.map_gcps_lyr_obj_y_ix, float(click_pos_global[1]))
                self.map_gcps_lyr.changeAttributeValue(sel_fid, self.map_gcps_lyr_obj_z_ix, float(click_pos_global[2]))
                self.map_gcps_lyr.commitChanges()
                
                for pnts in self.obj_gcps_grp.children:
                    if int(self.sel_gid) == int(pnts.geometry.gid.data[0]):
                        pnts.geometry.positions.data[0, :] = click_pos                                      #update point geometry position
                        pnts.geometry.positions.update_range(0)
                        pnts.children[0].local.position = pnts.geometry.positions.data[0, :] + [0, 0, 10]   #update position of label
                        break
                    
                self.obj_canvas.request_draw(self.animate)
                self.dlg_orient.update_selected_gcp({"obj_x":click_pos_global[0],
                                                     "obj_y":click_pos_global[1],
                                                     "obj_z":click_pos_global[2]}, gcp_type="obj_space")
            else:
                
                dlg_meta = GcpMetaDialog()
                
                img_gids = [feat.attributes()[self.img_gcps_gid_ix] for feat in self.img_gcps_lyr.getFeatures()]
                map_gids = [feat.attributes()[self.map_gcps_gid_ix] for feat in self.map_gcps_lyr.getFeatures()]
                pot_gids = list(set(img_gids).difference(map_gids))
                    
                dlg_meta.combo_gid.addItems(pot_gids)
                
                dlg_meta.line_iid.setText(self.active_camera.iid)
                
                dlg_meta.line_obj_x.setText("%.1f" % (click_pos_global[0]))
                dlg_meta.line_obj_y.setText("%.1f" % (click_pos_global[1]))
                dlg_meta.line_obj_z.setText("%.1f" % (click_pos_global[2]))
                
                dlg_meta.gids_not_allowed = map_gids
                
                result = dlg_meta.exec_() 

                if result:
                    
                    curr_gid = dlg_meta.combo_gid.currentText() 
                    
                    click_obj = create_point_3d(click_pos, curr_gid)
                    self.obj_gcps_grp.add(click_obj)
                    self.obj_canvas.request_draw(self.animate)
                    
                    self.dlg_orient.add_gcp_to_table({"obj_x":click_pos_global[0], 
                                                    "obj_y":click_pos_global[1],
                                                    "obj_z":click_pos_global[2],
                                                    "gid":curr_gid},
                                                    gcp_type="obj_space")
                    
                    feat = QgsFeature(self.map_gcps_lyr.fields())
                    
                    feat.setGeometry(QgsPoint(click_pos_global[0], click_pos_global[1]))
                    feat.setAttribute("iid", self.active_camera.iid)
                    feat.setAttribute("gid", dlg_meta.combo_gid.currentText())
                    feat.setAttribute("obj_x", float(click_pos_global[0]))
                    feat.setAttribute("obj_y", float(click_pos_global[1]))
                    feat.setAttribute("obj_z", float(click_pos_global[2]))
                    feat.setAttribute("desc", dlg_meta.line_desc.text())
                    feat.setAttribute("active", 0)
                    (res, afeat) = self.map_gcps_lyr.dataProvider().addFeatures([feat])
                    self.map_gcps_lyr.commitChanges()
                    
                    self.map_gcps_lyr.triggerRepaint()
                    # self.map_gcps_lyr.reload()
                    # self.map_canvas.refresh()