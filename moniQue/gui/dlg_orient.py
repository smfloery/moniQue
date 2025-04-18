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
import open3d as o3d
import numpy as np
import pandas as pd

from qgis.PyQt import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt

import operator
from ..lsq import srs_lm
from ..helpers import calc_hfov, calc_vfov, alzeka2rot, alpha2azi, rot2alzeka
from .dlg_meta_offset import OffsetMetaDialog

import pygfx as gfx

class OrientDialog(QtWidgets.QDialog):
    
    gcp_selected_signal = QtCore.pyqtSignal(object)
    gcp_deselected_signal = QtCore.pyqtSignal()
    gcp_delete_signal = QtCore.pyqtSignal(object)
    gcp_imported_signal = QtCore.pyqtSignal(object)
    get_camera_signal = QtCore.pyqtSignal()
    camera_estimated_signal = QtCore.pyqtSignal(object)
    save_orientation_signal = QtCore.pyqtSignal()
    
    activate_mouse_projection_signal = QtCore.pyqtSignal()
    deactivate_mouse_projection_signal = QtCore.pyqtSignal()

    # offset_signal = QtCore.pyqtSignal(object)
    
    def __init__(self, parent=None, icon_dir=None, active_iid=None):
        """Constructor."""
        super(OrientDialog, self).__init__()

        self.name2ix = {"gid":1,
                        "X":2,
                        "Y":3,
                        "Z":4,
                        "x":5,
                        "y":6,
                        "dx":7,
                        "dy":8}
        
        self.prev_row = -1
        self.init_params = None
        
        self.parent = parent
        self.parent.img_list.setEnabled(False)
        self.parent.activate_gcp_picking()
        self.parent.orient_dlg_open = True
        self.parent.obj_canvas.setCursor(QCursor(Qt.CrossCursor))
        
        self.icon_dir = icon_dir

        self.setWindowTitle("%s - Camera parameter estimation" % (active_iid))
        self.resize(800, 400)
        self.setMinimumSize(QtCore.QSize(800, 400))
        self.setMaximumSize(QtCore.QSize(800, 400))
        
        params_toolbar = QtWidgets.QToolBar("")
        params_toolbar.setIconSize(QtCore.QSize(20, 20))
        
        table_toolbar = QtWidgets.QToolBar("")
        table_toolbar.setIconSize(QtCore.QSize(20, 20))
        
        self.btn_init_ori = QtWidgets.QAction("Set initial camera parameters from camera view.", self)
        self.btn_init_ori.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionMeasureBearing.png")))
        self.btn_init_ori.triggered.connect(self.get_camera_signal.emit)
        params_toolbar.addAction(self.btn_init_ori)

        self.btn_delete_gcp = QtWidgets.QAction("Delete selected GCP.", self)
        self.btn_delete_gcp.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionDeleteSelectedFeatures.png")))
        self.btn_delete_gcp.triggered.connect(self.delete_selected_gcp)
        self.btn_delete_gcp.setEnabled(False)
        table_toolbar.addAction(self.btn_delete_gcp)
        
        self.btn_import_gcps = QtWidgets.QAction("Import GCPs from *.csv", self)
        self.btn_import_gcps.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "import_gcp_from_file.png")))
        self.btn_import_gcps.triggered.connect(self.import_gcps_from_csv)
        table_toolbar.addAction(self.btn_import_gcps)
        
        self.btn_preview_pos = QtWidgets.QAction("Project 3D mouse position into the image.", self)
        self.btn_preview_pos.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "preview_pos.png")))
        self.btn_preview_pos.triggered.connect(self.project_mouse_position)
        self.btn_preview_pos.setEnabled(False)
        self.btn_preview_pos.setCheckable(True)
        table_toolbar.addAction(self.btn_preview_pos)

        self.btn_offset_dlg = QtWidgets.QAction("Displace camera along viewing direction.", self)
        self.btn_offset_dlg.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionElevationProfile.png")))
        self.btn_offset_dlg.triggered.connect(self.show_offset_dlg)
        table_toolbar.addAction(self.btn_offset_dlg)

        # self.offset = {'offset_x': 0.0, 
        #                'offset_y': 0.0, 
        #                'offset_z': 0.0}
    
        self.table_gcps = QtWidgets.QTableWidget()
        
        self.table_gcps.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.table_gcps.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_gcps.setAlternatingRowColors(True)
        self.table_gcps.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table_gcps.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_gcps.setObjectName("table_gcps")
        self.table_gcps.setColumnCount(9)
        self.table_gcps.setRowCount(0)
        
        self.table_gcps.cellClicked.connect(self.gcp_selected)
        self.table_gcps.itemChanged.connect(self.gcp_status_changed)
        
        self.table_gcps.horizontalHeader().setHighlightSections(True)
        self.table_gcps.horizontalHeader().resizeSection(0, 10)
        self.table_gcps.horizontalHeader().resizeSection(1, 30)
        self.table_gcps.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table_gcps.horizontalHeader().resizeSection(2, 80)
        self.table_gcps.horizontalHeader().resizeSection(3, 80)
        self.table_gcps.horizontalHeader().resizeSection(4, 80)
        self.table_gcps.horizontalHeader().resizeSection(5, 70)
        self.table_gcps.horizontalHeader().resizeSection(6, 70)
        self.table_gcps.horizontalHeader().resizeSection(7, 60)
        self.table_gcps.horizontalHeader().resizeSection(8, 60)

        self.table_gcps.verticalHeader().setVisible(False)
        
        self.table_gcps.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.table_gcps.setHorizontalHeaderLabels(["use", "gid", "X", "Y", "Z", "x", "y", "dx", "dy"])

        params_layout = QtWidgets.QVBoxLayout()
        
        params_layout.setSpacing(3)
    
        def create_cam_param_layout(param=None, label_size=25, line_size=125, unit=None):

            layout = QtWidgets.QHBoxLayout()
            param_label = QtWidgets.QLabel(param)
            param_label.setFixedWidth(25)
            param_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            param_line = QtWidgets.QLineEdit()
            param_line.setMinimumWidth(100)
            param_line.setReadOnly(True)
            param_line.setToolTip("Estimated parameter")

            param_std_line = QtWidgets.QLineEdit()
            param_std_line.setFixedWidth(50)
            param_std_line.setToolTip("Standard deviation")
            
            unit_label = QtWidgets.QLabel(unit)
            unit_label.setFixedWidth(25)

            layout.addWidget(param_label)
            layout.addWidget(param_line)
            layout.addWidget(param_std_line)
            layout.addWidget(unit_label)

            return layout, param_line, param_std_line

        obj_x0_layout, obj_x0_line, obj_x0_std_line = create_cam_param_layout(param="X<sub>0</sub>: ", unit=" [m]")
        obj_y0_layout, obj_y0_line, obj_y0_std_line = create_cam_param_layout(param="Y<sub>0</sub>: ", unit=" [m]")
        obj_z0_layout, obj_z0_line, obj_z0_std_line = create_cam_param_layout(param="Z<sub>0</sub>: ", unit=" [m]")

        self.obj_x0_line = obj_x0_line
        self.obj_x0_std_line = obj_x0_std_line
        
        self.obj_y0_line = obj_y0_line
        self.obj_y0_std_line = obj_y0_std_line
        
        self.obj_z0_line = obj_z0_line
        self.obj_z0_std_line = obj_z0_std_line
                
        alpha_layout, alpha_line, alpha_std_line = create_cam_param_layout(param="\u03B1: ", unit=" [°]")
        zeta_layout, zeta_line, zeta_std_line = create_cam_param_layout(param="\u03B6: ", unit=" [°]")
        kappa_layout, kappa_line, kappa_std_line = create_cam_param_layout(param="\u03BA: ", unit=" [°]")

        self.alpha_line = alpha_line
        self.alpha_std_line = alpha_std_line
        
        self.zeta_line = zeta_line
        self.zeta_std_line = zeta_std_line
        
        self.kappa_line = kappa_line
        self.kappa_std_line = kappa_std_line
        
        focal_layout, focal_line, focal_std_line = create_cam_param_layout(param="f: ", unit=" [px]")      
        img_x0_layout, img_x0_line, img_x0_std_line = create_cam_param_layout(param="x<sub>0</sub>: ", unit=" [px]")
        img_y0_layout, img_y0_line, img_y0_std_line = create_cam_param_layout(param="y<sub>0</sub>: ", unit=" [px]")
        
        self.focal_line = focal_line
        self.focal_std_line = focal_std_line
        
        self.img_x0_line = img_x0_line
        self.img_x0_std_line = img_x0_std_line
        
        self.img_y0_line = img_y0_line
        self.img_y0_std_line = img_y0_std_line
        
        params_layout.addWidget(params_toolbar)
        
        params_layout.addLayout(obj_x0_layout)
        params_layout.addLayout(obj_y0_layout)
        params_layout.addLayout(obj_z0_layout)
        
        params_layout.addLayout(alpha_layout)
        params_layout.addLayout(zeta_layout)
        params_layout.addLayout(kappa_layout)

        params_layout.addLayout(focal_layout)
        params_layout.addLayout(img_x0_layout)
        params_layout.addLayout(img_y0_layout)

        params_layout.addStretch()
        
        self.btn_calc_ori = QtWidgets.QPushButton("Calculate")
        self.btn_calc_ori.setEnabled(False)
        self.btn_calc_ori.clicked.connect(lambda: self.calc_orientation(self.offset))
        
        self.btn_save_ori = QtWidgets.QPushButton("Save")
        self.btn_save_ori.setEnabled(False)
        self.btn_save_ori.clicked.connect(self.save_orientation)
        
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setContentsMargins(5, 0, 0, 0)
        btn_layout.addWidget(self.btn_calc_ori)
        btn_layout.addWidget(self.btn_save_ori)

        params_layout.addLayout(btn_layout)

        self.table_layout = QtWidgets.QVBoxLayout()
        self.table_layout.addWidget(table_toolbar)
        self.table_layout.addWidget(self.table_gcps)
        
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(5, 0, 5, 0)
        main_layout.addLayout(self.table_layout)
        main_layout.addLayout(params_layout)

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 5)
        # layout.addWidget(self.main_toolbar)
        layout.addLayout(main_layout)
        self.setLayout(layout)

        self.error_dialog = QtWidgets.QErrorMessage(parent=self)

        self.offset = None
        
    def gcp_selected(self, rix, cix):
        
        if cix != 0:
    
            #row was already selected; hence only deselect
            if rix == self.prev_row:
                self.btn_delete_gcp.setEnabled(False)
                self.table_gcps.clearSelection()
                self.prev_row = -1
                self.gcp_deselected_signal.emit()

            else:
                self.btn_delete_gcp.setEnabled(True)
                self.table_gcps.setCurrentCell(rix, cix)
                self.prev_row = rix

                self.sel_gid = self.table_gcps.item(rix, 1).text()
                self.gcp_selected_signal.emit({"gid":self.sel_gid})
    
    def gcp_status_changed(self, item):
        active_gcps = 0
        
        if item.column() == 0:
            nr_rows = self.table_gcps.rowCount()
                    
            for rix in range(nr_rows):
                if self.table_gcps.item(rix, 0).checkState() == QtCore.Qt.Checked:
                    active_gcps += 1
    
            if active_gcps >= 4:
                self.btn_calc_ori.setEnabled(True)
            else:
                self.btn_calc_ori.setEnabled(False)
    
    def import_gcps_from_csv(self):
        csv_path = QtWidgets.QFileDialog.getOpenFileName(None, "Load *.csv", "", ("GCPs (*.csv)"))[0]
        
        if csv_path:
            pd_csv = pd.read_csv(csv_path, sep=";", encoding="utf-8")
            
            cols = list(pd_csv.columns)
            
            if cols != ["gid", "img_x", "img_y", "obj_x", "obj_y", "obj_z"]:
                print("Provided .csv does not match the required format!")            
            else:
                gcps = pd_csv.to_dict(orient='records')
                
                for gcp in gcps:
                    self.add_gcp_to_table(gcp)
                    self.gcp_imported_signal.emit(gcp)
        
    def delete_selected_gcp(self):
        self.gcp_delete_signal.emit({"gid":self.sel_gid})
        
        self.table_gcps.removeRow(self.prev_row)
        self.table_gcps.clearSelection()
        self.prev_row = -1
        self.btn_delete_gcp.setEnabled(False)
        
        #if GCP is deleted the number of active GCPS might have changed;
        active_gcps = 0
        nr_rows = self.table_gcps.rowCount()
        for rix in range(nr_rows):
            if self.table_gcps.item(rix, 0).checkState() == QtCore.Qt.Checked:
                active_gcps += 1
    
        if active_gcps >= 4:
            self.btn_calc_ori.setEnabled(True)
        else:
            self.btn_calc_ori.setEnabled(False)
    
    def add_gcp_to_table(self, data, gcp_type=None):
        
        nr_rows = self.table_gcps.rowCount()
        nr_cols = self.table_gcps.columnCount()
        
        gcp_exists = False
                
        for rix in range(nr_rows):
            if self.table_gcps.item(rix, 1).text() == data["gid"]:
                
                if gcp_type == "obj_space":
                    self.table_gcps.setItem(rix, self.name2ix["X"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_x"])))
                    self.table_gcps.setItem(rix, self.name2ix["Y"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_y"])))
                    self.table_gcps.setItem(rix, self.name2ix["Z"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_z"])))
                
                elif gcp_type == "img_space":
                    self.table_gcps.setItem(rix, self.name2ix["x"], QtWidgets.QTableWidgetItem("%.1f" % (data["img_x"])))
                    self.table_gcps.setItem(rix, self.name2ix["y"], QtWidgets.QTableWidgetItem("%.1f" % (data["img_y"])))
                
                self.table_gcps.item(rix, 0).setCheckState(QtCore.Qt.Checked)
                self.table_gcps.item(rix, 0).setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)

                gcp_exists = True
                
                break
            
        if not gcp_exists:
            self.table_gcps.insertRow(nr_rows)
            self.table_gcps.setRowHeight(nr_rows, 25)

            chkBoxItem = QtWidgets.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable)# | Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
                        
            self.table_gcps.setItem(nr_rows, 0, chkBoxItem)
            self.table_gcps.setItem(nr_rows, self.name2ix["gid"], QtWidgets.QTableWidgetItem(str(data["gid"])))

            if gcp_type == "obj_space":
                self.table_gcps.setItem(nr_rows, self.name2ix["X"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_x"])))
                self.table_gcps.setItem(nr_rows, self.name2ix["Y"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_y"])))
                self.table_gcps.setItem(nr_rows, self.name2ix["Z"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_z"])))
            elif gcp_type == "img_space":
                self.table_gcps.setItem(nr_rows, self.name2ix["x"], QtWidgets.QTableWidgetItem("%.1f" % (data["img_x"])))
                self.table_gcps.setItem(nr_rows, self.name2ix["y"], QtWidgets.QTableWidgetItem("%.1f" % (data["img_y"])))
            else:
                self.table_gcps.setItem(nr_rows, self.name2ix["x"], QtWidgets.QTableWidgetItem("%.1f" % (data["img_x"])))
                self.table_gcps.setItem(nr_rows, self.name2ix["y"], QtWidgets.QTableWidgetItem("%.1f" % (data["img_y"])))
                self.table_gcps.setItem(nr_rows, self.name2ix["X"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_x"])))
                self.table_gcps.setItem(nr_rows, self.name2ix["Y"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_y"])))
                self.table_gcps.setItem(nr_rows, self.name2ix["Z"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_z"])))
                
                self.table_gcps.item(nr_rows, 0).setCheckState(QtCore.Qt.Checked)
                self.table_gcps.item(nr_rows, 0).setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                
    def add_gcps_from_lyr(self, gcps):
        
        self.active_gcps = 0
        
        nr_gcps = len(gcps)
        
        for rx, (gid, data) in enumerate(gcps.items()):
            
            nr_none_attr = operator.countOf(data.values(), None)
            
            self.table_gcps.insertRow(rx)
            self.table_gcps.setRowHeight(rx, 25)

            chkBoxItem = QtWidgets.QTableWidgetItem()
            flags = chkBoxItem.flags()
            flags |= QtCore.Qt.ItemIsUserCheckable
            
            if nr_none_attr > 2:
                flags &= ~QtCore.Qt.ItemIsEnabled
                        
            chkBoxItem.setFlags(flags)
            
            if data["active"] == "1":
                chkBoxItem.setCheckState(QtCore.Qt.Checked)
            else:
                chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            
            self.table_gcps.setItem(rx, 0, chkBoxItem)    
            self.table_gcps.setItem(rx, self.name2ix["gid"], QtWidgets.QTableWidgetItem(gid))
            if data["obj_x"]:
                self.table_gcps.setItem(rx, self.name2ix["X"], QtWidgets.QTableWidgetItem("%.1f" % data["obj_x"]))
            
            if data["obj_y"]:
                self.table_gcps.setItem(rx, self.name2ix["Y"], QtWidgets.QTableWidgetItem("%.1f" % data["obj_y"]))
            
            if data["obj_z"]:
                self.table_gcps.setItem(rx, self.name2ix["Z"], QtWidgets.QTableWidgetItem("%.1f" % data["obj_z"]))
            
            if data["img_x"]:
                self.table_gcps.setItem(rx, self.name2ix["x"], QtWidgets.QTableWidgetItem("%.1f" % data["img_x"]))
            
            if data["img_y"]:                                        
                self.table_gcps.setItem(rx, self.name2ix["y"], QtWidgets.QTableWidgetItem("%.1f" % data["img_y"]))
            
            if data["img_dx"]:
                self.table_gcps.setItem(rx, self.name2ix["dx"], QtWidgets.QTableWidgetItem("%.1f" % data["img_dx"]))
            
            if data["img_dy"]:
                self.table_gcps.setItem(rx, self.name2ix["dy"], QtWidgets.QTableWidgetItem("%.1f" % data["img_dy"]))
    
    def update_selected_gcp(self, data, gcp_type=None):
        if gcp_type == "img_space":
            self.table_gcps.setItem(self.table_gcps.currentRow(), self.name2ix["x"], QtWidgets.QTableWidgetItem("%.1f" % (data["img_x"])))
            self.table_gcps.setItem(self.table_gcps.currentRow(), self.name2ix["y"], QtWidgets.QTableWidgetItem("%.1f" % (data["img_y"])))
        elif gcp_type == "obj_space":
            self.table_gcps.setItem(self.table_gcps.currentRow(), self.name2ix["X"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_x"])))
            self.table_gcps.setItem(self.table_gcps.currentRow(), self.name2ix["Y"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_y"])))
            self.table_gcps.setItem(self.table_gcps.currentRow(), self.name2ix["Z"], QtWidgets.QTableWidgetItem("%.1f" % (data["obj_z"])))
    
    def set_init_params(self, data):
        self.obj_x0_line.setText("%.1f" % (data["obj_x0"]))
        self.obj_y0_line.setText("%.1f" % (data["obj_y0"]))
        self.obj_z0_line.setText("%.1f" % (data["obj_z0"]))
        
        #display euler angles in degrees; but in data array its still in radiant
        self.alpha_line.setText("%.3f" % (np.rad2deg(data["alpha"])))
        self.zeta_line.setText("%.3f" % (np.rad2deg(data["zeta"])))
        self.kappa_line.setText("%.3f" % (np.rad2deg(data["kappa"])))
        
        self.img_x0_line.setText("%.1f" % (data["img_x0"]))
        self.img_y0_line.setText("%.1f" % (data["img_y0"]))
        self.focal_line.setText("%.1f" % (data["f"]))
                
        if "obj_x0_std" in list(data.keys()):
            if data["obj_x0_std"] is not None:
                self.obj_x0_std_line.setText("%.1f" % (data["obj_x0_std"]))
            else:
                self.obj_x0_std_line.setText("")    
        else:
            self.obj_x0_std_line.setText("")
        
        if "obj_y0_std" in list(data.keys()):
            if data["obj_y0_std"] is not None:
                self.obj_y0_std_line.setText("%.1f" % (data["obj_y0_std"]))
            else:
                self.obj_y0_std_line.setText("")    
        else:
            self.obj_y0_std_line.setText("")
        
        if "obj_z0_std" in list(data.keys()):
            if data["obj_z0_std"] is not None:
                self.obj_z0_std_line.setText("%.1f" % (data["obj_z0_std"]))
            else:
                self.obj_z0_std_line.setText("")    
        else:
            self.obj_z0_std_line.setText("")
        
        if "alpha_std" in list(data.keys()):
            if data["alpha_std"] is not None:
                self.alpha_std_line.setText("%.3f" % (np.rad2deg(data["alpha_std"])))
            else:
                self.alpha_std_line.setText("")    
        else:
            self.alpha_std_line.setText("")
        
        if "zeta_std" in list(data.keys()):
            if data["zeta_std"] is not None:
                self.zeta_std_line.setText("%.3f" % (np.rad2deg(data["zeta_std"])))
            else:
                self.zeta_std_line.setText("")    
        else:
            self.zeta_std_line.setText("")
        
        if "kappa_std" in list(data.keys()):
            if data["kappa_std"] is not None:
                self.kappa_std_line.setText("%.3f" % (np.rad2deg(data["kappa_std"])))
            else:
                self.kappa_std_line.setText("")    
        else:
            self.kappa_std_line.setText("")
        
        if "f_std" in list(data.keys()):
            if data["f_std"] is not None:
                self.focal_std_line.setText("%.1f" % (data["f_std"]))
            else:
                self.focal_std_line.setText("")    
        else:
            self.focal_std_line.setText("")
                
        self.init_params = data.copy()
    
    def set_residuals(self, data):
        
        used_gids = list(data["residuals"].keys())
        
        nr_rows = self.table_gcps.rowCount()
                
        for rix in range(nr_rows):
            
            curr_gid = self.table_gcps.item(rix,1).text()
            
            if curr_gid in used_gids:
                self.table_gcps.setItem(rix, self.name2ix["dx"], QtWidgets.QTableWidgetItem("%.1f" % (data["residuals"][curr_gid][0])))
                self.table_gcps.setItem(rix, self.name2ix["dy"], QtWidgets.QTableWidgetItem("%.1f" % (data["residuals"][curr_gid][1])))
            else:
                self.table_gcps.setItem(rix, self.name2ix["dx"], QtWidgets.QTableWidgetItem(""))
                self.table_gcps.setItem(rix, self.name2ix["dy"], QtWidgets.QTableWidgetItem(""))
             
    def calc_orientation(self, curr_offset):
               
        if not self.init_params:
            self.error_dialog.showMessage('Set initial camera parameters first!')
        else:
            ori_data = {"gid":[], "img":[], "obj":[], "init_params":None}
            
            nr_rows = self.table_gcps.rowCount()
            for rix in range(nr_rows):
                if self.table_gcps.item(rix, 0).checkState() == QtCore.Qt.Checked:
                    curr_gid = self.table_gcps.item(rix, self.name2ix["gid"]).text()
                    curr_obj_x = float(self.table_gcps.item(rix, self.name2ix["X"]).text())
                    curr_obj_y = float(self.table_gcps.item(rix, self.name2ix["Y"]).text())
                    curr_obj_z = float(self.table_gcps.item(rix, self.name2ix["Z"]).text()) 
                    curr_img_x = float(self.table_gcps.item(rix, self.name2ix["x"]).text())
                    curr_img_y = float(self.table_gcps.item(rix, self.name2ix["y"]).text())
                    
                    ori_data["gid"].append(curr_gid)
                    ori_data["img"].append([curr_img_x, curr_img_y])
                    ori_data["obj"].append([curr_obj_x, curr_obj_y, curr_obj_z])

            ori_data["init_params"] = self.init_params
 
            res = srs_lm(ori_data, offset=curr_offset)
                        
            if res.success == False:
                self.error_dialog.showMessage('LSQ did not converge: %s' % (res.message))
            else:
                est_obj_x0 = res.params["obj_x0"].value
                est_obj_y0 = res.params["obj_y0"].value
                est_obj_z0 = res.params["obj_z0"].value 
                est_alpha = res.params["alpha"].value
                est_zeta = res.params["zeta"].value
                est_kappa = res.params["kappa"].value
                est_focal = res.params["f"].value
                
                alzekas = rot2alzeka(alzeka2rot([est_alpha, est_zeta, est_kappa]))
                                                
                est_azi = alpha2azi(alzekas[0, 0])
                est_azi_inv = alpha2azi(alzekas[1, 0])
                
                #for north clockwise: atan2(x,y); for east-counterclockwise: atan2(y,x)
                prc2gcp_azi = np.arctan2(np.array(ori_data["obj"])[:, 0] - est_obj_x0, 
                                         np.array(ori_data["obj"])[:, 1] - est_obj_y0)
                prc2gcp_azi = (prc2gcp_azi + 2*np.pi) % (2*np.pi) #map atan2 to 0-360
                                
                if np.abs(prc2gcp_azi[0] - est_azi_inv) < np.abs(prc2gcp_azi[0] - est_azi):
                    est_alpha = alzekas[1, 0]
                    est_zeta = alzekas[1, 1]
                    est_kappa = alzekas[1, 2]
                    
                cxx = res.covar
                
                cxx_std = np.sqrt(np.diag(cxx))
                cxx_names = ["%s_std" % (name) for name in res.var_names]
                cxx_dict = dict(zip(cxx_names, cxx_std.tolist()))
                
                gcp_residuals = res.residual.reshape(-1, 2)
                gcp_gids = ori_data["gid"]
                
                gcp_dict = {"residuals": dict(zip(gcp_gids, gcp_residuals.tolist()))}
                
                est_data = {"obj_x0":est_obj_x0,
                            "obj_y0":est_obj_y0,
                            "obj_z0":est_obj_z0,
                            "alpha":est_alpha,
                            "zeta":est_zeta,
                            "kappa":est_kappa,
                            "img_x0":self.init_params["img_x0"],
                            "img_y0":self.init_params["img_y0"],
                            "f":est_focal}
                est_data = {**est_data, **cxx_dict}
                est_data = {**est_data, **gcp_dict}

                self.camera_estimated_signal.emit(est_data)
                self.set_init_params(est_data)
                self.set_residuals(est_data)
                self.btn_save_ori.setEnabled(True)

    def save_orientation(self):
        self.btn_preview_pos.setEnabled(True)
        self.save_orientation_signal.emit()
    
    def project_mouse_position(self):
        if self.btn_preview_pos.isChecked():    #activate
            self.activate_mouse_projection_signal.emit()
        else:
            self.deactivate_mouse_projection_signal.emit()
    
    def closeEvent(self, event):
        self.btn_preview_pos.setChecked(False)
        self.btn_preview_pos.setEnabled(False)
        
        #only activate image list if image is not rendered in 3D
        if not self.parent.btn_obj_canvas_show_img.isChecked():
            self.parent.img_list.setEnabled(True)
            
        self.parent.btn_ori_tool.setChecked(False)
        
        self.parent.untoggle_project_mouse_pos()
        self.parent.deactivate_gcp_picking()
        
        self.parent.obj_canvas.setCursor(QCursor(Qt.ArrowCursor))
        
        self.parent.discard_changes()
        self.parent.orient_dlg_open = False
        
        if self.parent.active_camera.is_oriented == 1:
            self.parent.btn_mono_tool.setEnabled(True)
            self.parent.btn_mono_select.setEnabled(True)
            self.parent.btn_mono_vertex.setEnabled(True)
        
    def show_offset_dlg(self):
        # self.offset = None
        # self.first_time = True
        
        temp_cam = self.parent.temporary_camera
        
        if temp_cam is not None:
        
            prc = np.array([float(temp_cam["obj_x0"]), float(temp_cam["obj_y0"]), float(temp_cam["obj_z0"])]) - self.parent.min_xyz
            rmat = alzeka2rot([float(temp_cam["alpha"]), float(temp_cam["zeta"]), float(temp_cam["kappa"])])
            cmat = np.array([[1, 0, -float(temp_cam["img_x0"])], 
                                [0, 1, -float(temp_cam["img_y0"])],
                                [0, 0, -float(temp_cam["f"])]])
                
            plane_pnts_img = np.array([[temp_cam["img_x0"], temp_cam["img_y0"], 1]]).T
            plane_pnts_dir = (rmat@cmat@plane_pnts_img).T
            plane_pnts_dir = plane_pnts_dir / np.linalg.norm(plane_pnts_dir, axis=1).reshape(-1, 1)

            ray_offset = np.arange(250, -250, -1).reshape(-1, 1)
            pnts_along_ray = prc + ray_offset*plane_pnts_dir
            pnts_along_ray_o3d = o3d.core.Tensor(pnts_along_ray, dtype=o3d.core.Dtype.Float32)
            dist2mesh = self.parent.o3d_scene.compute_signed_distance(pnts_along_ray_o3d)
            pnts_profile = pnts_along_ray[:, 2] - dist2mesh.numpy()
            
            offset_dlg = OffsetMetaDialog()
            offset_dlg.plot_data({"offset":ray_offset.ravel(), "profile":pnts_profile, "prc":prc, "ray_dir":plane_pnts_dir})
            offset_dlg.offset_selected_signal.connect(self.re_estimate_camera)
            offset_dlg.exec_()

    def re_estimate_camera(self, offset_dict):
        offset_dict["offset_prc"] += self.parent.min_xyz
        self.calc_orientation(curr_offset=offset_dict)
        
    
    # def show_offset(self, preview_offset, accepted):
    #     forward, right, up, alpha = self.calc_offset(preview_offset)

    #     #this assumes that the camera is exactly horizontal?! Better: use the direction vectors
    #     self.preview_offset = {'offset_x': forward * np.cos(alpha) + right * np.cos(alpha - (np.pi/2)), 
    #                            'offset_y': forward * np.sin(alpha) + right * np.sin(alpha - (np.pi/2)), 
    #                            'offset_z': up}
        
    #     self.offset_signal.emit(self.preview_offset)
    #     self.first_time = False

    #     if accepted:
    #         self.offset = self.preview_offset

    # def calc_offset(self, offset):
    #     forward = float(offset[0]) if offset[0] != '' else 0.0
    #     right = float(offset[1]) if offset[1] != '' else 0.0
    #     up = float(offset[2]) if offset[2] != '' else 0.0
    #     alpha = self.init_params['alpha']

    #     return forward, right, up, alpha

        




