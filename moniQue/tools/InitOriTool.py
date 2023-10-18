from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsFeature, QgsPoint, QgsGeometry, QgsRaster, QgsWkbTypes
from qgis.PyQt.QtCore import Qt
import json

class InitOriTool(QgsMapTool):
    
    def __init__(self, canvas):        
        self.canvas = canvas
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
                    
                    self.ori_pnts.append([mx, my, click_h])
                    self.is_drawing = True
                    
                    if len(self.ori_pnts) == 1:
                        print("Wohoooo")
                        self.rubberPnt.addPoint(QgsPointXY(mx, my), True)
                        self.rubberPnt.show()
                    elif len(self.ori_pnts) == 2:
                        self.store_ori()
    
    def store_ori(self):
        print("Whoop")
        print(self.ori_pnts)
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