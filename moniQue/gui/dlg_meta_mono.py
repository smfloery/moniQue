from PyQt5.QtWidgets import QDialog, QGroupBox, QLineEdit, QDialogButtonBox, QVBoxLayout, QFormLayout, QLabel

class MonoMetaDialog(QDialog):
  
    def __init__(self):
        super(MonoMetaDialog, self).__init__()
        
        # setting window title
        self.setWindowTitle("Set monoplotting feature attributes.")
  
        # setting geometry to the window
        self.setGeometry(100, 100, 300, 400)
  
        # creating a group box
        self.formGroupBox = QGroupBox()
    
        self.line_iid = QLineEdit()
        self.line_iid.setReadOnly(True)
        self.line_iid.setEnabled(False)
        
        # creating a line edit
        self.line_type = QLineEdit()
        self.line_type.setReadOnly(False)
        self.line_type.setEnabled(True)
                            
        # creating a line edit
        self.line_comment = QLineEdit()
        self.line_comment.setReadOnly(False)
        self.line_comment.setEnabled(True)
        
        # calling the method that create the form
        self.createForm()
  
        # creating a dialog button for ok and cancel
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)# | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)

        # creating a vertical layout
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
    
    def getMeta(self):
        return {"type":self.line_type.text(), "comment":self.line_comment.text()}
    
    def clearFields(self):
        self.line_type.clear()
        self.line_comment.clear()
            
    def createForm(self):
  
        # creating a form layout
        layout = QFormLayout()
        layout.addRow(QLabel("IID"), self.line_iid)
        layout.addRow(QLabel("Type"), self.line_type)
        layout.addRow(QLabel("Comment"), self.line_comment)
  
        # setting layout
        self.formGroupBox.setLayout(layout)
  
    def fillAttributes(self, camera):
        self.line_iid.setText(camera.iid)