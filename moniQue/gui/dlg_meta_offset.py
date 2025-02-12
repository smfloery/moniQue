import numpy as np
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QGroupBox, QLineEdit, QDialogButtonBox, QVBoxLayout, QFormLayout, QLabel, QErrorMessage, QPushButton


class OffsetMetaDialog(QDialog):

    preview_offset_signal = QtCore.pyqtSignal(object, bool)
  
    def __init__(self):
        super(OffsetMetaDialog, self).__init__()

        # setting window title
        self.setWindowTitle("Set offset for camera position")
  
        # setting geometry to the window
        self.setGeometry(1000, 500, 300, 250)
  
        # creating a group box
        self.formGroupBox = QGroupBox()

        self.forward = QLineEdit()
        self.forward.setReadOnly(False)
        self.forward.setEnabled(True)
        self.forward.setPlaceholderText('0')

        self.right = QLineEdit()
        self.right.setReadOnly(False)
        self.right.setEnabled(True)
        self.right.setPlaceholderText('0')

        self.up = QLineEdit()
        self.up.setReadOnly(False)
        self.up.setEnabled(True)
        self.up.setPlaceholderText('0')
        
        self.createForm()

        # creating a dialog button for ok and cancel
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)

        self.previewButton = QPushButton(self.tr("&Preview"))
        self.buttonBox.addButton(self.previewButton, QDialogButtonBox.ActionRole)

        # adding action when form is accepted
        self.buttonBox.accepted.connect(self.accept)
        self.previewButton.clicked.connect(self.preview)
  
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

        self.accepted = False

    
    def accept(self):
        self.accepted = True
        self.preview()
        super().accept()

    def preview(self):
        self.preview_offset = [self.forward.text(), self.right.text(), self.up.text()]
        self.preview_offset_signal.emit(self.preview_offset, self.accepted)
        
    def createForm(self):
  
        # creating a form layout
        layout = QFormLayout()
  
        # adding rows
        # for name and adding input text
        layout.addRow(QLabel("Forward"), self.forward)
        layout.addRow(QLabel("Right"), self.right)
        layout.addRow(QLabel("Up"), self.up)

        # setting layout
        self.formGroupBox.setLayout(layout)


