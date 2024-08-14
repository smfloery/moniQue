from PyQt5.QtWidgets import QDialog, QGroupBox, QLineEdit, QDialogButtonBox, QVBoxLayout, QFormLayout, QLabel, QComboBox, QErrorMessage, QFileDialog, QTextEdit
from PyQt5.QtGui import QIntValidator

class ImportAkonDialog(QDialog):
  
    def __init__(self):
        super(ImportAkonDialog, self).__init__()
        
        # setting window title
        self.setWindowTitle("Import image from AKON")
  
        # setting geometry to the window
        self.setGeometry(1000, 500, 300, 100)
  
        # creating a group box
        self.formGroupBox = QGroupBox()

        self.akon_id = QTextEdit()
        self.akon_id.setReadOnly(False)
        self.akon_id.setEnabled(True)
        self.akon_id.setPlaceholderText('AK123_456;AK654_321;...')
        
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

        self.error_dialog = QErrorMessage(parent=self)
        self.gids_not_allowed = None

        #self.ok = False
    
    #def accept(self):
    #    if len(self.akon_id.text()) == 9:
    #        self.ok = True
    #        super().accept()
    #    elif len(self.akon_id.text()) == 0:
    #        self.error_dialog.showMessage('Please select an AKON_ID!')
    #    else:
    #        self.error_dialog.showMessage('The AKON_ID consists of 9 characters (i.e. AK123_456)!')

        
            
        
    def createForm(self):
  
        # creating a form layout
        layout = QFormLayout()
  
        # adding rows
        # for name and adding input text
        layout.addRow(QLabel("AKON_ID: "), self.akon_id)
  
        # setting layout
        self.formGroupBox.setLayout(layout)
