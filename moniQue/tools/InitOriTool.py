from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsFeature, QgsPoint, QgsGeometry, QgsRaster, QgsWkbTypes
from qgis.PyQt.QtCore import Qt
import json
import math

class InitOriTool(QgsMapTool):
    
    def __init__(self, canvas, dlg):        
        self.canvas = canvas
        self.dlg = dlg
        self.is_drawing = False
        
        QgsMapTool.__init__(self, self.canvas)
        
        self.rubberPnt = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.rubberPnt.setColor(Qt.white)
        self.rubberPnt.setStrokeColor(Qt.black)
        self.rubberPnt.setWidth(1)
        self.rubberPnt.setIconSize(10)
        self.rubberPnt.reset(QgsWkbTypes.PointGeometry)
        
        self.rubberOri = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubberOri.setColor(Qt.red)
        self.rubberOri.setWidth(2)
        self.rubberOri.setLineStyle(Qt.DashLine)
        self.rubberOri.reset()
        
        self.ori_pnts = []
        
    def set_dhm_src(self, lyr):
        self.dhm_src = lyr
    
    def set_camera(self, camera):
        self.camera = camera
                
    def canvasPressEvent(self, e):
        
        if e.button() == Qt.LeftButton:

            click_pos = self.toMapCoordinates(e.pos())            
            mx, my = float(click_pos.x()), float(click_pos.y())
            
            if self.dhm_src is not None:
            
                click_h = self.dhm_src.dataProvider().identify(QgsPointXY(mx, my), QgsRaster.IdentifyFormatValue).results()[1]
                
                if click_h is not None:
                    
                    self.rubberOri.addPoint(QgsPointXY(mx, my), True)

                    if not self.is_drawing: #it appaers that the first point is added twice?
                        self.rubberOri.removeLastPoint()    
                        
                    self.rubberOri.show()
                    
                    self.ori_pnts.append(QgsPoint(mx, my, click_h))
                    self.is_drawing = True
                    
                    if len(self.ori_pnts) == 1:
                        print("Wohoooo")
                        self.rubberPnt.addPoint(QgsPointXY(mx, my), True)
                        self.rubberPnt.show()
                    elif len(self.ori_pnts) == 2:
                        self.store_ori()
    
    def store_ori(self):
        
        init_azi = self.ori_pnts[0].azimuth(self.ori_pnts[1])
        init_f = math.sqrt(self.camera.w**2 + self.camera.h**2)
        
        self.dlg.line_X.setText("%.1f" % (self.ori_pnts[0].x()))
        self.dlg.line_Y.setText("%.1f" % (self.ori_pnts[0].y()))
        self.dlg.line_Z.setText("%.1f" % (self.ori_pnts[0].z()))
        
        self.dlg.line_alpha.setText("%.1f" % (init_azi))
    
        if self.camera.w > self.camera.h:
            self.dlg.line_zeta.setText("%.1f" % (0))
            self.dlg.line_kappa.setText("%.1f" % (90))
        else:
            self.dlg.line_zeta.setText("%.1f" % (90))
            self.dlg.line_kappa.setText("%.1f" % (0))
        
        self.dlg.line_f.setText("%.1f" % (init_f))
        self.dlg.line_x0.setText("%.1f" % (self.camera.w/2.))
        self.dlg.line_y0.setText("-%.1f" % (self.camera.h/2.))
        
        self.is_drawing = False
        self.rubberOri.reset()
        self.rubberPnt.reset(QgsWkbTypes.PointGeometry)
        self.ori_pnts = []
                
    def canvasMoveEvent(self, e):
        
        if self.is_drawing:
            
            pos = self.toMapCoordinates(e.pos())
            mx, my = float(pos.x()), float(pos.y())

            if self.rubberOri.numberOfVertices() == 1:
                self.rubberOri.addPoint(QgsPointXY(mx, my), True)  
            elif self.rubberOri.numberOfVertices() == 2:
                self.rubberOri.removeLastPoint()
                self.rubberOri.addPoint(QgsPointXY(mx, my), True)
            
            self.rubberOri.show()
            
    def reset(self):
        pass
        
    def deactivate(self):
        QgsMapTool.deactivate(self)        
        self.rubberOri.reset()
        self.rubberPnt.reset(QgsWkbTypes.PointGeometry)
        self.ori_pnts = []
        self.is_drawing = False
        self.deactivated.emit()