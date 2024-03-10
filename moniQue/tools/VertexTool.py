from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker, QgsMessageBar
from qgis.core import Qgis, QgsPointXY, QgsRectangle, QgsWkbTypes, QgsPointLocator, QgsPoint
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import open3d as o3d

class VertexTool(QgsMapTool):
    
    def __init__(self, img_canvas, map_canvas):
        self.img_canvas = img_canvas
        self.map_canvas = map_canvas
        self.msg_bar = QgsMessageBar(self.img_canvas)
        
        QgsMapTool.__init__(self, self.img_canvas)
        
        # results = loc.edgesInRect(QgsPoint(2.0, 2.0), 0.5)
        
        self.sel_rect = QgsRubberBand(self.img_canvas, QgsWkbTypes.PolygonGeometry)
        self.sel_rect.setFillColor(QColor(255, 0, 0, 50))
        self.sel_rect.setStrokeColor(Qt.red)        
        self.sel_rect.setWidth(1)
        self.sel_rect.reset()
        
        self.curr_vm_img = QgsVertexMarker(self.img_canvas)
        self.curr_vm_img.setColor(Qt.red)
        self.curr_vm_img.setIconType(4)
        self.curr_vm_img.setIconSize(10)
        self.curr_vm_img.setPenWidth(2)
        self.curr_vm_img.hide()
        
        self.move_rubber_img = QgsRubberBand(self.img_canvas, QgsWkbTypes.LineGeometry)
        self.move_rubber_img.setStrokeColor(Qt.red)        
        self.move_rubber_img.setWidth(1)
        self.move_rubber_img.setLineStyle(Qt.DashLine)
        self.move_rubber_img.reset()
        
        self.move_rubber_map = QgsRubberBand(self.map_canvas, QgsWkbTypes.LineGeometry)
        self.move_rubber_map.setStrokeColor(Qt.red)        
        self.move_rubber_map.setWidth(1)
        self.move_rubber_map.setLineStyle(Qt.DashLine)
        self.move_rubber_map.reset()
        
        self.move_vm_img = QgsVertexMarker(self.img_canvas)
        self.move_vm_img.setColor(Qt.red)
        self.move_vm_img.setIconType(4)
        self.move_vm_img.setIconSize(10)
        self.move_vm_img.setPenWidth(2)
        self.move_vm_img.hide()
        
        self.curr_vm_map = QgsVertexMarker(self.map_canvas)
        self.curr_vm_map.setColor(Qt.red)
        self.curr_vm_map.setIconType(4)
        self.curr_vm_map.setIconSize(10)
        self.curr_vm_map.setPenWidth(2)
        self.curr_vm_map.hide()
        
        self.move_vm_map = QgsVertexMarker(self.map_canvas)
        self.move_vm_map.setColor(Qt.red)
        self.move_vm_map.setIconType(4)
        self.move_vm_map.setIconSize(10)
        self.move_vm_map.setPenWidth(2)
        self.move_vm_map.hide()
        
        self.sel_vm_img = []
        self.sel_vm_map = []
        self.sel_vm_ix = []
        
        self.sel_adjacent_vx_ix = []
        
        self.sel_vertex_tolerance = 10
        
        self.reset()

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.isSelectedPoint = False
        self.sel_rect.reset(QgsWkbTypes.PolygonGeometry)
        self.sel_adjacent_vx_ix = []
        
    def set_layers(self, img_lyr, map_lyr):
        self.img_lyr = img_lyr
        self.map_lyr = map_lyr
    
    def canvasDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
             match = self.pnt_loc.nearestEdge(self.toMapCoordinates(e.pos()), 500)
             if match.hasEdge:
                
                match_fid = match.featureId()
                match_vertex_ix = match.vertexIndex()
                
                self.sel_vm_ix.append([match_fid, -1])
                # adjacent_vx_ix = self.img_lyr.getGeometry(match_fid).adjacentVertices(match_vertex_ix)
                
                self.sel_adjacent_vx_ix = [match_vertex_ix, match_vertex_ix + 1]
                self.isSelectedPoint = True
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete:
            if self.sel_vm_ix:
                
                self.map_lyr.startEditing()
                self.img_lyr.startEditing()
                
                if len(self.sel_vm_ix) > 1:
                    self.sel_vm_ix.sort(key=lambda x: int(x[1]), reverse=True)

                sel_fid_ids = {}
                
                for m in self.sel_vm_ix:
                    m_fid = m[0]
                    m_vix = m[1]
                    
                    if m_fid not in sel_fid_ids:
                        sel_fid_ids[m_fid] = [m_vix]
                    
                    else:
                        sel_fid_ids[m_fid].append(m_vix)
                
                for fid, vix_list in sel_fid_ids.items():
                    fid_nr_vix = len(list(self.map_lyr.getFeature(fid).geometry().vertices()))
                    
                    #only delete vertices if 2 vertices remain; otherwise the geometry would not be a valid linestring
                    if fid_nr_vix - len(vix_list) < 2: 
                        self.msg_bar.pushMessage("Info", "%i not edited. Too many vertices selected for deletion." % (fid_nr_vix), level=Qgis.Info, duration=3)
                    else:
                        for vix in vix_list:                
                            self.map_lyr.deleteVertex(m_fid, vix)
                            self.img_lyr.deleteVertex(m_fid, vix)

                self.map_lyr.commitChanges()
                self.img_lyr.commitChanges()
                self.clear_markers()
               
        else:
            pass #no markers selected
         
    def canvasPressEvent(self, e):
        
        if e.button() == Qt.LeftButton:
            
            if not self.isSelectedPoint:
            
                self.clear_markers()
                
                match = self.pnt_loc.nearestVertex(self.toMapCoordinates(e.pos()), self.sel_vertex_tolerance)
                
                if match.hasVertex(): 
                    
                    vm = QgsVertexMarker(self.img_canvas)
                    vm.setCenter(match.point())
                    vm.setColor(Qt.blue)
                    vm.setIconType(4)
                    vm.setIconSize(10)
                    vm.setPenWidth(2)
                    vm.show()
                    self.sel_vm_img.append(vm)
                    
                    match_fid = match.featureId()
                    match_vertex_ix = match.vertexIndex()
                    match_vertex_pos_map = self.map_lyr.getGeometry(match_fid).vertexAt(match_vertex_ix)
                    
                    vm = QgsVertexMarker(self.map_canvas)
                    vm.setCenter(QgsPointXY(match_vertex_pos_map))
                    vm.setColor(Qt.blue)
                    vm.setIconType(4)
                    vm.setIconSize(10)
                    vm.setPenWidth(2)
                    vm.show()
                    self.sel_vm_map.append(vm)
                    
                    self.sel_vm_ix.append([match_fid, match_vertex_ix])
                    self.isSelectedPoint = True
                    
                    adjacent_vx_ix = self.img_lyr.getGeometry(match_fid).adjacentVertices(match_vertex_ix)
                    self.sel_adjacent_vx_ix = adjacent_vx_ix
                    
                else:
                    self.startPoint = self.toMapCoordinates(e.pos())
                    self.endPoint = self.startPoint
                    self.isEmittingPoint = True
                    self.showRect(self.startPoint, self.endPoint)
            else:
                
                obj_coord = self.monoplot(e)
                print(obj_coord)
                
                if obj_coord is not None:
                
                    self.img_lyr.startEditing()
                    self.map_lyr.startEditing()
                    
                    if self.sel_vm_ix[0][1] == -1: #if this index is -1 we are in inserting mode initated by double press
                        
                        mouse_pos = self.toMapCoordinates(e.pos())
                        self.img_lyr.insertVertex(mouse_pos.x(), mouse_pos.y(), self.sel_vm_ix[0][0], self.sel_adjacent_vx_ix[1])
                        self.map_lyr.insertVertex(obj_coord[0], obj_coord[1], self.sel_vm_ix[0][0], self.sel_adjacent_vx_ix[1])
                        
                    else:
                    
                        self.img_lyr.moveVertexV2(QgsPoint(self.toMapCoordinates(e.pos())), self.sel_vm_ix[0][0], self.sel_vm_ix[0][1])
                        self.map_lyr.moveVertexV2(QgsPoint(obj_coord[0], obj_coord[1]), self.sel_vm_ix[0][0], self.sel_vm_ix[0][1])
                    
                    self.img_lyr.commitChanges()
                    self.map_lyr.commitChanges()
                
                self.clear_markers()
                self.isSelectedPoint = False
                
        elif e.button() == Qt.RightButton:
            self.clear_markers()
            self.isSelectedPoint = False

    def clear_markers(self):
        #clear old selected vertex markers
        if self.sel_vm_img:
            for m in self.sel_vm_img:
                self.img_canvas.scene().removeItem(m)
        
        if self.sel_vm_map:
            for m in self.sel_vm_map:
                self.map_canvas.scene().removeItem(m)
        
        self.move_vm_img.hide()
        self.move_vm_map.hide()    
        self.curr_vm_img.hide()
        self.curr_vm_map.hide()
        
        self.sel_vm_ix = []        
        self.sel_vm_img = []
        self.sel_vm_map = []
        
        self.move_rubber_img.reset()
        self.move_rubber_map.reset()
        
    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        r = self.rectangle()
        
        if r is not None:
            
            self.clear_markers()
            
            pnts_in_rect = self.pnt_loc.verticesInRect(r)
            
            if pnts_in_rect:
                for pnt in pnts_in_rect:
                                        
                    vm = QgsVertexMarker(self.img_canvas)
                    vm.setCenter(pnt.point())
                    vm.setColor(Qt.blue)
                    vm.setIconType(4)
                    vm.setIconSize(10)
                    vm.setPenWidth(2)
                    vm.show()
                    self.sel_vm_img.append(vm)
                    
                    match_fid = pnt.featureId()
                    match_vertex_ix = pnt.vertexIndex()
                    match_vertex_pos_map = self.map_lyr.getGeometry(match_fid).vertexAt(match_vertex_ix)
                    
                    vm = QgsVertexMarker(self.map_canvas)
                    vm.setCenter(QgsPointXY(match_vertex_pos_map))
                    vm.setColor(Qt.blue)
                    vm.setIconType(4)
                    vm.setIconSize(10)
                    vm.setPenWidth(2)
                    vm.show()
                    self.sel_vm_map.append(vm)
                    
                    self.sel_vm_ix.append([match_fid, match_vertex_ix])

                    
            self.reset() #after the vertices have been selected, reset the recangle
                
    def canvasMoveEvent(self, e):
        
        if not self.isEmittingPoint:
            if not self.isSelectedPoint:
                match = self.pnt_loc.nearestVertex(self.toMapCoordinates(e.pos()), self.sel_vertex_tolerance)
                if match.hasVertex():
                                
                    self.curr_vm_img.setCenter(match.point())
                    self.curr_vm_img.show()
                    
                    match_fid = match.featureId()
                    match_vertex_ix = match.vertexIndex()
                    match_vertex_pos_map = self.map_lyr.getGeometry(match_fid).vertexAt(match_vertex_ix)
                    self.curr_vm_map.setCenter(QgsPointXY(match_vertex_pos_map))
                    self.curr_vm_map.show()               
                    
                else:
                    self.curr_vm_img.hide()
                    self.curr_vm_map.hide()
            else:
                
                self.move_rubber_img.reset()
                self.move_rubber_map.reset()
                
                curr_mouse_pos = self.toMapCoordinates(e.pos())
                obj_coord = self.monoplot(e)
                
                print(obj_coord)
                
                if obj_coord is not None:
                    
                    obj_pnt = QgsPointXY(obj_coord[0], obj_coord[1])
                    
                    self.move_vm_img.setCenter(curr_mouse_pos)
                    self.move_vm_img.show()
                    
                    self.move_vm_map.setCenter(obj_pnt)
                    self.move_vm_map.show()
                    
                    sel_vx_geom_img = self.img_lyr.getGeometry(self.sel_vm_ix[0][0])
                    sel_vx_geom_map = self.map_lyr.getGeometry(self.sel_vm_ix[0][0])
                    
                    if self.sel_adjacent_vx_ix[0] == -1:
                        self.move_rubber_img.addPoint(curr_mouse_pos)
                        self.move_rubber_img.addPoint(QgsPointXY(sel_vx_geom_img.vertexAt(self.sel_adjacent_vx_ix[1])), True)
                        
                        self.move_rubber_map.addPoint(obj_pnt)
                        self.move_rubber_map.addPoint(QgsPointXY(sel_vx_geom_map.vertexAt(self.sel_adjacent_vx_ix[1])), True)
                        
                    elif self.sel_adjacent_vx_ix[1] == -1:
                        self.move_rubber_img.addPoint(curr_mouse_pos)
                        self.move_rubber_img.addPoint(QgsPointXY(sel_vx_geom_img.vertexAt(self.sel_adjacent_vx_ix[0])), True)
                        
                        self.move_rubber_map.addPoint(obj_pnt)
                        self.move_rubber_map.addPoint(QgsPointXY(sel_vx_geom_map.vertexAt(self.sel_adjacent_vx_ix[0])), True)
                        
                    else:
                        self.move_rubber_img.addPoint(QgsPointXY(sel_vx_geom_img.vertexAt(self.sel_adjacent_vx_ix[0])))
                        self.move_rubber_img.addPoint(curr_mouse_pos)
                        self.move_rubber_img.addPoint(QgsPointXY(sel_vx_geom_img.vertexAt(self.sel_adjacent_vx_ix[1])), True)
                        
                        self.move_rubber_map.addPoint(QgsPointXY(sel_vx_geom_map.vertexAt(self.sel_adjacent_vx_ix[0])))
                        self.move_rubber_map.addPoint(obj_pnt)
                        self.move_rubber_map.addPoint(QgsPointXY(sel_vx_geom_map.vertexAt(self.sel_adjacent_vx_ix[1])), True)
                
                    self.move_rubber_img.show()
                    self.move_rubber_map.show()
                
        else:
            self.endPoint = self.toMapCoordinates(e.pos())
            self.showRect(self.startPoint, self.endPoint)

    def set_layers(self, img_lyr, map_lyr):
        self.img_lyr = img_lyr
        self.map_lyr = map_lyr
        self.pnt_loc = QgsPointLocator(self.img_lyr)
        
    def showRect(self, startPoint, endPoint):
        self.sel_rect.reset(QgsWkbTypes.PolygonGeometry)
        
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        point1 = QgsPointXY(startPoint.x(), startPoint.y())
        point2 = QgsPointXY(startPoint.x(), endPoint.y())
        point3 = QgsPointXY(endPoint.x(), endPoint.y())
        point4 = QgsPointXY(endPoint.x(), startPoint.y())

        self.sel_rect.addPoint(point1, False)
        self.sel_rect.addPoint(point2, False)
        self.sel_rect.addPoint(point3, False)
        self.sel_rect.addPoint(point4, False)  
        self.sel_rect.closePoints(True)# true to update canvas
        self.sel_rect.show()

    def rectangle(self):
        if self.startPoint is None or self.endPoint is None:
            return None
        elif (self.startPoint.x() == self.endPoint.x() or \
            self.startPoint.y() == self.endPoint.y()):
            return None

        return QgsRectangle(self.startPoint, self.endPoint)

    def set_scene(self, scene):
        self.ray_scene = scene
    
    def set_camera(self, camera):
        self.camera = camera
    
    def set_minxyz(self, min_xyz):
        self.min_xyz = min_xyz
    
    def monoplot(self, e):
        pos = self.toMapCoordinates(e.pos())
    
        mx, my = float(pos.x()), float(pos.y())
        
        if (mx >= 0) and (mx <= self.camera.img_w):
            if (my <= 0) and (my >= self.camera.img_h*(-1)):
        
                ray = self.camera.ray(img_x=mx, img_y=my)
                ray[0, :3] -= self.min_xyz
                
                o3d_ray = o3d.core.Tensor(ray, dtype=o3d.core.Dtype.Float32)
                ans = self.ray_scene.cast_rays(o3d_ray)
                
                if ans['t_hit'].isfinite():
                    obj_coord = o3d_ray[0, :3] + o3d_ray[0, 3:]*ans['t_hit'].reshape((-1,1))
                    obj_coord = obj_coord.numpy().ravel()
                    obj_coord[:3] += self.min_xyz
                    return obj_coord
                else:
                    return None
            else:
                return None
        else:
            return None
                    
    def deactivate(self):
        
        self.clear_markers()
        self.reset()
        QgsMapTool.deactivate(self)
        self.deactivated.emit()