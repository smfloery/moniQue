from PyQt5.QtWidgets import QDialog, QGroupBox, QLineEdit, QDialogButtonBox, QVBoxLayout, QFormLayout, QLabel, QComboBox

class GcpMetaDialog(QDialog):
  
    def __init__(self):
        super(GcpMetaDialog, self).__init__()
        
        # setting window title
        self.setWindowTitle("Set GCP attributes")
  
        # setting geometry to the window
        self.setGeometry(100, 100, 300, 400)
  
        # creating a group box
        self.formGroupBox = QGroupBox()
    
        self.line_iid = QLineEdit()
        self.line_iid.setReadOnly(True)
        self.line_iid.setEnabled(False)
        
        # self.line_gid = QLineEdit()
        # self.line_gid.setReadOnly(True)
        # self.line_gid.setEnabled(False)
        self.combo_gid = QComboBox()
        self.combo_gid.setEditable(True)
        self.combo_gid.setInsertPolicy(QComboBox.InsertAtTop)

        # creating a line edit
        self.line_img_x = QLineEdit()
        self.line_img_x.setReadOnly(True)
        self.line_img_x.setEnabled(False)
        
        self.line_img_y = QLineEdit()
        self.line_img_y.setReadOnly(True)
        self.line_img_y.setEnabled(False)
        
        self.line_obj_x = QLineEdit()
        self.line_obj_x.setReadOnly(True)
        self.line_obj_x.setEnabled(False)
        
        self.line_obj_y = QLineEdit()
        self.line_obj_y.setReadOnly(True)
        self.line_obj_y.setEnabled(False)
        
        self.line_obj_h = QLineEdit()
        self.line_obj_h.setReadOnly(True)
        self.line_obj_h.setEnabled(False)
                            
        # creating a line edit
        self.line_desc = QLineEdit()
        self.line_desc.setReadOnly(False)
        self.line_desc.setEnabled(True)
        
        # calling the method that create the form
        self.createForm()
  
        # creating a dialog button for ok and cancel
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)# | QDialogButtonBox.Cancel)
  
        # adding action when form is accepted
        self.buttonBox.accepted.connect(self.accept)
  
        # creating a vertical layout
        mainLayout = QVBoxLayout()
  
        # adding form group box to the layout
        mainLayout.addWidget(self.formGroupBox)
  
        # adding button box to the layout
        mainLayout.addWidget(self.buttonBox)
  
        # setting lay out
        self.setLayout(mainLayout)
    
    # def getMeta(self):
    #     return {"type":self.line_type.text(), "comment":self.line_comment.text()}
    
    # def clearFields(self):
    #     self.line_type.clear()
    #     self.line_comment.clear()
  
    def createForm(self):
  
        # creating a form layout
        layout = QFormLayout()
  
        # adding rows
        # for name and adding input text
        layout.addRow(QLabel("IID"), self.line_iid)
        # layout.addRow(QLabel("GID"), self.line_gid)
        layout.addRow(QLabel("GID"), self.combo_gid)
        layout.addRow(QLabel("x"), self.line_img_x)
        layout.addRow(QLabel("y"), self.line_img_y)
        layout.addRow(QLabel("X"), self.line_obj_x)
        layout.addRow(QLabel("Y"), self.line_obj_y)
        layout.addRow(QLabel("H"), self.line_obj_h)
        layout.addRow(QLabel("Desc"), self.line_desc)
  
        # setting layout
        self.formGroupBox.setLayout(layout)
  
    # def fillAttributes(self, camera):
    #     self.line_id.setText(camera.id)
    #     self.line_von.setText(camera.meta["von"])
    #     self.line_bis.setText(camera.meta["bis"])