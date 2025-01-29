from PyQt5.QtWidgets import QDialog, QGroupBox, QLineEdit, QDialogButtonBox, QVBoxLayout, QFormLayout, QLabel, QComboBox, QErrorMessage, QFileDialog
from PyQt5.QtGui import QIntValidator

class OffsetMetaDialog(QDialog):
  
    def __init__(self):
        super(OffsetMetaDialog, self).__init__()
        
        # setting window title
        self.setWindowTitle("Set offset for camera position")
  
        # setting geometry to the window
        self.setGeometry(1000, 500, 300, 250)
  
        # creating a group box
        self.formGroupBox = QGroupBox()

        self.offset_x = QLineEdit()
        self.offset_x.setReadOnly(False)
        self.offset_x.setEnabled(True)
        self.offset_x.setPlaceholderText('0')

        self.offset_y = QLineEdit()
        self.offset_y.setReadOnly(False)
        self.offset_y.setEnabled(True)
        self.offset_y.setPlaceholderText('0')

        self.offset_z = QLineEdit()
        self.offset_z.setReadOnly(False)
        self.offset_z.setEnabled(True)
        self.offset_z.setPlaceholderText('0')

        self.offset_al = QLineEdit()
        self.offset_al.setReadOnly(False)
        self.offset_al.setEnabled(True)
        self.offset_al.setPlaceholderText('0')

        self.offset_ka = QLineEdit()
        self.offset_ka.setReadOnly(False)
        self.offset_ka.setEnabled(True)
        self.offset_ka.setPlaceholderText('0')

        self.offset_ze = QLineEdit()
        self.offset_ze.setReadOnly(False)
        self.offset_ze.setEnabled(True)
        self.offset_ze.setPlaceholderText('0')

        self.offset_fov = QLineEdit()
        self.offset_fov.setReadOnly(False)
        self.offset_fov.setEnabled(True)
        self.offset_fov.setPlaceholderText('0')
        
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

    
    def accept(self):
        super().accept()
        
    def createForm(self):
  
        # creating a form layout
        layout = QFormLayout()
  
        # adding rows
        # for name and adding input text
        layout.addRow(QLabel("Offset_X"), self.offset_x)
        layout.addRow(QLabel("Offset_Y"), self.offset_y)
        layout.addRow(QLabel("Offset_Z"), self.offset_z)
        layout.addRow(QLabel("Offset_Alpha"), self.offset_al)
        layout.addRow(QLabel("Offset_Kappa"), self.offset_ka)
        layout.addRow(QLabel("Offset_Zeta"), self.offset_ze)
        layout.addRow(QLabel("Offset_FOV"), self.offset_fov)

  
        # setting layout
        self.formGroupBox.setLayout(layout)
