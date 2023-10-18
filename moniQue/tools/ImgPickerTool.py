from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsFeature, QgsPoint, QgsGeometry, QgsJsonUtils
from qgis.PyQt.QtCore import Qt
import json
class ImgPickerTool(QgsMapTool):
    
    def __init__(self, canvas, meta_window):
        
        self.canvas = canvas
        self.meta_window = meta_window
        
        QgsMapTool.__init__(self, self.canvas)
        
    def set_layers(self, img_lyr, map_lyr):
        self.img_lyr = img_lyr
        self.img_lyr_gix = img_lyr.dataProvider().fieldNameIndex('gid')

        self.map_lyr = map_lyr
        self.map_lyr_gix = map_lyr.dataProvider().fieldNameIndex('gid')

    def set_camera(self, camera):
        self.camera = camera
                
    def canvasPressEvent(self, e):
        
        if e.button() == Qt.LeftButton:

            click_pos = self.toMapCoordinates(e.pos())            
            mx, my = float(click_pos.x()), float(click_pos.y())
            
            if (mx >= 0) and (mx <= self.camera.w):
                if (my <= 0) and (my >= self.camera.h*(-1)):
                                                           
                    img_gids = [feat.attributes()[self.img_lyr_gix] for feat in self.img_lyr.getFeatures()]
                    map_gids = [feat.attributes()[self.map_lyr_gix] for feat in self.map_lyr.getFeatures()]
                    pot_gids = list(set(map_gids).difference(img_gids))
                    
                    self.meta_window.combo_gid.clear()
                    self.meta_window.combo_gid.addItems(pot_gids)
                    
                    self.meta_window.line_iid.setText(self.camera.iid)
                    self.meta_window.line_img_x.setText(str(mx))
                    self.meta_window.line_img_y.setText(str(my))
                    
                    result = self.meta_window.exec_() 
                    if result:

                        feat = QgsFeature(self.img_lyr.fields())
                
                        feat.setGeometry(QgsPoint(mx, my))
                        feat["iid"] = self.camera.iid
                        feat["gid"] = self.meta_window.combo_gid.currentText() 
                        feat["x"] = mx
                        feat["y"] = my
                        feat["desc"] = self.meta_window.line_desc.text() 
                        feat["active"] = 1
                        
                        #img_feat.setAttributes([self.camera.id, self.camera.meta["von"], self.camera.meta["bis"], feat_attr["type"], feat_attr["comment"]])
                        self.img_lyr.dataProvider().addFeatures([feat])
                        
                        self.img_lyr.commitChanges()
                        self.img_lyr.triggerRepaint()
                        self.img_lyr.reload()
                        self.canvas.refresh()
                    
    def reset(self):
        pass
        
    def deactivate(self):
        QgsMapTool.deactivate(self)        
        self.deactivated.emit()