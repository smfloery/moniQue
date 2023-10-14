from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsFeature, QgsPoint, QgsGeometry, QgsRaster
from qgis.PyQt.QtCore import Qt

class MapPickerTool(QgsMapTool):
    
    def __init__(self, canvas):
        
        self.canvas = canvas
        # self.meta_window = meta_window
        
        QgsMapTool.__init__(self, self.canvas)
        
    def set_layers(self, lyr):
        self.lyr = lyr
    
    def set_dhm_src(self, lyr):
        self.dhm_src = lyr
    
    def set_camera(self, camera):
        self.camera = camera
                
    def canvasPressEvent(self, e):
        
        if e.button() == Qt.LeftButton:

            click_pos = self.toMapCoordinates(e.pos())            
            mx, my = float(click_pos.x()), float(click_pos.y())
            
            click_h = self.dhm_src.dataProvider().identify(QgsPointXY(mx, my), QgsRaster.IdentifyFormatValue).results()[1]
            if click_h is not None:
                
                feat = QgsFeature(self.lyr.fields())
                feat.setGeometry(QgsPoint(mx, my))
                feat["iid"] = self.camera.iid
                feat["gid"] = -1
                feat["X"] = mx
                feat["Y"] = my
                feat["H"] = click_h
                feat["H_src"] = self.dhm_src.name()
                
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