from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsRectangle, QgsWkbTypes, QgsVectorLayer
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class SelectTool(QgsMapTool):
    
    def __init__(self, img_canvas):
        self.img_canvas = img_canvas
        
        QgsMapTool.__init__(self, self.img_canvas)
        
        self.rubberBand = QgsRubberBand(self.img_canvas, QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setFillColor(QColor(255, 0, 0, 50))
        self.rubberBand.setStrokeColor(Qt.red)
        self.reset()

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)

    def set_layers(self, img_lyr, map_lyr):
        self.img_lyr = img_lyr
        self.map_lyr = map_lyr
    
    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.img_lyr.removeSelection()
            self.map_lyr.removeSelection()
            self.startPoint = self.toMapCoordinates(e.pos())
            self.endPoint = self.startPoint
            self.isEmittingPoint = True
            self.showRect(self.startPoint, self.endPoint)
            
        elif e.button() == Qt.RightButton:
            self.reset()
            self.map_lyr.removeSelection()
            self.img_lyr.removeSelection()

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        r = self.rectangle()
        
        if r is not None:
            self.img_lyr.selectByRect(r, QgsVectorLayer.SetSelection)
            self.reset()
            
            img_sel_feat_ids = self.img_lyr.selectedFeatureIds()
            if len(img_sel_feat_ids) > 0:
                self.map_lyr.selectByIds(img_sel_feat_ids)
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete:
            self.map_lyr.startEditing()
            self.img_lyr.startEditing()
            
            self.map_lyr.deleteSelectedFeatures()
            self.img_lyr.deleteSelectedFeatures()
            
            self.map_lyr.commitChanges()
            self.img_lyr.commitChanges()
        else:
            pass
                
    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endPoint = self.toMapCoordinates(e.pos())
        self.showRect(self.startPoint, self.endPoint)

    def showRect(self, startPoint, endPoint):
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        point1 = QgsPointXY(startPoint.x(), startPoint.y())
        point2 = QgsPointXY(startPoint.x(), endPoint.y())
        point3 = QgsPointXY(endPoint.x(), endPoint.y())
        point4 = QgsPointXY(endPoint.x(), startPoint.y())

        self.rubberBand.addPoint(point1, False)
        self.rubberBand.addPoint(point2, False)
        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(point4, False)  
        self.rubberBand.closePoints(True) # true to update canvas
        self.rubberBand.show()

    def rectangle(self):
        if self.startPoint is None or self.endPoint is None:
            return None
        elif (self.startPoint.x() == self.endPoint.x() or \
            self.startPoint.y() == self.endPoint.y()):
            return None

        return QgsRectangle(self.startPoint, self.endPoint)

    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.deactivated.emit()