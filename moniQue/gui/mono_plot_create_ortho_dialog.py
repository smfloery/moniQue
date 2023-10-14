# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\gui\mono_plot_create_ortho_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(500, 227)
        Dialog.setMinimumSize(QtCore.QSize(500, 200))
        Dialog.setMaximumSize(QtCore.QSize(500, 250))
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(329, 190, 161, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.layoutWidget = QtWidgets.QWidget(Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 150, 481, 28))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_out = QtWidgets.QLabel(self.layoutWidget)
        self.label_out.setObjectName("label_out")
        self.horizontalLayout.addWidget(self.label_out)
        self.line_out_path = QtWidgets.QLineEdit(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line_out_path.sizePolicy().hasHeightForWidth())
        self.line_out_path.setSizePolicy(sizePolicy)
        self.line_out_path.setMaximumSize(QtCore.QSize(350, 16777215))
        self.line_out_path.setObjectName("line_out_path")
        self.horizontalLayout.addWidget(self.line_out_path)
        self.btn_out_path = QtWidgets.QPushButton(self.layoutWidget)
        self.btn_out_path.setObjectName("btn_out_path")
        self.horizontalLayout.addWidget(self.btn_out_path)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 232, 141))
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.radio_las = QtWidgets.QRadioButton(self.groupBox)
        self.radio_las.setChecked(True)
        self.radio_las.setObjectName("radio_las")
        self.horizontalLayout_3.addWidget(self.radio_las)
        self.radio_tif = QtWidgets.QRadioButton(self.groupBox)
        self.radio_tif.setChecked(False)
        self.radio_tif.setObjectName("radio_tif")
        self.horizontalLayout_3.addWidget(self.radio_tif)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_res = QtWidgets.QLabel(self.groupBox)
        self.label_res.setEnabled(False)
        self.label_res.setMaximumSize(QtCore.QSize(75, 16777215))
        self.label_res.setObjectName("label_res")
        self.horizontalLayout_2.addWidget(self.label_res)
        spacerItem = QtWidgets.QSpacerItem(30, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.line_res = QtWidgets.QLineEdit(self.groupBox)
        self.line_res.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line_res.sizePolicy().hasHeightForWidth())
        self.line_res.setSizePolicy(sizePolicy)
        self.line_res.setMinimumSize(QtCore.QSize(75, 20))
        self.line_res.setMaximumSize(QtCore.QSize(75, 16777215))
        self.line_res.setClearButtonEnabled(True)
        self.line_res.setObjectName("line_res")
        self.horizontalLayout_2.addWidget(self.line_res)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_min_dist = QtWidgets.QLabel(self.groupBox)
        self.label_min_dist.setEnabled(False)
        self.label_min_dist.setMaximumSize(QtCore.QSize(105, 16777215))
        self.label_min_dist.setObjectName("label_min_dist")
        self.horizontalLayout_4.addWidget(self.label_min_dist)
        spacerItem1 = QtWidgets.QSpacerItem(30, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.line_min_dist = QtWidgets.QLineEdit(self.groupBox)
        self.line_min_dist.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line_min_dist.sizePolicy().hasHeightForWidth())
        self.line_min_dist.setSizePolicy(sizePolicy)
        self.line_min_dist.setMinimumSize(QtCore.QSize(75, 20))
        self.line_min_dist.setMaximumSize(QtCore.QSize(75, 16777215))
        self.line_min_dist.setClearButtonEnabled(True)
        self.line_min_dist.setObjectName("line_min_dist")
        self.horizontalLayout_4.addWidget(self.line_min_dist)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.check_toc = QtWidgets.QCheckBox(self.groupBox)
        self.check_toc.setEnabled(False)
        self.check_toc.setCheckable(True)
        self.check_toc.setChecked(True)
        self.check_toc.setAutoExclusive(False)
        self.check_toc.setTristate(False)
        self.check_toc.setObjectName("check_toc")
        self.verticalLayout.addWidget(self.check_toc)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_out.setText(_translate("Dialog", "Output:"))
        self.btn_out_path.setText(_translate("Dialog", "Browse"))
        self.groupBox.setTitle(_translate("Dialog", "Output Format"))
        self.radio_las.setText(_translate("Dialog", "Pointcloud (.las)"))
        self.radio_tif.setText(_translate("Dialog", "Orthophoto (.tif)"))
        self.label_res.setText(_translate("Dialog", "Resolution [m]:"))
        self.line_res.setText(_translate("Dialog", "1"))
        self.line_res.setPlaceholderText(_translate("Dialog", "m"))
        self.label_min_dist.setText(_translate("Dialog", "Minimum distance [m]:"))
        self.line_min_dist.setText(_translate("Dialog", "25"))
        self.line_min_dist.setPlaceholderText(_translate("Dialog", "m"))
        self.check_toc.setText(_translate("Dialog", "Add to TOC"))
