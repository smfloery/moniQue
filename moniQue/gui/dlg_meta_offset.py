import numpy as np
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QGroupBox, QLineEdit, QDialogButtonBox, QVBoxLayout, QFormLayout, QLabel, QErrorMessage, QPushButton
import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)

class OffsetMetaDialog(QDialog):

    # preview_offset_signal = QtCore.pyqtSignal(object, bool)
    offset_selected_signal = QtCore.pyqtSignal(object)
    
    def __init__(self):
        super(OffsetMetaDialog, self).__init__()

        # setting window title
        self.setWindowTitle("Set offset for camera position")
  
        # setting geometry to the window
        self.setGeometry(1000, 500, 1000, 300)

        self.canvas = MplCanvas(self, width=2, height=1, dpi=100)
        self.canvas.mpl_connect("motion_notify_event", self.on_move)
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.curr_offset_line = None
        self.curr_offset_text = None
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

    def plot_data(self, data):
        
        self.data = data
        
        offset = data["offset"]
        profile = data["profile"]
        prc = data["prc"]
        pnts_ray = prc + offset.reshape(-1, 1)*data["ray_dir"]

        self.canvas.ax.plot(offset, profile, color="black")
        self.canvas.ax.plot([offset[0], offset[-1]], [pnts_ray[0, 2], pnts_ray[-1, 2]], linestyle="--", color="green")
        self.canvas.ax.scatter(0, prc[2], s=75, c="red", marker="+", zorder=10)
        self.canvas.ax.set_xlim([offset[0], offset[-1]])

    def on_click(self, event):
        clicked_offset = event.xdata
        clicked_prc = self.data["prc"] + clicked_offset*self.data["ray_dir"]
        
        if clicked_offset is not None:
            self.offset_selected_signal.emit({"offset":clicked_offset, "offset_prc":clicked_prc.ravel()})
        
    def on_move(self, event):
        curr_offset = event.xdata
        
        if curr_offset is not None:
            curr_offset_ix = np.searchsorted(np.sort(self.data["offset"]), curr_offset*(-1))
            curr_profile = self.data["profile"][curr_offset_ix]

            curr_ray_pnt = self.data["prc"] + curr_offset * self.data["ray_dir"]
            curr_ray_pnt_h = curr_ray_pnt.ravel()[2]
            
            if self.curr_offset_text is None:
                self.curr_offset_text = self.canvas.ax.annotate("%.1fm" % (curr_ray_pnt_h - curr_profile),         
                                                                xy=(event.x, event.y),
                                                                xycoords='figure pixels',
                                                                xytext=(5, 5),
                                                                textcoords='offset points',
                                                                fontweight="bold",
                                                                fontsize=12)
            else:
                self.curr_offset_text.remove()
                self.curr_offset_text = self.canvas.ax.annotate("%.1fm" % (curr_ray_pnt_h - curr_profile),         
                                                                xy=(event.x, event.y),
                                                                xycoords='figure pixels',
                                                                xytext=(5, 5),
                                                                textcoords='offset points',
                                                                fontweight="bold",
                                                                fontsize=12)
                
            if self.curr_offset_line is None:        
                self.curr_offset_line = self.canvas.ax.plot([curr_offset, curr_offset], [curr_ray_pnt_h, curr_profile], color="orange")[0]
            else:
                self.curr_offset_line.set_data([curr_offset, curr_offset],[curr_ray_pnt_h, curr_profile])
                
            self.canvas.draw()
        
        else:
            if self.curr_offset_line is not None:
                self.curr_offset_line.remove()
                self.curr_offset_line = None
            if self.curr_offset_text is not None:
                self.curr_offset_text.remove()   
                self.curr_offset_text = None
            
            self.canvas.draw()