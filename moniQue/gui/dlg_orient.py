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

from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.gui import QgsProjectionSelectionWidget
from qgis.core import (
    Qgis,
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsVectorFileWriter,
)

import operator
from ..lsq import srs_lm

class OrientDialog(QtWidgets.QDialog):
    
    gcp_selected_signal = QtCore.pyqtSignal(object)
    gcp_deselected_signal = QtCore.pyqtSignal()
    gcp_delete_signal = QtCore.pyqtSignal(object)
    get_camera_signal = QtCore.pyqtSignal()
    
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
        
        self.parent = parent
        self.parent.img_list.setEnabled(False)
        self.parent.activate_gcp_picking()

        self.icon_dir = icon_dir

        self.setWindowTitle("%s - Camera parameter estimation" % (active_iid))
        self.resize(800, 400)
        self.setMinimumSize(QtCore.QSize(800, 400))
        self.setMaximumSize(QtCore.QSize(800, 400))
        
        params_toolbar = QtWidgets.QToolBar("")
        params_toolbar.setIconSize(QtCore.QSize(20, 20))
        
        table_toolbar = QtWidgets.QToolBar("")
        table_toolbar.setIconSize(QtCore.QSize(20, 20))
        
        self.btn_init_ori = QtWidgets.QAction("Set initial orientation from camera view.", self)
        self.btn_init_ori.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionMeasureBearing.png")))
        self.btn_init_ori.triggered.connect(self.get_camera_signal.emit)
        # self.btn_ori_tool.setCheckable(True)
        # self.btn_ori_tool.setEnabled(False)
        params_toolbar.addAction(self.btn_init_ori)

        self.btn_delete_gcp = QtWidgets.QAction("Delete selected GCP.", self)
        self.btn_delete_gcp.setIcon(QtGui.QIcon(os.path.join(self.icon_dir, "mActionDeleteSelectedFeatures.png")))
        self.btn_delete_gcp.triggered.connect(self.delete_selected_gcp)
        # self.btn_ori_tool.setCheckable(True)
        self.btn_delete_gcp.setEnabled(False)
        table_toolbar.addAction(self.btn_delete_gcp)

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
        self.table_gcps.horizontalHeader().resizeSection(1, 50)
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
            param_label.setMinimumSize(QtCore.QSize(25, 10))
            param_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            param_line = QtWidgets.QLineEdit()
            param_line.setMinimumSize(QtCore.QSize(125, 10))
            param_line.setReadOnly(True)
            unit_label = QtWidgets.QLabel(unit)
            unit_label.setMinimumSize(QtCore.QSize(25, 10))

            layout.addWidget(param_label)
            layout.addWidget(param_line)
            layout.addWidget(unit_label)

            return layout, param_line

        obj_x0_layout, obj_x0_line = create_cam_param_layout(param="X<sub>0</sub>: ", unit=" [m]")
        obj_y0_layout, obj_y0_line = create_cam_param_layout(param="Y<sub>0</sub>: ", unit=" [m]")
        obj_z0_layout, obj_z0_line = create_cam_param_layout(param="Z<sub>0</sub>: ", unit=" [m]")

        alpha_layout, alpha_line = create_cam_param_layout(param="\u03B1: ", unit=" [°]")
        zeta_layout, zeta_line = create_cam_param_layout(param="\u03B6: ", unit=" [°]")
        kappa_layout, kappa_line = create_cam_param_layout(param="\u03BA: ", unit=" [°]")

        focal_layout, focal_line = create_cam_param_layout(param="f: ", unit=" [px]")
        img_x0_layout, img_x0_line = create_cam_param_layout(param="x<sub>0</sub>: ", unit=" [px]")
        img_y0_layout, img_y0_line = create_cam_param_layout(param="y<sub>0</sub>: ", unit=" [px]")
        
        
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
        self.btn_calc_ori.clicked.connect(self.calc_orientation)
        
        self.btn_save_ori = QtWidgets.QPushButton("Save")
        self.btn_save_ori.setEnabled(False)
        
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
    
    def closeEvent(self, event):
        self.parent.img_list.setEnabled(True)
        self.parent.btn_ori_tool.setChecked(False)

        self.parent.deactivate_gcp_picking()

        # self.close_dialog_signal.emit()

        # gpkg_layout = QtWidgets.QHBoxLayout()
        # gpkg_label = QtWidgets.QLabel("GPKG Path")
        # self.gpkg_line = QtWidgets.QLineEdit()
        # self.gpkg_line.setEnabled(False)
        # self.gpkg_btn = QtWidgets.QPushButton()
        # self.gpkg_btn.clicked.connect(self.set_gpkg_path)
        
        # gpkg_layout.addWidget(gpkg_label)
        # gpkg_layout.addWidget(self.gpkg_line)
        # gpkg_layout.addWidget(self.gpkg_btn)

        # mesh_layout = QtWidgets.QHBoxLayout()
        # mesh_label = QtWidgets.QLabel("Mesh Path")
        # self.mesh_line = QtWidgets.QLineEdit()
        # self.mesh_line.setEnabled(False)
        # self.mesh_btn = QtWidgets.QPushButton()
        # self.mesh_btn.clicked.connect(self.set_mesh_path)

        # mesh_layout.addWidget(mesh_label)
        # mesh_layout.addWidget(self.mesh_line)
        # mesh_layout.addWidget(self.mesh_btn)
        
        # crs_layout = QtWidgets.QHBoxLayout()
        # crs_label = QtWidgets.QLabel("Project CRS")
        # self.crs_widget = QgsProjectionSelectionWidget()
        # self.crs_widget.crsChanged.connect(self.set_crs)

        # crs_layout.addWidget(crs_label)
        # crs_layout.addWidget(self.crs_widget)
        
        # btn_layout = QtWidgets.QHBoxLayout()
        # self.create_btn = QtWidgets.QPushButton("Create")
        # self.create_btn.setEnabled(False)
        # self.create_btn.clicked.connect(self.create_project)
        
        # btn_layout.addStretch(1)
        # btn_layout.addWidget(self.create_btn)
        
        # main_layout.addLayout(gpkg_layout)
        # main_layout.addLayout(mesh_layout)
        # main_layout.addLayout(crs_layout)
        # main_layout.addLayout(btn_layout)
        # main_layout.addStretch(1)
        # self.setLayout(main_layout)
    
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
            
            if data["active"] == 1:
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
    
    def calc_orientation(self):
        nr_rows = self.table_gcps.rowCount()
        
        ori_data = {"gid":[], 
                    "img":[], 
                    "obj":[], 
                    "init_params":{"obj_x0":None,
                                    "obj_y0":None,
                                    "obj_z0":None,
                                    "alpha":None,
                                    "zeta":None,
                                    "kappa":None,
                                    "f":None,
                                    "img_x0":None,
                                    "img_y0":None}}
        
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
                
                
        #TODO get initival values
        
        print(ori_data)
                