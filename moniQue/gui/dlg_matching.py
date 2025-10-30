from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QRadioButton, QButtonGroup, QPushButton
from PyQt5.QtGui import QIntValidator

class MatchingDialog(QDialog):
  
    def __init__(self):#, def_res, def_name):
        super(MatchingDialog, self).__init__()
        
        # setting window title
        self.setWindowTitle("Automatic feature point detection & matching")
  
        # setting geometry to the window
        self.setGeometry(1000, 500, 300, 250)
  
        cs1 = QRadioButton("Superpoint",self)
        cs1.setChecked(True)
        cs2 = QRadioButton("DISK",self)
        cs3 = QRadioButton("ALIKED",self)

        self.cs_group = QButtonGroup(self)
        self.cs_group.addButton(cs1)
        self.cs_group.addButton(cs2)
        self.cs_group.addButton(cs3)

        rb_layout = QHBoxLayout()
        rb_layout.addWidget(cs1)
        rb_layout.addWidget(cs2)
        rb_layout.addWidget(cs3)
        
        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(self.close)
        
        match_btn = QPushButton("Extract and match")
        match_btn.clicked.connect(self.extract_match)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(match_btn)
        btn_layout.addWidget(close_btn)
        
        dlg_layout = QVBoxLayout()
        dlg_layout.addLayout(rb_layout)
        dlg_layout.addLayout(btn_layout)
        self.setLayout(dlg_layout)
        
    def extract_match(self):
        
        import torch
        import numpy as np
        from skimage import io
        from skimage.transform import FundamentalMatrixTransform
        from skimage.measure import ransac
        from lightglue.utils import numpy_image_to_torch, rbd
        from lightglue import LightGlue, SuperPoint, DISK, ALIKED
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        extractor_type = self.cs_group.checkedButton().text()
        
        if extractor_type == "Superpoint":
            extractor = SuperPoint(max_num_keypoints=2048).eval().to(device)
            matcher = LightGlue(features='superpoint').eval().to(device)
        elif extractor_type == "DISK":
            extractor = DISK(max_num_keypoints=2048).eval().to(device)
            matcher = LightGlue(features='disk').eval().to(device)
        elif extractor_type == "ALIKED":
            extractor = ALIKED(max_num_keypoints=2048).eval().to(device)
            matcher = LightGlue(features='aliked').eval().to(device)
        
        print("Loading images...")
        hist_arr = io.imread(self.main_dlg.active_camera.path)
        print(np.shape(hist_arr))
        rend_arr = self.main_dlg.get_rendered_scene()
        print(np.shape(rend_arr))
        
        print("Converting to tensor...")
        hist_ten = numpy_image_to_torch(hist_arr).to(device)
        rend_ten = numpy_image_to_torch(rend_arr).to(device)
        
        print("Extracting features...")
        hist_feats = extractor.extract(hist_ten)
        rend_feats = extractor.extract(rend_ten)
        
        print("Finding matches...")
        raw_matches = matcher({'image0': hist_feats, 
                             'image1': rend_feats})
        hist_feats, rend_feats, raw_matches = [rbd(x) for x in [hist_feats, rend_feats, raw_matches]]  # remove batch dimension
        raw_matches = raw_matches['matches']  # indices with shape (K,2)        
        print(raw_matches)
        
        hist_pnts = hist_feats['keypoints'][raw_matches[..., 0]]  # coordinates in image #0, shape (K,2)
        rend_pnts = rend_feats['keypoints'][raw_matches[..., 1]]  # coordinates in image #1, shape (K,2)
        
        print("Geometrical verification...")
        # #https://scikit-image.org/docs/0.25.x/auto_examples/transform/plot_fundamental_matrix.html
        model, inliers = ransac((hist_pnts, rend_pnts),
                                FundamentalMatrixTransform,
                                min_samples=8,
                                residual_threshold=1,
                                max_trials=5000)    
        
        print(np.count_nonzero(inliers), np.count_nonzero(inliers)/len(inliers)*100)
        
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
