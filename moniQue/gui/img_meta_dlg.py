from PyQt5.QtWidgets import QDialog, QGroupBox, QLineEdit, QDialogButtonBox, QVBoxLayout, QFormLayout, QLabel

class MetaWindow(QDialog):
  
    def __init__(self):
        super(MetaWindow, self).__init__()
        
        # setting window title
        self.setWindowTitle("Set feature attribute")
  
        # setting geometry to the window
        self.setGeometry(100, 100, 300, 400)
  
        # creating a group box
        self.formGroupBox = QGroupBox()
    
        # creating a line edit
        self.line_id = QLineEdit()
        self.line_id.setReadOnly(True)
        self.line_id.setEnabled(False)
        
        # creating a line edit
        self.line_von = QLineEdit()
        self.line_von.setReadOnly(True)
        self.line_von.setEnabled(False)
        
        # creating a line edit
        self.line_bis = QLineEdit()
        self.line_bis.setReadOnly(True)
        self.line_bis.setEnabled(False)
          
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
    
    def getMeta(self):
        return {"type":self.line_type.text(), "comment":self.line_comment.text()}
    
    def clearFields(self):
        self.line_type.clear()
        self.line_comment.clear()
  
    def createForm(self):
  
        # creating a form layout
        layout = QFormLayout()
  
        # adding rows
        # for name and adding input text
        layout.addRow(QLabel("Image"), self.line_id)
        layout.addRow(QLabel("Von"), self.line_von)
        layout.addRow(QLabel("Bis"), self.line_bis)
        layout.addRow(QLabel("Type"), self.line_type)
        layout.addRow(QLabel("Comment"), self.line_comment)
  
        # setting layout
        self.formGroupBox.setLayout(layout)
  
    def fillAttributes(self, camera):
        self.line_id.setText(camera.id)
        self.line_von.setText(camera.meta["von"])
        self.line_bis.setText(camera.meta["bis"])