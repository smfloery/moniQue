# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MoniQue
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
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QApplication, QFileDialog

from qgis.core import QgsProject, QgsVectorLayer, QgsJsonUtils
from qgis.gui import QgsMapToolPan, QgsMessageBar

# # Initialize Qt resources from file resources.py
# from .resources import *
from .gui.dlg_main import MainDialog
from .gui.dlg_convert import ConvertDialog

import os.path
import json
import open3d as o3d
import numpy as np
import requests 
import xml.etree.ElementTree as ET

from .camera import Camera

class MoniQue:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.iface.actionMapTips().trigger()    #enable showing map tips
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        self.icon_dir = os.path.join(self.plugin_dir, "gfx", "icon")
        
        self.project_name = None
        
        #paths to the styling files
        self.cam_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "camera.qml")
        self.img_line_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "lines_img.qml")
        self.map_line_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "lines_map.qml")
        self.map_region_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "region_map.qml")
        self.map_gcps_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "gcps_map.qml")
        self.img_gcps_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "gcps_img.qml")
        
        #map_canvas is the canvas of the QGIS main window
        self.map_canvas = iface.mapCanvas()
        
        self.camera_collection = {}
        
        #set tools
        self.map_pan_tool = QgsMapToolPan(self.map_canvas)

        # Declare instance attributes
        self.actions = []
    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        launch_icon = QIcon(os.path.join(self.plugin_dir, "icon.png"))
        launch_action = QAction(launch_icon, 'Run moniQue...', self.iface.mainWindow())
        launch_action.triggered.connect(self.open_main_dlg)
        launch_action.setEnabled(True)
        
        convert_icon = QIcon(os.path.join(self.icon_dir, "mActionAddMeshLayer.png"))
        convert_action = QAction(convert_icon, "Convert DTM to mesh...", self.iface.mainWindow())
        convert_action.triggered.connect(self.open_convert_dlg)
        convert_action.setEnabled(True)
        
        self.iface.addPluginToMenu("moniQue", launch_action)
        self.iface.addPluginToMenu("moniQue", convert_action)
        
        self.iface.addToolBarIcon(launch_action)
        
        self.actions.append(launch_action)
        self.actions.append(convert_action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu('moniQue', action)
            self.iface.removeToolBarIcon(action)

    def on_load_project_signal(self, data):
        
        self.gpkg_path = data["gpkg_path"]
        self.project_name = os.path.basename(self.gpkg_path).rsplit(".")[0]
        
        QApplication.instance().setOverrideCursor(Qt.WaitCursor)
        
        self.reset_plugin()
        
        #load layers from geopackage
        gpkg_reg_lyr = self.gpkg_path + "|layername=region"
        self.reg_lyr = QgsVectorLayer(gpkg_reg_lyr, "region", "ogr")
        self.reg_lyr.loadNamedStyle(self.map_region_qml_path)
                
        gpkg_cam_lyr = self.gpkg_path + "|layername=cameras"
        self.cam_lyr = QgsVectorLayer(gpkg_cam_lyr, "cameras", "ogr")           
        self.cam_lyr.loadNamedStyle(self.cam_qml_path)
                        
        gpkg_map_lines_lyr = self.gpkg_path + "|layername=lines"
        self.map_line_lyr = QgsVectorLayer(gpkg_map_lines_lyr, "lines", "ogr")
        self.map_line_lyr.loadNamedStyle(self.map_line_qml_path)
       
        gpkg_img_lines_lyr = self.gpkg_path + "|layername=lines_img"
        self.img_line_lyr = QgsVectorLayer(gpkg_img_lines_lyr, "lines_img", "ogr")
        self.img_line_lyr.loadNamedStyle(self.img_line_qml_path)       

        gpkg_map_gcps_lyr = self.gpkg_path + "|layername=gcps"
        self.map_gcps_lyr = QgsVectorLayer(gpkg_map_gcps_lyr, "gcps", "ogr")
        self.map_gcps_lyr.loadNamedStyle(self.map_gcps_qml_path)       
        
        gpkg_img_gcps_lyr = self.gpkg_path + "|layername=gcps_img"
        self.img_gcps_lyr = QgsVectorLayer(gpkg_img_gcps_lyr, "gcps_img", "ogr")
        self.img_gcps_lyr.loadNamedStyle(self.img_gcps_qml_path)       
                    
        root = QgsProject.instance().layerTreeRoot()
        monoGroup = root.insertGroup(0, self.project_name)  
        monoGroup.addLayer(self.map_line_lyr) 
        monoGroup.addLayer(self.cam_lyr) 
        monoGroup.addLayer(self.reg_lyr)
        monoGroup.addLayer(self.map_gcps_lyr)

        expression = "iid = 'sth_not_existing'"
        self.img_line_lyr.setSubsetString(expression) #show only those lines which correspond to the currently selected image
        self.img_gcps_lyr.setSubsetString(expression)
        self.map_gcps_lyr.setSubsetString(expression)
        
        #define layers which should be shown/considered in which canvas
        self.map_canvas.setLayers([self.map_line_lyr, self.cam_lyr, self.reg_lyr, self.map_gcps_lyr])
        self.map_canvas.setExtent(self.reg_lyr.extent())
        self.map_canvas.refresh()
        
        self.dlg_main.setWindowTitle(self.project_name)
        self.crs = self.cam_lyr.crs()
        
        self.layer_collection = {"reg_lyr":self.reg_lyr,
                                 "cam_lyr":self.cam_lyr,
                                 "img_line_lyr":self.img_line_lyr,
                                 "img_gcps_lyr":self.img_gcps_lyr,
                                 "map_line_lyr":self.map_line_lyr,
                                 "map_gcps_lyr":self.map_gcps_lyr}
        
        self.dlg_main.set_layers(self.layer_collection)
        self.dlg_main.activate_gui_elements()
        
        self.load_mesh()        #commented to switch loading single mesh to tiles
        self.load_cameras_from_gpkg()
        
        QApplication.instance().restoreOverrideCursor()
    
    def load_cameras_from_gpkg(self):
        
        cam_feats = self.cam_lyr.getFeatures() 
        for feat in cam_feats:
            
            feat_json = json.loads(QgsJsonUtils.exportAttributes(feat))
            del feat_json["fid"]
            cam = Camera(**feat_json)

            self.camera_collection[cam.iid] = cam
            self.dlg_main.add_camera_to_list(cam)
    
    def load_mesh(self):
        
        reg_feat = list(self.reg_lyr.getFeatures())[0]
        json_path = reg_feat["json_path"]

        if not os.path.exists(json_path):
            json_path = QFileDialog.getOpenFileName(None, "Mesh not found! Select new directory to the Mesh", "", ("JSON (*.json)"))[0]
            field_idx = self.reg_lyr.fields().indexOf('json_path')
            self.reg_lyr.startEditing()
            self.reg_lyr.changeAttributeValue(1,field_idx,json_path)
            self.reg_lyr.commitChanges()
        
        with open(json_path, "r") as f:
            tiles_data = json.load(f)
            tiles_data["tile_dir"] = os.path.join(os.path.dirname(json_path), "mesh")
            tiles_data["op_dir"] = os.path.join(os.path.dirname(json_path), "op")
            
            mesh_lvls = []
            sd_names = next(os.walk(tiles_data["tile_dir"]))[1]
            for sd in sd_names:
                mesh_lvls.append(int(sd))
            mesh_lvls.sort(reverse=True)
            tiles_data["mesh_lvls"] = list(map(str, mesh_lvls))
            
            if os.path.exists(tiles_data["op_dir"]):
    
                op_lvls = []            
                sd_names = next(os.walk(tiles_data["op_dir"]))[1]
                for sd in sd_names:
                    if "mesh" in sd:
                        op_lvls.append(int(sd.split("_")[0]))
                op_lvls.sort(reverse=True)
                tiles_data["op_lvls"] = list(map(str, op_lvls))
            else:
                tiles_data["op_lvls"] = []
        
        print(tiles_data["mesh_lvls"])
        
        ##! WIE IN ZUKUNFT DIE RAYCASTING SCENE SETZEN?
        # self.ray_scene = scene
        self.dlg_main.add_mesh_to_obj_canvas(tiles_data)
        
    def reset_plugin(self):
        
        root = QgsProject.instance().layerTreeRoot()
        
        #project_name is only set if anything was loaded; 
        #if its not available than we don't have to do anything
        if self.project_name:
            monoGroup = root.findGroup(self.project_name)
            if monoGroup:
                root.removeChildNode(monoGroup)
            
            # # self.clear_highlighted_features()    
            
            self.map_canvas.refresh()            
            self.map_canvas.setMapTool(self.map_pan_tool)
            
            self.dlg_main.setWindowTitle("moniQue")
    
    def open_convert_dlg(self):
        self.dlg_convert = ConvertDialog(icon_dir=self.icon_dir, parent=self)
        self.dlg_convert.show()
    
    def open_main_dlg(self):
                
        self.dlg_main = MainDialog(plugin_dir=self.plugin_dir, parent=self)
        
        self.dlg_main.camera_collection = self.camera_collection
        self.dlg_main.load_project_signal.connect(self.on_load_project_signal)
        self.dlg_main.close_dialog_signal.connect(self.reset_plugin)
        
        self.dlg_main.show()

