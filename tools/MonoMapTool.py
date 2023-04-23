from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsFeature, QgsPoint, QgsGeometry
from qgis.PyQt.QtCore import Qt
import open3d as o3d

class MonoMapTool(QgsMapTool):
    
    def __init__(self, img_canvas, map_canvas, meta_window):
        self.is_drawing = False
        
        self.img_canvas = img_canvas
        self.map_canvas = map_canvas
        self.meta_window = meta_window
        
        QgsMapTool.__init__(self, self.img_canvas)
        self.rubberRay = QgsRubberBand(self.map_canvas)
        self.rubberRay.setColor(Qt.red)
        self.rubberRay.setLineStyle(Qt.DashLine)
        self.rubberRay.setWidth(2)
        self.rubberRay.reset()
        
        self.rubberMap = QgsRubberBand(self.map_canvas)
        self.rubberMap.setColor(Qt.blue)
        self.rubberMap.setWidth(2)
        self.rubberMap.reset()
        
        self.rubberMap_h = []
        
        self.rubberImg = QgsRubberBand(self.img_canvas)
        self.rubberImg.setColor(Qt.green)
        self.rubberImg.setWidth(2)
        self.rubberImg.reset()
        
        self.rubberImg_prev = QgsRubberBand(self.img_canvas)
        self.rubberImg_prev.setColor(Qt.green)
        self.rubberImg_prev.setWidth(2)
        self.rubberImg_prev.setLineStyle(Qt.DashLine)
        self.rubberImg_prev.reset()
        
        self.rubberMap_prev = QgsRubberBand(self.map_canvas)
        self.rubberMap_prev.setColor(Qt.blue)
        self.rubberMap_prev.setWidth(2)
        self.rubberMap_prev.setLineStyle(Qt.DashLine)
        self.rubberMap_prev.reset()
        
    def set_scene(self, scene):
        self.ray_scene = scene
        
    def set_layers(self, img_lyr, map_lyr):
        self.img_lyr = img_lyr
        self.map_lyr = map_lyr
        
    def set_camera(self, camera):
        self.camera = camera
        self.rubberRay.reset()
        self.rubberMap.reset()
        self.rubberMap_h = []
        self.rubberImg.reset()
        self.rubberRay.addPoint(QgsPointXY(self.camera.prc[0], self.camera.prc[1]))
                
    def canvasPressEvent(self, e):
        
        if e.button() == Qt.LeftButton:
            
            self.is_drawing = True
            
            click_pos = self.toMapCoordinates(e.pos())
            mx, my = float(click_pos.x()), float(click_pos.y())
            
            if (mx >= 0) and (mx <= self.camera.img_w):
                if (my <= 0) and (my >= self.camera.img_h*(-1)):
                                
                    ray = self.camera.ray(img_x=mx, img_y=my)
                    o3d_ray = o3d.core.Tensor([ray], dtype=o3d.core.Dtype.Float32)
                    ans = self.ray_scene.cast_rays(o3d_ray)
                    
                    if ans['t_hit'].isfinite():
                        obj_coord = o3d_ray[0,:3] + o3d_ray[0,3:]*ans['t_hit'].reshape((-1,1))
                        obj_coord = obj_coord.numpy().ravel()
                    
                        self.rubberMap.addPoint(QgsPointXY(obj_coord[0], obj_coord[1]), True)
                        self.rubberMap_h.append(obj_coord[2])
                        self.rubberMap.show()
                        
                        self.rubberImg.addPoint(QgsPointXY(mx, my), True)
                        self.rubberImg.show()
                        
                        self.rubberImg_prev.reset()
                        self.rubberImg_prev.addPoint(QgsPointXY(mx, my), True)
                        self.rubberImg_prev.show()
                        
                        self.rubberMap_prev.reset()
                        self.rubberMap_prev.addPoint(QgsPointXY(obj_coord[0], obj_coord[1]), True)
                        self.rubberMap_prev.show()
        
        elif e.button() == Qt.RightButton:
            
            if self.rubberMap.numberOfVertices() > 3:
                
                map_line_geom = self.rubberMap.asGeometry()
                map_line_pnts_h = []
                for ix, vertex in enumerate(map_line_geom.vertices()):
                        v_x = vertex.x()
                        v_y = vertex.y()
                        v_h = self.rubberMap_h[ix]
                        map_line_pnts_h.append(QgsPoint(v_x, v_y, v_h))
                
                
                img_line_geom = self.rubberImg.asGeometry()
                
                self.meta_window.fillAttributes(self.camera)
                result = self.meta_window.exec_() 
                
                if result:
                
                    feat_attr = self.meta_window.getMeta()
                    
                    self.meta_window.clearFields()
                    
                    map_feat = QgsFeature(self.map_lyr.fields())
                    map_feat.setGeometry(QgsGeometry.fromPolyline(map_line_pnts_h))
                    map_feat["mtum_id"] = self.camera.id
                    map_feat["von"] = self.camera.meta["von"]
                    map_feat["bis"] = self.camera.meta["bis"]
                    map_feat["type"] = feat_attr["type"]
                    map_feat["comment"] = feat_attr["comment"]
                    # map_feat.setAttributes([self.camera.id, self.camera.meta["von"], self.camera.meta["bis"], feat_attr["type"], feat_attr["comment"]])
                    self.map_lyr.dataProvider().addFeatures([map_feat])
                    
                    self.map_lyr.commitChanges()
                    self.map_lyr.triggerRepaint()
                    self.map_canvas.refresh()
                    
                    img_feat = QgsFeature(self.img_lyr.fields())
                    img_feat.setGeometry(img_line_geom)
                    img_feat["mtum_id"] = self.camera.id
                    img_feat["von"] = self.camera.meta["von"]
                    img_feat["bis"] = self.camera.meta["bis"]
                    img_feat["type"] = feat_attr["type"]
                    img_feat["comment"] = feat_attr["comment"]
                    
                    #img_feat.setAttributes([self.camera.id, self.camera.meta["von"], self.camera.meta["bis"], feat_attr["type"], feat_attr["comment"]])
                    self.img_lyr.dataProvider().addFeatures([img_feat])
                    
                    self.img_lyr.commitChanges()
                    self.img_lyr.triggerRepaint()
                    self.img_lyr.reload()
                    # self.img_canvas.refresh()
                
            self.is_drawing = False
            self.rubberMap.reset()
            self.rubberMap_h = []
            self.rubberImg.reset()
            self.rubberImg_prev.reset()
            self.rubberMap_prev.reset()
                
    def canvasMoveEvent(self, e):
        pos = self.toMapCoordinates(e.pos())
    
        mx, my = float(pos.x()), float(pos.y())
        
        if (mx >= 0) and (mx <= self.camera.img_w):
            if (my <= 0) and (my >= self.camera.img_h*(-1)):
        
                ray = self.camera.ray(img_x=mx, img_y=my)
                o3d_ray = o3d.core.Tensor([ray], dtype=o3d.core.Dtype.Float32)
                ans = self.ray_scene.cast_rays(o3d_ray)
    
                if self.is_drawing:
                    if self.rubberImg_prev.numberOfVertices() == 2:
                        self.rubberImg_prev.removeLastPoint()
                    self.rubberImg_prev.addPoint(QgsPointXY(mx, my), True)
                
                if ans['t_hit'].isfinite():
                    obj_coord = o3d_ray[0,:3] + o3d_ray[0,3:]*ans['t_hit'].reshape((-1,1))
                    obj_coord = obj_coord.numpy().ravel()
                    
                    if self.rubberRay.numberOfVertices() == 2:
                        self.rubberRay.removeLastPoint()
                    
                    self.rubberRay.addPoint(QgsPointXY(obj_coord[0], obj_coord[1]), True)
                    self.rubberRay.show()
                    
                    if self.is_drawing:
                        if self.rubberMap_prev.numberOfVertices() == 2:
                            self.rubberMap_prev.removeLastPoint()
                        self.rubberMap_prev.addPoint(QgsPointXY(obj_coord[0], obj_coord[1]), True)
                        
                else:
                    if self.rubberRay.numberOfVertices() == 2:
                        self.rubberRay.removeLastPoint()
                        
                    if self.rubberMap_prev.numberOfVertices() == 2:
                        self.rubberMap_prev.removeLastPoint()
            else:
                if self.rubberRay.numberOfVertices() == 2:
                    self.rubberRay.removeLastPoint()
                    
                if self.rubberMap_prev.numberOfVertices() == 2:
                    self.rubberMap_prev.removeLastPoint()
        else:
            if self.rubberRay.numberOfVertices() == 2:
                self.rubberRay.removeLastPoint()
                    
            if self.rubberMap_prev.numberOfVertices() == 2:
                self.rubberMap_prev.removeLastPoint()
                    
    def reset(self):
        self.rubberRay.reset()
        
        self.rubberImg.reset()
        self.rubberImg_prev.reset()
        
        self.rubberMap_h = []
        self.rubberMap.reset()
        self.rubberMap_prev.reset()
        
        self.rubberRay.addPoint(QgsPointXY(self.camera.prc[0], self.camera.prc[1]))
        
    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.rubberRay.reset()
        
        self.rubberImg.reset()
        self.rubberImg_prev.reset()
        
        self.rubberMap_h = []
        self.rubberMap.reset()
        self.rubberMap_prev.reset()
        
        self.deactivated.emit()