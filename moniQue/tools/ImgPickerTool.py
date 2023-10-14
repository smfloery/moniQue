from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsFeature, QgsPoint, QgsGeometry
from qgis.PyQt.QtCore import Qt

class ImgPickerTool(QgsMapTool):
    
    def __init__(self, canvas):
        
        self.canvas = canvas
        # self.meta_window = meta_window
        
        QgsMapTool.__init__(self, self.canvas)
        
    def set_layers(self, lyr):
        self.lyr = lyr
        
    def set_camera(self, camera):
        self.camera = camera
                
    def canvasPressEvent(self, e):
        
        if e.button() == Qt.LeftButton:

            click_pos = self.toMapCoordinates(e.pos())            
            mx, my = float(click_pos.x()), float(click_pos.y())
            
            if (mx >= 0) and (mx <= self.camera.w):
                if (my <= 0) and (my >= self.camera.h*(-1)):
                    
                    feat = QgsFeature(self.lyr.fields())
                    
                    feat.setGeometry(QgsPoint(mx, my))
                    feat["iid"] = self.camera.iid
                    feat["gid"] = -1
                    feat["x"] = mx
                    feat["y"] = my
                    
                    #img_feat.setAttributes([self.camera.id, self.camera.meta["von"], self.camera.meta["bis"], feat_attr["type"], feat_attr["comment"]])
                    self.lyr.dataProvider().addFeatures([feat])
                    
                    self.lyr.commitChanges()
                    self.lyr.triggerRepaint()
                    self.lyr.reload()
                    self.canvas.refresh()
                    
    def reset(self):
        pass
        
    def deactivate(self):
        QgsMapTool.deactivate(self)        
        self.deactivated.emit()