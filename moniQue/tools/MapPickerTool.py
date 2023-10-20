from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsFeature, QgsPoint, QgsGeometry, QgsRaster
from qgis.PyQt.QtCore import Qt
from PyQt5.QtCore import pyqtSignal

import json
class MapPickerTool(QgsMapTool):
    
    featAdded = pyqtSignal(object)

    def __init__(self, canvas, meta_window):
        
        self.canvas = canvas
        self.meta_window = meta_window
        
        QgsMapTool.__init__(self, self.canvas)
        
    def set_layers(self, img_lyr, map_lyr):
        self.img_lyr = img_lyr
        self.img_lyr_gix = img_lyr.dataProvider().fieldNameIndex('gid')
        self.map_lyr = map_lyr
        self.map_lyr_gix = map_lyr.dataProvider().fieldNameIndex('gid')
    
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
        
                    img_gids = [feat.attributes()[self.img_lyr_gix] for feat in self.img_lyr.getFeatures()]
                    map_gids = [feat.attributes()[self.map_lyr_gix] for feat in self.map_lyr.getFeatures()]
                    pot_gids = list(set(img_gids).difference(map_gids))
                    
                    self.meta_window.combo_gid.clear()
                    self.meta_window.combo_gid.addItems(pot_gids)
                    
                    self.meta_window.line_iid.setText(self.camera.iid)
                    self.meta_window.line_obj_x.setText(str(mx))
                    self.meta_window.line_obj_y.setText(str(my))
                    self.meta_window.line_obj_h.setText(str(click_h))
                    
                    result = self.meta_window.exec_() 
                    if result:
                        
                        feat = QgsFeature(self.map_lyr.fields())
                        feat.setGeometry(QgsPoint(mx, my))
                        feat["iid"] = self.camera.iid
                        feat["gid"] = self.meta_window.combo_gid.currentText() 
                        feat["X"] = mx
                        feat["Y"] = my
                        feat["H"] = click_h
                        feat["desc"] = self.meta_window.line_desc.text() 
                        feat["H_src"] = self.dhm_src.dataProvider().dataSourceUri()
                        feat["active"] = 1
                        (res, afeat) = self.map_lyr.dataProvider().addFeatures([feat])
                        self.map_lyr.commitChanges()
                        
                        self.featAdded.emit({"fid":afeat[0].id(), "gid":feat["gid"]})
                        self.map_lyr.triggerRepaint()
                        self.map_lyr.reload()
                        self.canvas.refresh()
                    
    def reset(self):
        pass
        
    def deactivate(self):
        QgsMapTool.deactivate(self)        
        self.deactivated.emit()