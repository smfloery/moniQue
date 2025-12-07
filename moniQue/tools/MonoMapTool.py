from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPointXY, QgsFeature, QgsPoint, QgsGeometry
from qgis.PyQt.QtCore import Qt
import open3d as o3d
import numpy as np
from ..helpers import alzeka2rot, smpls_to_rays, max_evec_dir_north
import diptest

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
        self.rubberMap_std = []
        self.rubberMap_img = []
        self.rubberMap_evec_dir = []
        self.rubberMap_pval = []
        
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
    
    def set_covar_samples(self, smpls, dir2pnts):
        
        self.smpls = smpls
        self.dir2pnts = dir2pnts             
                   
    def set_scene(self, scene):
        self.ray_scene = scene
        
    def set_layers(self, img_lyr, map_lyr, vex_lyr):
        self.img_lyr = img_lyr
        self.map_lyr = map_lyr
        self.vex_lyr = vex_lyr
    
    def set_minxyz(self, min_xyz):
        self.min_xyz = min_xyz
     
    def set_camera(self, camera):
        self.camera = camera
        self.rubberRay.reset()
        self.rubberMap.reset()
        self.rubberMap_h = []
        self.rubberMap_std = []
        self.rubberMap_img = []
        self.rubberMap_evec_dir = []
        self.rubberImg.reset()
        self.rubberRay.addPoint(QgsPointXY(self.camera.prc[0], self.camera.prc[1]))
                
    def canvasPressEvent(self, e):
        
        if e.button() == Qt.LeftButton:
            
            self.is_drawing = True
            
            click_pos = self.toMapCoordinates(e.pos())
            mx, my = float(click_pos.x()), float(click_pos.y())
            
            if (mx >= 0) and (mx <= self.camera.img_w):
                if (my <= 0) and (my >= self.camera.img_h*(-1)):
                    
                    #0:3: prcs; 3:6:dirs
                    rays = smpls_to_rays(self.smpls, self.dir2pnts, mx, my, self.camera.min_d_mono, self.min_xyz)
                    o3d_rays = o3d.core.Tensor(rays, dtype=o3d.core.Dtype.Float32)
                    
                    ans = self.ray_scene.cast_rays(o3d_rays)
                    
                    ans_dist = ans["t_hit"].numpy().ravel()
                    ans_valid = np.isfinite(ans_dist)
                                        
                    if ans_valid[0]:
                                                
                        ans_coords = rays[:, :3] + rays[:, 3:] * ans_dist.reshape(-1, 1)
                        ans_coords = ans_coords[ans_valid, :]                
                        ans_covar = np.cov(ans_coords, rowvar=False)
                        xyz_std = np.sqrt(np.diag(ans_covar))
                        
                        #project coordinates onto line of sight to create 1D distribution along the LOS
                        coords_vec = ans_coords - rays[0, :3]
                        coords_ld = np.sum(coords_vec*rays[0, 3:], axis=1) - ans_dist[0]
                        
                        #use this 1D distributed pnts to calculate the diptest
                        _, pval = diptest.diptest(coords_ld)
                                                
                        dir_north_evec = max_evec_dir_north(ans_covar)
                        
                        obj_coord = ans_coords[0, :] + self.min_xyz
                    
                        self.rubberMap.addPoint(QgsPointXY(obj_coord[0], obj_coord[1]), True)
                        self.rubberMap_h.append(obj_coord[2])
                        self.rubberMap_std.append(xyz_std.ravel().tolist())
                        self.rubberMap_img.append([mx, my])
                        self.rubberMap_evec_dir.append(dir_north_evec)
                        self.rubberMap_pval.append(pval)
                        
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
            
            if self.rubberMap.numberOfVertices() >= 2:
                
                map_line_geom = self.rubberMap.asGeometry()
                map_line_pnts_h = []
                map_line_pnts_std = []
                map_line_pnts_img = []
                map_line_pnts_evec_dir = []
                map_line_pnts_pval = []
                
                for ix, vertex in enumerate(map_line_geom.vertices()):
                        v_x = vertex.x()
                        v_y = vertex.y()
                        v_h = self.rubberMap_h[ix]
                        map_line_pnts_h.append(QgsPoint(v_x, v_y, v_h))
                        map_line_pnts_std.append(self.rubberMap_std[ix])
                        map_line_pnts_img.append(self.rubberMap_img[ix])
                        map_line_pnts_evec_dir.append(self.rubberMap_evec_dir[ix])
                        map_line_pnts_pval.append(self.rubberMap_pval[ix])
                        
                img_line_geom = self.rubberImg.asGeometry()
                                
                self.meta_window.clearFields()
                self.meta_window.fillAttributes(self.camera)
                result = self.meta_window.exec_() 
                
                if result:
                
                    feat_attr = self.meta_window.getMeta()
                    
                    map_feat = QgsFeature(self.map_lyr.fields())
                    map_feat.setGeometry(QgsGeometry.fromPolyline(map_line_pnts_h))
                    map_feat["iid"] = self.camera.iid
                    map_feat["type"] = feat_attr["type"]
                    map_feat["comment"] = feat_attr["comment"]

                    _, added_feat = self.map_lyr.dataProvider().addFeatures([map_feat])
                    line_fid = added_feat[0]["fid"]
                    
                    self.map_lyr.commitChanges()
                    self.map_lyr.triggerRepaint()
                    
                    self.map_canvas.refresh()
                    
                    img_feat = QgsFeature(self.img_lyr.fields())
                    img_feat.setGeometry(img_line_geom)
                    img_feat["iid"] = self.camera.iid
                    img_feat["type"] = feat_attr["type"]
                    img_feat["comment"] = feat_attr["comment"]
                    
                    self.img_lyr.startEditing()
                    self.img_lyr.dataProvider().addFeatures([img_feat])
                    self.img_lyr.commitChanges()
                    self.img_lyr.triggerRepaint()
                    
                    self.img_canvas.refresh()

                    if self.main_dlg:
                        self.main_dlg.mark_gcp_changed(True)

                    vx_feats = []
                    for vx in range(len(map_line_pnts_h)):
                        vex_feat = QgsFeature(self.vex_lyr.fields())
                        vex_feat.setGeometry(QgsGeometry.fromPoint(map_line_pnts_h[vx]))
                        vex_feat["iid"] = self.camera.iid
                        vex_feat["lid"] = line_fid
                        vex_feat["obj_x_std"] = map_line_pnts_std[vx][0]
                        vex_feat["obj_y_std"] = map_line_pnts_std[vx][1]
                        vex_feat["obj_z_std"] = map_line_pnts_std[vx][2]
                        vex_feat["img_x"] = map_line_pnts_img[vx][0]
                        vex_feat["img_y"] = map_line_pnts_img[vx][1]
                        vex_feat["max_evec_dir"] = map_line_pnts_evec_dir[vx]
                        vex_feat["pval"] = map_line_pnts_pval[vx]
                        vx_feats.append(vex_feat)
                    
                    self.vex_lyr.dataProvider().addFeatures(vx_feats)
                    self.vex_lyr.commitChanges()
                    self.vex_lyr.triggerRepaint()
                    
                    self.map_canvas.refresh()
                        
            self.is_drawing = False
            self.rubberMap.reset()
            self.rubberMap_h = []
            self.rubberMap_std = []
            self.rubberMap_img = []
            self.rubberMap_evec_dir = []
            self.rubberMap_pval = []
            
            self.rubberImg.reset()
            self.rubberImg_prev.reset()
            self.rubberMap_prev.reset()
                
    def canvasMoveEvent(self, e):
        pos = self.toMapCoordinates(e.pos())
        mx, my = float(pos.x()), float(pos.y())
        
        if (mx >= 0) and (mx <= self.camera.img_w):
            if (my <= 0) and (my >= self.camera.img_h*(-1)):
                
                if self.is_drawing:
                    if self.rubberImg_prev.numberOfVertices() == 2:
                        self.rubberImg_prev.removeLastPoint()
                    self.rubberImg_prev.addPoint(QgsPointXY(mx, my), True)
                
                rays = smpls_to_rays(self.smpls, self.dir2pnts, mx, my, self.camera.min_d_mono, self.min_xyz)
                o3d_rays = o3d.core.Tensor(rays, dtype=o3d.core.Dtype.Float32)
                
                ans = self.ray_scene.cast_rays(o3d_rays)
                
                ans_dist = ans["t_hit"].numpy().ravel()
                ans_valid = np.isfinite(ans_dist)
                                                                                                    
                if ans_valid[0]:
                                            
                    ans_coords = rays[:, :3] + rays[:, 3:] * ans_dist.reshape(-1, 1)
                    ans_coords = ans_coords[ans_valid, :]                
                    # ans_covar = np.cov(ans_coords, rowvar=False)
                    # xyz_std = np.sqrt(np.diag(ans_covar))
                                        
                    obj_coord = ans_coords[0, :] + self.min_xyz
                    
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
        self.rubberMap_std = []
        self.rubberMap_img = []
        self.rubberMap_evec_dir = []
        self.rubberMap_pval = []
        
        self.rubberMap.reset()
        self.rubberMap_prev.reset()
        
        self.rubberRay.addPoint(QgsPointXY(self.camera.prc[0], self.camera.prc[1]))
        
    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.rubberRay.reset()
        
        self.rubberImg.reset()
        self.rubberImg_prev.reset()
        
        self.rubberMap_h = []
        self.rubberMap_std = []
        self.rubberMap_img = []
        self.rubberMap_evec_dir = []
        self.rubberMap_pval = []
        
        self.rubberMap.reset()
        self.rubberMap_prev.reset()
        
        self.deactivated.emit()