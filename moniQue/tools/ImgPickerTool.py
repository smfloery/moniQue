from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsFeature, QgsPoint, QgsGeometry, QgsJsonUtils
from qgis.PyQt.QtCore import Qt
import json
from PyQt5.QtCore import pyqtSignal

class ImgPickerTool(QgsMapTool):
    
    gcpAdded = pyqtSignal(object)

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
        
        if (e.button() == Qt.LeftButton) & (e.modifiers() == Qt.ControlModifier):

            click_pos = self.toMapCoordinates(e.pos())            
            mx, my = float(click_pos.x()), float(click_pos.y())
            
            if (mx >= 0) and (mx <= self.camera.img_w):
                if (my <= 0) and (my >= self.camera.img_h*(-1)):
                    
                    feat_geom = QgsPoint(mx, my)
                    
                    #TODO change feature attributes as well
                    if self.img_lyr.selectedFeatureCount() > 0:
                        sel_fid = self.img_lyr.selectedFeatureIds()[0]
                        self.img_lyr.startEditing()
                        self.img_lyr.changeGeometry(sel_fid, QgsGeometry.fromPoint(feat_geom))
                        self.img_lyr.commitChanges()
                        
                    else:       
                        
                        img_gids = [feat.attributes()[self.img_lyr_gix] for feat in self.img_lyr.getFeatures()]
                        map_gids = [feat.attributes()[self.map_lyr_gix] for feat in self.map_lyr.getFeatures()]
                        pot_gids = list(set(map_gids).difference(img_gids))
                        
                        # self.meta_window.combo_gid.clear()
                        self.meta_window.combo_gid.clearEditText()
                        self.meta_window.combo_gid.addItems(pot_gids)
                        
                        self.meta_window.line_iid.setText(self.camera.iid)
                        self.meta_window.line_img_x.setText("%.1f" % (mx))
                        self.meta_window.line_img_y.setText("%.1f" % (my))
                        
                        result = self.meta_window.exec_() 
                        if result:
                        
                            feat = QgsFeature(self.img_lyr.fields())
                            feat.setGeometry(feat_geom)
                            feat.setAttribute("iid", self.camera.iid)
                            feat.setAttribute("gid", self.meta_window.combo_gid.currentText())
                            feat.setAttribute("img_x", "%.1f" % (mx))
                            feat.setAttribute("img_y", "%.1f" % (my))
                            feat.setAttribute("desc", self.meta_window.line_desc.text())
                            feat.setAttribute("active", 0)
                            
                            #img_feat.setAttributes([self.camera.id, self.camera.meta["von"], self.camera.meta["bis"], feat_attr["type"], feat_attr["comment"]])
                            (res, afeat) = self.img_lyr.dataProvider().addFeatures([feat])
                                                    
                            self.img_lyr.commitChanges()
                            self.gcpAdded.emit({"fid":afeat[0].id(), "gid":feat["gid"], "img_x":mx, "img_y":my, "active":0})
                        
                    self.img_lyr.triggerRepaint()
                    self.canvas.refresh()
                    
    def reset(self):
        pass
        
    def deactivate(self):
        QgsMapTool.deactivate(self)        
        self.deactivated.emit()