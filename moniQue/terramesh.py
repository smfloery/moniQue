import open3d as o3d
import numpy as np
from osgeo import gdal
from pymartini import Martini
import os

gdal.UseExceptions()
 
def load_geoimg(img_path, nr_bands=3, band_dtype=np.uint8):

    ds = gdal.Open(img_path)
    
    ds_w = ds.RasterXSize
    ds_h = ds.RasterYSize
    
    ds_gt = ds.GetGeoTransform()
    ds_geo = ds.GetProjection()
    
    band_arr = np.zeros((ds_h, ds_w, nr_bands), dtype=band_dtype)
    
    for i in range(nr_bands):
        curr_band = ds.GetRasterBand(i+1)
        curr_arr = curr_band.ReadAsArray().astype(band_dtype)
        band_arr[:, :, i] = curr_arr
    
    ds_nd = ds.GetRasterBand(1).GetNoDataValue()
    
    return band_arr.squeeze(), ds_gt, ds_geo, ds_h, ds_w, ds_nd

def geo2px(coords, gt):
    feat_vx_col = np.floor((coords[:, 0] - gt[0]) / gt[1]).astype(int)
    feat_vx_row = np.floor((coords[:, 1] - gt[3]) / gt[5]).astype(int)
    return np.hstack((feat_vx_row.reshape(-1, 1), feat_vx_col.reshape(-1, 1)))

def px2geo(coords, gt, pixel_shift=True):   
    # xoffset, px_w, rot1, yoffset, rot2, px_h = gt
    # supposing x and y are your pixel coordinate this 
    # is how to get the coordinate in space.
    pos_x = gt[1] * coords[:, 1] + gt[2] * coords[:, 0] + gt[0]
    pos_y = gt[4] * coords[:, 1] + gt[5] * coords[:, 0] + gt[3]

    # shift to the center of the pixel
    if pixel_shift:
        pos_x += gt[1] * 0.5
        pos_y += gt[5] * 0.5
    
    return np.hstack((pos_x.reshape(-1, 1), pos_y.reshape(-1, 1)))

def mesh_from_array(arr_h, arr_w):
                
    vix = np.arange(arr_h * arr_w).reshape(arr_h, arr_w)
    
    tl = vix[0:-1, 0:-1].ravel()
    tr = vix[0:-1:, 1:].ravel()
    ll = vix[1:, 0:-1].ravel()
    lr = vix[1:, 1:].ravel()
    
    face_tl = np.hstack((tl.reshape(-1, 1), 
                        tr.reshape(-1, 1), 
                        ll.reshape(-1, 1)))
    face_lr = np.hstack((tr.reshape(-1, 1),
                        lr.reshape(-1, 1),
                        ll.reshape(-1, 1)))
    
    faces = np.vstack((face_tl, face_lr))
    
    return faces.astype(np.uint32)

class MeshTile:
    def __init__(self, vertices=None, triangles=None, tile_arr=None, tile_gt=None, tile_size=None, bounds_local=None, bounds_geo=None):
        if vertices is None:
            raise ValueError("Vertices must be provided.")
        if triangles is None:
            raise ValueError("Triangles must be provided.")
        
        self.vertices = vertices
        self.triangles = triangles
        self.tile_size = tile_size
        self.bbox_px = bounds_local
        self.bbox_geo = bounds_geo
        self.tile_arr = tile_arr
        self.tile_gt = tile_gt
        
        self.nr_vertices = len(self.vertices)
        self.nr_triangles = len(self.triangles)
        
        self.extract_boundaries()
        
    def __str__(self):
        return "MeshTile(vertices=%i, triangles=%i)" % (self.nr_vertices, self.nr_triangles)
    
    def __repr__(self):
        return "MeshTile(vertices=%i, triangles=%i)" % (self.nr_vertices, self.nr_triangles)
    
    def extract_boundaries(self):
        
        # bdry_coords = self.vertices.reshape(-1, 2)[bdry_vix, :]
        lix = np.argwhere(self.vertices[:, 1] == 0).ravel()
        rix = np.argwhere(self.vertices[:, 1] == self.tile_size-1).ravel()
        tix = np.argwhere(self.vertices[:, 0] == 0).ravel()
        bix = np.argwhere(self.vertices[:, 0] == self.tile_size-1).ravel()
        
        lix_asc = np.argsort(self.vertices[lix, :][:, 0]).ravel()
        rix_asc = np.argsort(self.vertices[rix, :][:, 0]).ravel()
        tix_asc = np.argsort(self.vertices[tix, :][:, 1]).ravel()
        bix_asc = np.argsort(self.vertices[bix, :][:, 1]).ravel()
        
        l_vix = lix[lix_asc]
        r_vix = rix[rix_asc]
        t_vix = tix[tix_asc]
        b_vix = bix[bix_asc]
        
        assert len(np.unique(l_vix)) == len(l_vix)
        assert len(np.unique(r_vix)) == len(r_vix)
        assert len(np.unique(t_vix)) == len(t_vix)
        assert len(np.unique(b_vix)) == len(b_vix)
        
        #LEFT BDRY
        #get indices of triangles containing border vertices
        l_tix = np.unique(np.argwhere(np.in1d(self.triangles.ravel(), l_vix)) // 3).ravel()
        
        #extract columns and rows of border vertex; for each triangle the coordinates are in one row
        l_tix_vertex_coord = self.vertices[self.triangles[l_tix, :].ravel(), :].reshape(-1, 6)
        
        #for l_border use the column to indicate which are valid border triangles; Those triangles
        #must contain two vertices where the column is 0; for top or bottom use [0, 2, 4]
        l_tix_valid_ix = np.count_nonzero(l_tix_vertex_coord[:, [1, 3, 5]] == 0, axis=1) == 2
        l_tix = l_tix[l_tix_valid_ix]
        
        #sort the valid triangle ids by ascending maximum row of the border vertices; for top or bottom use cols: [1, 3, 5]
        l_tix_asc = np.argsort(np.max(l_tix_vertex_coord[:, [0, 2, 4]], axis=1)[l_tix_valid_ix])
        
        l_tix = l_tix[l_tix_asc]
        
        self.l_vix = l_vix
        self.l_tix = l_tix
        
        #RIGHT BDRY
        #get indices of triangles containing border vertices
        r_tix = np.unique(np.argwhere(np.in1d(self.triangles.ravel(), r_vix)) // 3).ravel()
        
        #extract columns and rows of border vertex; for each triangle the coordinates are in one row
        r_tix_vertex_coord = self.vertices[self.triangles[r_tix, :].ravel(), :].reshape(-1, 6)
        
        #for r_border use the column to indicate which are valid border triangles; Those triangles
        #must contain two vertices where the column is 0; for top or bottom use [0, 2, 4]
        r_tix_valid_ix = np.count_nonzero(r_tix_vertex_coord[:, [1, 3, 5]] == self.tile_size-1, axis=1) == 2
        r_tix = r_tix[r_tix_valid_ix]
        
        #sort the valid triangle ids by ascending maximum row of the border vertices; for top or bottom use cols: [1, 3, 5]
        r_tix_asc = np.argsort(np.max(r_tix_vertex_coord[:, [0, 2, 4]], axis=1)[r_tix_valid_ix])
        
        r_tix = r_tix[r_tix_asc]
        
        self.r_vix = r_vix
        self.r_tix = r_tix

        #TOP BDRY
        #get indices of triangles containing border vertices
        t_tix = np.unique(np.argwhere(np.in1d(self.triangles.ravel(), t_vix)) // 3).ravel()
        
        #extract columns and rows of border vertex; for each triangle the coordinates are in one row
        t_tix_vertex_coord = self.vertices[self.triangles[t_tix, :].ravel(), :].reshape(-1, 6)
        
        #for t_border use the column to indicate which are valid border triangles; Those triangles
        #must contain two vertices where the column is 0; for top or bottom use [0, 2, 4]
        t_tix_valid_ix = np.count_nonzero(t_tix_vertex_coord[:, [0, 2, 4]] == 0, axis=1) == 2
        t_tix = t_tix[t_tix_valid_ix]
        
        #sort the valid triangle ids by ascending maximum row of the border vertices; for top or bottom use cols: [1, 3, 5]
        t_tix_asc = np.argsort(np.max(t_tix_vertex_coord[:, [1, 3, 5]], axis=1)[t_tix_valid_ix])
        
        t_tix = t_tix[t_tix_asc]
        
        self.t_vix = t_vix
        self.t_tix = t_tix

        #RIGHT BDRY
        #get indices of triangles containing border vertices
        b_tix = np.unique(np.argwhere(np.in1d(self.triangles.ravel(), b_vix)) // 3).ravel()
        
        #extract columns and rows of border vertex; for each triangle the coordinates are in one row
        b_tix_vertex_coord = self.vertices[self.triangles[b_tix, :].ravel(), :].reshape(-1, 6)
        
        #for b_border use the column to indicate which are valid border triangles; Those triangles
        #must contain two vertices where the column is 0; for top or bottom use [0, 2, 4]
        b_tix_valid_ix = np.count_nonzero(b_tix_vertex_coord[:, [0, 2, 4]] == self.tile_size-1, axis=1) == 2
        b_tix = b_tix[b_tix_valid_ix]
        
        #sort the valid triangle ids by ascending maximum row of the border vertices; for top or bottom use cols: [1, 3, 5]
        b_tix_asc = np.argsort(np.max(b_tix_vertex_coord[:, [1, 3, 5]], axis=1)[b_tix_valid_ix])
        
        b_tix = b_tix[b_tix_asc]
        
        self.b_vix = b_vix
        self.b_tix = b_tix

class MeshGrid:
    
    def __init__(self, path=None, tile_size=256, max_error=1):
        
        if path is None:
            raise ValueError("Path to the .tif must be provided.")
        if not os.path.exists(path):
            raise FileNotFoundError("Not a valid path.")
        
        #TODO check if tile_size is 2**n+1
         
        self.path = path
        self.tile_size = tile_size
        self.max_error = max_error
        self.data = {}
        
        self.build()
        
    def build(self):
        dgm_arr, dgm_gt, dgm_prj, dgm_h, dgm_w, dgm_nd = load_geoimg(self.path, nr_bands=1, band_dtype=np.float32)        
        dgm_arr[dgm_arr == dgm_nd] = -1
            
        r_steps = np.arange(0, dgm_h, self.tile_size)
        c_steps = np.arange(0, dgm_w, self.tile_size)
        
        if r_steps[-1] != dgm_h:
            r_steps = np.append(r_steps, dgm_h)
        
        if c_steps[-1] != dgm_w:
            c_steps = np.append(c_steps, dgm_w)
        
        self.nr_cols = len(c_steps)
        self.nr_rows = len(r_steps)
        
        #as we extract the dgm with 1 px overlay we adjust the tilesize after we calcutate the splits
        self.tile_size += 1
        martini = Martini(self.tile_size)
        
        for rx in range(len(r_steps)-1):
            for cx in range(len(c_steps)-1):
        # for rx in range(len(r_steps)-1):
        #     for cx in range(len(c_steps)-1):
                
                min_c = c_steps[cx]
                max_c = c_steps[cx+1]+1 #1px overlap; Guranteees that the tilesize is 2**n+1
                
                min_r = r_steps[rx]
                max_r = r_steps[rx+1]+1 #1px overlap; Guranteees that the tilesize is 2**n+1
                
                bounds_geo = px2geo(np.array([[min_r, min_c], 
                                              [max_r, max_c]]), gt=dgm_gt)
                
                min_x_geo = np.min(bounds_geo[:, 0])
                max_y_geo = np.max(bounds_geo[:, 1])
                
                tile_gt = (min_x_geo, dgm_gt[1], dgm_gt[2], max_y_geo, dgm_gt[4], dgm_gt[5])
                tile_bbox = list(bounds_geo.ravel())
                
                tile_arr = dgm_arr[min_r:max_r, min_c:max_c]
                tile_h, tile_w = np.shape(tile_arr)
                
                if tile_h != self.tile_size:
                    tile_arr = np.pad(tile_arr, pad_width=((0,self.tile_size-tile_h),(0,0)), mode="constant", constant_values=-1)
                
                if tile_w != self.tile_size:
                    tile_arr = np.pad(tile_arr, pad_width=((0,0),(0,self.tile_size-tile_w),), mode="constant", constant_values=-1)
                
                assert np.shape(tile_arr) == (self.tile_size, self.tile_size)
                self.tile_size = np.shape(tile_arr)[0]
                
                tile = martini.create_tile(tile_arr)
                vertices, triangles = tile.get_mesh(self.max_error)
                
                #martini returns vertices as col/row; we further use row/col; hence, np.fliplr
                vertices = np.fliplr(vertices.reshape(-1, 2))
                triangles = triangles.reshape(-1, 3)
                                
                vert_h = tile_arr[vertices[:, 0], vertices[:, 1]]
                tris_vert_h = vert_h[triangles.ravel()].reshape(-1, 3)
                 
                valid_tix = np.nonzero(~np.any(tris_vert_h==-1, axis=1))[0]
                if len(valid_tix) == 0:
                    continue
                
                valid_tris = triangles[valid_tix, :]
                valid_tris_vix, valid_tris_vix_ix, valid_tris_vix_inv = np.unique(valid_tris, return_inverse=True, return_index=True)
                #inv for creating new ids of triangles
                # ix for extracting the corresponding vertices
                new_tris_vix = np.arange(len(valid_tris_vix))
                
                triangles = new_tris_vix[valid_tris_vix_inv].reshape(-1, 3)
                vertices = vertices[valid_tris_vix, :]               
                
                mesh_tile = MeshTile(vertices=vertices, 
                                     triangles=triangles, 
                                     tile_size=self.tile_size,
                                     tile_gt=tile_gt,
                                     tile_arr=tile_arr,
                                     bounds_local=[min_c, min_r, max_c, max_r],
                                     bounds_geo=tile_bbox)
                
                self.data["%i_%i" % (rx, cx)] = mesh_tile

    def update_tid(self, tid, new_verts, new_tris, pop_tris):
                    
        self.data[tid].vertices = np.vstack((self.data[tid].vertices, np.array(new_verts)))
    
        upd_triangles = np.delete(self.data[tid].triangles, pop_tris, axis=0)
        self.data[tid].triangles = np.vstack((upd_triangles, np.array(new_tris))).astype(np.uint32)
        
        self.data[tid].extract_boundaries()
        
        self.data[tid].nr_vertices = np.shape(self.data[tid].vertices)[0]
        self.data[tid].nr_triangles = np.shape(self.data[tid].triangles)[0]
                        
    def snap(self, tid, missing_vix_coords, mode=None):
        
        missing_vix_coords = missing_vix_coords.astype(np.uint32)
        
        if mode == "left":
            bdry_coords = self.data[tid].vertices[self.data[tid].r_vix, :]
            bdry_trix = self.data[tid].r_tix
            bdry_const = self.tile_size-1
            bix = 0
            not_bix = 1
        elif mode == "right":
            bdry_coords = self.data[tid].vertices[self.data[tid].l_vix, :]
            bdry_trix = self.data[tid].l_tix
            bdry_const = 0
            bix = 0
            not_bix = 1
        elif mode == "top":
            bdry_coords = self.data[tid].vertices[self.data[tid].b_vix, :]
            bdry_trix = self.data[tid].b_tix
            bdry_const = self.tile_size-1
            bix = 1
            not_bix = 0
        elif mode == "bottom":
            bdry_coords = self.data[tid].vertices[self.data[tid].t_vix, :]
            bdry_trix = self.data[tid].t_tix
            bdry_const = 0
            bix = 1
            not_bix = 0
        else:
            raise ValueError("%s not supported." % (mode))
        
        #six is the index where coordinates of next must be inserted into curr to maintain order
        missing_vix_coords_six = np.searchsorted(bdry_coords[:, bix].ravel(), missing_vix_coords, side="left")-1
        uq_six, uq_six_inv = np.unique(missing_vix_coords_six, return_inverse=True)
        
        uq_six = uq_six[uq_six < len(bdry_trix)]            #sometimes the other border is longer than the current one; hence, clip those ranges
        uq_six = uq_six[uq_six >= 0]
        
        if len(uq_six) == 0:
            return [], [], []

        max_vix = len(self.data[tid].vertices) - 1
        
        new_verts = []
        new_tris = []
        pop_tris = []
        
        for ix, six in enumerate(uq_six):
                                
            miss_coords = missing_vix_coords[np.nonzero(uq_six_inv == ix)[0]]
            miss_vix = np.arange(max_vix+1, max_vix+1+len(miss_coords))
            
            for coord in miss_coords:                               
                if mode in ["left", "right"]:
                    new_verts.append([coord, bdry_const])#, coord_h])
                elif mode in ["top", "bottom"]:
                    new_verts.append([bdry_const, coord])#, coord_h])

            trix_insert = bdry_trix[six]                                            #index of the triangle where the miss_coords will be inserted
            trix_insert_vix = self.data[tid].triangles[trix_insert, :]              #vertex indices of the triangle
            trix_insert_vix_coords = self.data[tid].vertices[trix_insert_vix, :]    #vertex coords of the triangle
            
            pop_tris.append(trix_insert)
            
            #get indixes within each triangle corresponding to the bdry and not ("norm");
            #while use pymartini appaers that bdry edges are always the first two vertices this might
            #not be always true;
            bdry_ix = np.argwhere(trix_insert_vix_coords[:, not_bix] == bdry_const).ravel()
            assert len(bdry_ix) == 2, "No valid boundary triangles for %s (%s)." % (tid, mode)
            
            norm_ix = np.setdiff1d(np.arange(3), bdry_ix)
            
            bdry_coords_ext = np.hstack((trix_insert_vix_coords[bdry_ix, bix], miss_coords))
            bdry_vix = np.hstack((trix_insert_vix[bdry_ix], miss_vix))
            
            norm_vix = trix_insert_vix[norm_ix]
            
            bdry_coords_ext_ascix = np.argsort(bdry_coords_ext)
            
            bdry_coords_ext = bdry_coords_ext[bdry_coords_ext_ascix]
            bdry_vix = bdry_vix[bdry_coords_ext_ascix]
            
            for bx in range(len(bdry_coords_ext)-1):
                if mode == "right" or mode == "top":
                    bx_tri = [bdry_vix[bx], bdry_vix[bx+1], norm_vix[0]]
                elif mode == "left" or mode == "bottom":
                    bx_tri = [bdry_vix[bx], norm_vix[0], bdry_vix[bx+1]]
                new_tris.append(bx_tri)

            max_vix = miss_vix[-1]

        return new_verts, new_tris, pop_tris
    
    def snap_boundaries_left_right(self, left_tid, right_tid):
                                   
        #current boundary vertices coordinates | next boundary vertices coordinates
        left_bv_coords = self.data[left_tid].vertices[self.data[left_tid].r_vix, :]
        right_bv_coords = self.data[right_tid].vertices[self.data[right_tid].l_vix, :]
        
        # # #vertices which are not on the border of the one tile but on the other; 
        # # #we use the column coords of the vertices as indicator for left/right case: 
        # # setdiff1d(a,b) - returns the values of a not in b; to get the indices we further need to use isin
        right_missing_vix_coords = np.setdiff1d(left_bv_coords[:, 0], right_bv_coords[:, 0])  #coords missing in next but in curr
        left_missing_vix_coords = np.setdiff1d(right_bv_coords[:, 0], left_bv_coords[:, 0])  #coords missing in curr but in next
        
        l_new_verts, l_new_tris, l_pop_tris = self.snap(left_tid, left_missing_vix_coords, mode="left")
        r_new_verts, r_new_tris, r_pop_tris = self.snap(right_tid, right_missing_vix_coords, mode="right")
        
        if len(l_new_verts) > 0:
            self.update_tid(left_tid, l_new_verts, l_new_tris, l_pop_tris)
        if len(r_new_verts) > 0:
            self.update_tid(right_tid, r_new_verts, r_new_tris, r_pop_tris)
    
    def snap_boundaries_top_bottom(self, top_tid, bottom_tid):
                                   
        #current boundary vertices coordinates | next boundary vertices coordinates
        top_bv_coords = self.data[top_tid].vertices[self.data[top_tid].b_vix, :]
        bot_bv_coords = self.data[bottom_tid].vertices[self.data[bottom_tid].t_vix, :]
        
        # # #vertices which are not on the border of the one tile but on the other; 
        # # #we use the column coords of the vertices as indicator for left/right case: 
        # # setdiff1d(a,b) - returns the values of a not in b; to get the indices we further need to use isin
        top_missing_vix_coords = np.setdiff1d(bot_bv_coords[:, 1], top_bv_coords[:, 1])  #coords missing in next but in curr
        bot_missing_vix_coords = np.setdiff1d(top_bv_coords[:, 1], bot_bv_coords[:, 1])  #coords missing in curr but in next
        
        t_new_verts, t_new_tris, t_pop_tris = self.snap(top_tid, top_missing_vix_coords, mode="top")
        b_new_verts, b_new_tris, b_pop_tris = self.snap(bottom_tid, bot_missing_vix_coords, mode="bottom")
        
        if len(t_new_verts) > 0:
            self.update_tid(top_tid, t_new_verts, t_new_tris, t_pop_tris)
        if len(b_new_verts) > 0:
            self.update_tid(bottom_tid, b_new_verts, b_new_tris, b_pop_tris)
    
    def snap_boundaries(self):
        rows = range(0, self.nr_rows-1)
        cols = range(0, self.nr_cols-1)
        
        for r in rows:
            for c in cols:
                curr_tid = "%s_%s" % (r, c)
                if curr_tid not in self.data.keys():
                    continue
                
                if c+1 <= cols[-1]:
                    right_tid = "%s_%s" % (r, c+1)
                    if right_tid not in self.data.keys():
                        right_tid = None
                else:
                    right_tid = None
                if r+1 <= rows[-1]:
                    lower_tid = "%s_%s" % (r+1, c)
                    if lower_tid not in self.data.keys():
                        lower_tid = None
                else:
                    lower_tid = None
                
                if right_tid:
                    self.snap_boundaries_left_right(left_tid=curr_tid, right_tid=right_tid)
                if lower_tid:
                    self.snap_boundaries_top_bottom(top_tid=curr_tid, bottom_tid=lower_tid)
        
    # def to_json(self, path):
        
    #     if path is None:
    #         raise ValueError("Valid path must be provided.")
        
    #     tiles = []
        
    #     for k,v in self.data.items():
            
    #         bbox_coords = [[v.bbox_geo[0], v.bbox_geo[1]],
    #                        [v.bbox_geo[2], v.bbox_geo[1]],
    #                        [v.bbox_geo[2], v.bbox_geo[3]],
    #                        [v.bbox_geo[0], v.bbox_geo[3]],
    #                        [v.bbox_geo[0], v.bbox_geo[1]]]
            
    #         bbox_geom = Polygon([bbox_coords])
    #         bbox_feat = Feature(geometry=bbox_geom, 
    #                             properties={"id": k, 
    #                                         "nrv":v.nr_vertices, 
    #                                         "nrt":v.nr_triangles})
    #         tiles.append(bbox_feat)
        
    #     tile_collection = FeatureCollection(tiles)
        
    #     with open(path, 'w') as f:
    #         dump(tile_collection, f)
    
    def merge_tiles(self, opath):
        
        out_verts = None
        out_tris = None
        
        rows = range(0, self.nr_rows-1)
        cols = range(0, self.nr_cols-1)
        
        for r in rows:
            for c in cols:
                curr_tid = "%s_%s" % (r, c)
                
                if curr_tid not in self.data.keys():
                    continue
                
                curr_tile = self.data[curr_tid]
                
                verts = curr_tile.vertices                        
                verts_h = curr_tile.tile_arr[verts[:, 0], verts[:, 1]]
                #tile_gt already contains the pixel shift towards the center; Hence, we don't add it again
                verts_geo = np.hstack((px2geo(verts, curr_tile.tile_gt, pixel_shift=False), verts_h.reshape(-1, 1)))
                
                tris = curr_tile.triangles
                
                if out_verts is None:
                    out_verts = verts_geo
                    out_tris = tris
                else:
                    
                    tris += int(np.shape(out_verts)[0])
                    
                    out_verts = np.vstack((out_verts, verts_geo))
                    out_tris = np.vstack((out_tris, tris))
        
        o3d_mesh = o3d.geometry.TriangleMesh(vertices=o3d.utility.Vector3dVector(out_verts),
                                             triangles=o3d.utility.Vector3iVector(out_tris))
        o3d_mesh.remove_duplicated_vertices()
        
        o3d.io.write_triangle_mesh(opath, o3d_mesh)