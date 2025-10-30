from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QRadioButton, QButtonGroup, QPushButton, QFormLayout, QLabel, QLineEdit, QFileDialog
from qgis.PyQt import QtGui, QtCore
from PyQt5.QtGui import QDoubleValidator

import os

class OrthophotoDialog(QDialog):
  
    def __init__(self, main_dlg):
        super(OrthophotoDialog, self).__init__()
        
        # setting window title
        self.setWindowTitle("Generate an orthophoto")
  
        # setting geometry to the window
        self.setGeometry(1000, 500, 500, 150)

        self.main_dlg = main_dlg
        
        path_layout = QHBoxLayout()
        path_label = QLabel("Path:")
        path_label.setFixedWidth(100)
        self.path_line = QLineEdit()
        self.path_line.setEnabled(False)
        self.path_btn = QPushButton()
        self.path_btn.setIcon(QtGui.QIcon(os.path.join(self.main_dlg.icon_dir, "mActionFileOpen.png")))
        self.path_btn.clicked.connect(self.set_op_path)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_line)
        path_layout.addWidget(self.path_btn)
        
        res_validator = QDoubleValidator()
        res_validator.setRange(0.1, 9999.0, 2)
        res_validator.setLocale(QtCore.QLocale("en_US"))

        
        res_layout = QHBoxLayout()
        res_label = QLabel("Resolution [m]:")
        res_label.setFixedWidth(100)
        self.res_line = QLineEdit()
        self.res_line.setFixedWidth(50)
        self.res_line.setText("1.00")
        self.res_line.setValidator(res_validator)
        res_layout.addWidget(res_label)
        res_layout.addWidget(self.res_line)
        res_layout.addStretch()
        
        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(self.close)
        
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.generate_op)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(close_btn)
        
        dlg_layout = QVBoxLayout()
        dlg_layout.addLayout(path_layout)
        dlg_layout.addLayout(res_layout)
        dlg_layout.addStretch()
        dlg_layout.addLayout(btn_layout)
        self.setLayout(dlg_layout)
    
    def generate_op(self):
        op_path = self.path_line.text()
        
        if self.res_line.hasAcceptableInput():
            op_res = float(self.res_line.text())
            print(op_path, op_res)
    
    def set_op_path(self):
        op_path = QFileDialog.getSaveFileName(None, "OP path", "", ("Tif (*.tif)"))[0]
        
        if op_path:
            self.path_line.setText(op_path)

            if self.path_line.text() is not "":
                self.generate_btn.setEnabled(True)
    
    # def extract_match(self):
        
    #     import torch
    #     import numpy as np
    #     from skimage import io
    #     from skimage.transform import FundamentalMatrixTransform
    #     from skimage.measure import ransac
    #     from lightglue.utils import numpy_image_to_torch, rbd
    #     from lightglue import LightGlue, SuperPoint, DISK, ALIKED
        
    #     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    #     extractor_type = self.cs_group.checkedButton().text()
        
    #     if extractor_type == "Superpoint":
    #         extractor = SuperPoint(max_num_keypoints=2048).eval().to(device)
    #         matcher = LightGlue(features='superpoint').eval().to(device)
    #     elif extractor_type == "DISK":
    #         extractor = DISK(max_num_keypoints=2048).eval().to(device)
    #         matcher = LightGlue(features='disk').eval().to(device)
    #     elif extractor_type == "ALIKED":
    #         extractor = ALIKED(max_num_keypoints=2048).eval().to(device)
    #         matcher = LightGlue(features='aliked').eval().to(device)
        
    #     print("Loading images...")
    #     hist_arr = io.imread(self.main_dlg.active_camera.path)
    #     print(np.shape(hist_arr))
    #     rend_arr = self.main_dlg.get_rendered_scene()
    #     print(np.shape(rend_arr))
        
    #     print("Converting to tensor...")
    #     hist_ten = numpy_image_to_torch(hist_arr).to(device)
    #     rend_ten = numpy_image_to_torch(rend_arr).to(device)
        
    #     print("Extracting features...")
    #     hist_feats = extractor.extract(hist_ten)
    #     rend_feats = extractor.extract(rend_ten)
        
    #     print("Finding matches...")
    #     raw_matches = matcher({'image0': hist_feats, 
    #                          'image1': rend_feats})
    #     hist_feats, rend_feats, raw_matches = [rbd(x) for x in [hist_feats, rend_feats, raw_matches]]  # remove batch dimension
    #     raw_matches = raw_matches['matches']  # indices with shape (K,2)        
    #     print(raw_matches)
        
    #     hist_pnts = hist_feats['keypoints'][raw_matches[..., 0]]  # coordinates in image #0, shape (K,2)
    #     rend_pnts = rend_feats['keypoints'][raw_matches[..., 1]]  # coordinates in image #1, shape (K,2)
        
    #     print("Geometrical verification...")
    #     # #https://scikit-image.org/docs/0.25.x/auto_examples/transform/plot_fundamental_matrix.html
    #     model, inliers = ransac((hist_pnts, rend_pnts),
    #                             FundamentalMatrixTransform,
    #                             min_samples=8,
    #                             residual_threshold=1,
    #                             max_trials=5000)    
        
    #     print(np.count_nonzero(inliers), np.count_nonzero(inliers)/len(inliers)*100)
        
    def set_main_dlg(self, dlg):
        self.main_dlg = dlg
    
    # def accept(self):
    #     if len(self.file_name.text()) > 0:
    #         if self.res_width.hasAcceptableInput() and self.res_height.hasAcceptableInput():
    #             self.ok = True
    #             super().accept()
    #         else:
    #             self.error_dialog.showMessage('No valid Resolution has been given! Maximum Resolution: 7680x4320 ; Minimum Resolution: 1x1 ')
    #     else:
    #         self.error_dialog.showMessage('Please choose a file name!')
        
            
        
    # def createForm(self):
  
    #     # creating a form layout
    #     layout = QFormLayout()
  
    #     # adding rows
    #     # for name and adding input text
    #     layout.addRow(QLabel("File Name"), self.file_name)
    #     layout.addRow(QLabel("Width"), self.res_width)
    #     layout.addRow(QLabel("Height"), self.res_height)
    #     layout.addRow(QLabel("Depth Offset"), self.depth_offset)
  
    #     # setting layout
    #     self.formGroupBox.setLayout(layout)
