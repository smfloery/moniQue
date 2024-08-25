from PyQt5.QtWidgets import QDialog, QGroupBox, QLineEdit, QDialogButtonBox, QVBoxLayout, QFormLayout, QLabel, QComboBox, QErrorMessage, QFileDialog
from PyQt5.QtGui import QIntValidator

class ExportMetaDialog(QDialog):
  
    def __init__(self, def_res, def_name):
        super(ExportMetaDialog, self).__init__()
        
        # setting window title
        self.setWindowTitle("Export Object View as PNG")
  
        # setting geometry to the window
        self.setGeometry(1000, 500, 300, 250)
  
        # creating a group box
        self.formGroupBox = QGroupBox()

        self.file_name = QLineEdit()
        self.file_name.setReadOnly(False)
        self.file_name.setEnabled(True)
        self.file_name.setText(def_name)
        self.file_name.setPlaceholderText('myRendering')
        
        self.res_width = QLineEdit()
        self.res_width.setReadOnly(False)
        self.res_width.setEnabled(True)
        self.res_width.setText(def_res[0])
        self.res_width.setPlaceholderText(def_res[0])

        self.res_height = QLineEdit()
        self.res_height.setReadOnly(False)
        self.res_height.setEnabled(True)
        self.res_height.setText(def_res[1])
        self.res_height.setPlaceholderText(def_res[1])

        self.depth_offset = QLineEdit()
        self.depth_offset.setReadOnly(False)
        self.depth_offset.setEnabled(True)
        self.depth_offset.setPlaceholderText('0')

        w_res_validator = QIntValidator()
        w_res_validator.setRange(1, 7680)

        h_res_validator = QIntValidator()
        h_res_validator.setRange(1, 4320)

        offset_validator = QIntValidator()
        offset_validator.setRange(1, 9999999)

        self.res_width.setValidator(w_res_validator)
        self.res_height.setValidator(h_res_validator)
        self.depth_offset.setValidator(offset_validator)
        
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

        self.ok = False
    
    def accept(self):
        if len(self.file_name.text()) > 0:
            if self.res_width.hasAcceptableInput() and self.res_height.hasAcceptableInput():
                self.ok = True
                super().accept()
            else:
                self.error_dialog.showMessage('No valid Resolution has been given! Maximum Resolution: 7680x4320 ; Minimum Resolution: 1x1 ')
        else:
            self.error_dialog.showMessage('Please choose a file name!')
        
            
        
    def createForm(self):
  
        # creating a form layout
        layout = QFormLayout()
  
        # adding rows
        # for name and adding input text
        layout.addRow(QLabel("File Name"), self.file_name)
        layout.addRow(QLabel("Width"), self.res_width)
        layout.addRow(QLabel("Height"), self.res_height)
        layout.addRow(QLabel("Depth Offset"), self.depth_offset)
  
        # setting layout
        self.formGroupBox.setLayout(layout)
