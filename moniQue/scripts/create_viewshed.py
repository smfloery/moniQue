from osgeo import gdal
import geopandas as gpd
import numpy as np
import sys
import os
import json
import open3d as o3d
import pandas as pd
from pyproj import Transformer
from skimage import morphology, io

def alpha2azi(alpha):
    return np.deg2rad((450 - np.rad2deg(alpha)) % 360)

def alzeka2rot(euler):
    
    al = euler[0]
    ze = euler[1]
    ka = euler[2]
    
    R = np.empty((3, 3))

    R[0,0] = np.cos(al) * np.cos(ze) * np.cos(ka) - np.sin(al) * np.sin(ka)
    R[0,1] = -np.cos(al) * np.cos(ze) * np.sin(ka) - np.sin(al) * np.cos(ka)
    R[0,2] = np.cos(al) * np.sin(ze)
    R[1,0] = np.sin(al) * np.cos(ze) * np.cos(ka) + np.cos(al) * np.sin(ka)
    R[1,1] = -np.sin(al) * np.cos(ze) * np.sin(ka) + np.cos(al) * np.cos(ka)
    R[1,2] = np.sin(al) * np.sin(ze)
    R[2,0] = -np.sin(ze) * np.cos(ka)
    R[2,1] = np.sin(ze) * np.sin(ka)
    R[2,2] = np.cos(ze)
    
    return R

def load_json(json_path):
    
    with open(json_path, "r") as f:
        tiles_data = json.load(f)
        tiles_data["tile_dir"] = os.path.join(os.path.dirname(json_path), "mesh")
        tiles_data["op_dir"] = os.path.join(os.path.dirname(json_path), "op")
        
        mesh_lvls = []
        sd_names = next(os.walk(tiles_data["tile_dir"]))[1]
        for sd in sd_names:
            mesh_lvls.append(int(sd))
        mesh_lvls.sort(reverse=True)
        tiles_data["mesh_lvls"] = list(map(str, mesh_lvls))
        
        if os.path.exists(tiles_data["op_dir"]):

            op_lvls = []            
            sd_names = next(os.walk(tiles_data["op_dir"]))[1]
            for sd in sd_names:
                if "mesh" in sd:
                    op_lvls.append(int(sd.split("_")[0]))
            op_lvls.sort(reverse=True)
            tiles_data["op_lvls"] = list(map(str, op_lvls))
        else:
            tiles_data["op_lvls"] = []

    return tiles_data
    
def tiles2scene(data):
    
    min_xyz = data["min_xyz"]
    
    o3d_scene = o3d.t.geometry.RaycastingScene()
    
    for tile in data["tiles"]:
        tile["op"] = {}
        tile_path = os.path.join(data["tile_dir"], "1", "%s.ply" % (tile["tid"]))
        
        tile_mesh = o3d.io.read_triangle_mesh(tile_path)
        tile_mesh = tile_mesh.translate((-min_xyz[0], -min_xyz[1], -min_xyz[2]), relative=True)    
        
        tile_mesh.compute_triangle_normals(normalized=True)
        tile_mesh.compute_vertex_normals(normalized=True)                
        mesh = o3d.t.geometry.TriangleMesh.from_legacy(tile_mesh)
        
        o3d_scene.add_triangles(mesh)
        
    return o3d_scene

def ray_plane_intersection_o3d(prc, alzeka, ior, img_pnts, scene):
    
    cmat = np.array([[1, 0, -ior[0]],
                    [0, 1, -ior[1]], 
                    [0, 0, -ior[2]]])
    
    rmat = alzeka2rot(alzeka)
    
    dir2pnts = rmat@cmat@img_pnts.T
    dir2pnts = dir2pnts / np.linalg.norm(dir2pnts, axis=0)
    
    rays = np.hstack((np.tile(prc, (len(img_pnts), 1)), dir2pnts.T))
    rays_o3d = o3d.core.Tensor(rays.astype(np.float32))
    
    ans = scene.cast_rays(rays_o3d)
    
    ans_dist = ans["t_hit"].numpy()
    ans_coords = rays[:, 0:3] + rays[:, 3:]*ans_dist.reshape(-1, 1)
    ans_nvecs = ans["primitive_normals"].numpy()
    
    ans_inca = np.arccos(np.sum(ans_nvecs*dir2pnts.T*(-1), axis=1) / np.linalg.norm(ans_nvecs, axis=1)*(np.linalg.norm(dir2pnts.T, axis=1)))
    
    return ans_coords, ans_nvecs, ans_dist, ans_inca

if __name__ == "__main__":
    
    voxel_size_m = 1
    min_hole_px = 10
    min_size_px = 100
    
    gpkg_name = "felix"
    gpkg_path = "D:\\1_PROJECTS\\24_HABER\\%s.gpkg" % (gpkg_name)

    out_dir = "D:\\1_PROJECTS\\24_HABER\\render\\"
    
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
        
    # cids = ["WolfgangHaber-Archiv-ialeD_10-490"]
    cids = ["WolfgangHaber-Archiv-ialeD_49-2308"]

    gpd_cams = gpd.read_file(gpkg_path, layer="cameras")
    gpd_cams = gpd_cams[gpd_cams["iid"].isin(cids)]
        
    cams_epsg = gpd_cams.crs.to_epsg()

    gpd_reg = gpd.read_file(gpkg_path, layer="region")
    
    json_path = gpd_reg["json_path"].values[0]
    tiles_data = load_json(json_path)
    
    o3d_scene = tiles2scene(tiles_data)
    
    for cx, cam in gpd_cams.iterrows():
        print(cam)
        
        iid = cam["iid"]
        
        clr = io.imread(cam["path"]).reshape(-1, 3)
        
        prc = np.array([cam["obj_x0"], cam["obj_y0"], cam["obj_z0"]])
        prc_local = prc - np.array(tiles_data["min_xyz"])
        
        alzeka = np.array([cam["alpha"], cam["zeta"], cam["kappa"]])
        ior = np.array([cam["img_x0"], cam["img_y0"], cam["f"]])
        
        #sampling points
        pnts_x = np.arange(0, cam["img_w"], step=1)
        pnts_y = np.arange(0, cam["img_h"], step=1)*(-1)
        
        xx, yy = np.meshgrid(pnts_x, pnts_y)
        img_pnts = np.hstack((xx.reshape(-1, 1), 
                            yy.reshape(-1, 1),
                            np.ones((len(pnts_x)*len(pnts_y),1))))  
        
        obj_pnts, obj_pnts_nvec, obj_pnts_dist, obj_pnts_inca = ray_plane_intersection_o3d(prc_local, alzeka, ior, img_pnts, o3d_scene)
        
        
        clr = clr[np.isfinite(obj_pnts).any(axis=1).ravel(), :]
        
        obj_pnts = obj_pnts[np.isfinite(obj_pnts).any(axis=1)]
        pcl = o3d.geometry.PointCloud()
        obj_pnts[:, 2] = 0
        
        pcl.points = o3d.utility.Vector3dVector(obj_pnts)
        pcl.colors = o3d.utility.Vector3dVector(clr)
        
        pcl_vxl = pcl.voxel_down_sample(voxel_size_m)    
        vxl_coords = np.asarray(pcl_vxl.points)[:, :2]
        vxl_colors = np.asarray(pcl_vxl.colors).astype(np.uint8)
        
        min_vxl_coords = np.min(vxl_coords, axis=0)
        max_vxl_coords = np.max(vxl_coords, axis=0)
        
        nr_cols = int((max_vxl_coords[0] - min_vxl_coords[0]) / voxel_size_m)+1
        nr_rows = int((max_vxl_coords[1] - min_vxl_coords[1]) / voxel_size_m)+1
                    
        vxl_arr = np.zeros((nr_rows, nr_cols), dtype=np.uint8)
        vxl_clr_arr = np.zeros((nr_rows, nr_cols, 3), dtype=np.uint8)

        vxl_gix = (vxl_coords - min_vxl_coords)/voxel_size_m
        vxl_gix = vxl_gix.astype(np.uint16)
        
        vxl_arr[vxl_gix[:, 1].ravel(), vxl_gix[:, 0].ravel()] = 1
        vxl_arr = np.flipud(vxl_arr)
        
        vxl_clr_arr[vxl_gix[:, 1].ravel(), vxl_gix[:, 0].ravel(), 0] = vxl_colors[:, 0]
        vxl_clr_arr[vxl_gix[:, 1].ravel(), vxl_gix[:, 0].ravel(), 1] = vxl_colors[:, 1]
        vxl_clr_arr[vxl_gix[:, 1].ravel(), vxl_gix[:, 0].ravel(), 2] = vxl_colors[:, 2]
        vxl_clr_arr = np.flipud(vxl_clr_arr)
        
        
        vxl_arr = morphology.remove_small_holes(vxl_arr, area_threshold=min_hole_px, connectivity=1)
        vxl_arr = morphology.binary_closing(vxl_arr.astype(bool), footprint=morphology.disk(1))
        vxl_arr = morphology.remove_small_objects(vxl_arr, min_size=min_size_px, connectivity=1)
        vxl_arr = morphology.remove_small_holes(vxl_arr, area_threshold=min_hole_px, connectivity=1)
        
        vxl_arr_gt = (min_vxl_coords[0]+tiles_data["min_xyz"][0]-voxel_size_m/2.,         #tl x
                      voxel_size_m,                           #res x
                      0,                                      #rot x
                      max_vxl_coords[1]+tiles_data["min_xyz"][1]+voxel_size_m/2.,      #tl y
                      0,                                      #rot y
                      voxel_size_m*(-1))

        driver = gdal.GetDriverByName("GTiff")

        outdata = driver.Create(os.path.join(out_dir, cam["iid"] + "_vs.tif"), nr_cols, nr_rows, 1, gdal.GDT_Byte)
        
        outdata.SetGeoTransform(vxl_arr_gt)
        # outdata.SetProjection(attr_arr_srs.ExportToWkt())
        
        outdata.GetRasterBand(1).WriteArray(vxl_arr[:, :].astype(np.uint8))
        outdata.GetRasterBand(1).SetNoDataValue(0)
        
        outdata.FlushCache()
        
        
        driver = gdal.GetDriverByName("GTiff")

        outdata = driver.Create(os.path.join(out_dir, cam["iid"] + "_op.tif"), nr_cols, nr_rows, 3, gdal.GDT_Byte)
        
        outdata.SetGeoTransform(vxl_arr_gt)
        # outdata.SetProjection(attr_arr_srs.ExportToWkt())
        
        outdata.GetRasterBand(1).WriteArray(vxl_clr_arr[:, :, 0].astype(np.uint8))
        outdata.GetRasterBand(1).SetNoDataValue(0)
        
        outdata.GetRasterBand(2).WriteArray(vxl_clr_arr[:, :, 1].astype(np.uint8))
        outdata.GetRasterBand(2).SetNoDataValue(0)
        
        outdata.GetRasterBand(3).WriteArray(vxl_clr_arr[:, :, 2].astype(np.uint8))
        outdata.GetRasterBand(3).SetNoDataValue(0)
        outdata.FlushCache()
        
    # #     img_path = cam["path"]
    # #     img = Image.open(img_path)

    # #     if create_csv:
    # #         bg_color = (255, 255, 255)    
    # #         img.thumbnail((canvas_h, canvas_w))
    # #         img_pad = img2square(img, background_color=bg_color)
    # #         # img_pad.save(os.path.join(out_dir, "%s.png" % (iid)))
                    
    # #         img_pad_bits = BytesIO()
    # #         img_pad.save(img_pad_bits, format="png")
    # #         img_pad_str = "data:image/png;base64," + base64.b64encode(img_pad_bits.getvalue()).decode("utf-8")

    # #         img_w, img_h = img.size
                    
    # #         if img_w > img_h:
    # #             diff = img_w-img_h
    # #             bbox = [diff/2., 0, img_w-(diff/2.), img_h]
    # #         else:
    # #             diff = img_h-img_w
    # #             bbox = [0, diff/2., img_w, img_h-(diff/2.)]

    # #         thumb_img = img.resize((50, 50), box=bbox)
    # #         # thumb_img.save("C:\\Users\\sfloery\\Desktop\\thumbs\\%i.png" % (row.iid))
    # #         thumb_bits = BytesIO()
    # #         thumb_img.save(thumb_bits, format="png")
    # #         thumb_str = "data:image/png;base64," + base64.b64encode(thumb_bits.getvalue()).decode("utf-8")
        
    # #     prc = np.array([cam["obj_x0"], cam["obj_y0"], cam["obj_z0"]])
    # #     prc_4326 = trans.transform(cam["obj_x0"], cam["obj_y0"])

    # #     euler = np.array([cam["alpha"], cam["zeta"], cam["kappa"]])
    # #     rmat = alzeka2rot(euler)
    # #     ior = np.array([cam["img_x0"], cam["img_y0"], cam["f"]])
        
    # #     hfov = cam["hfov"]
    # #     vfov = cam["vfov"]
        
    # #     img_h = cam["img_h"]
    # #     img_w = cam["img_w"]
        
    # #     rmat_gfx = np.zeros((4,4))
    # #     rmat_gfx[3, 3] = 1
    # #     rmat_gfx[:3, :3] = rmat
                
    # #     if hfov > vfov:
    # #         gfx_camera = gfx.PerspectiveCamera(fov=np.rad2deg(hfov)+5, depth_range=(min_dist_cam, 100000))
    # #     else:
    # #         gfx_camera = gfx.PerspectiveCamera(fov=np.rad2deg(vfov)+5, depth_range=(min_dist_cam, 100000))
    # #     gfx_camera.local.position = prc
    # #     gfx_camera.local.rotation_matrix = rmat_gfx

    # #     gfx_focal = (canvas_w/2)/np.tan(np.deg2rad(gfx_camera.fov/2.))
        
    # #     res_w = int(np.tan(hfov/2.)*gfx_focal*2)
    # #     res_h = int(np.tan(vfov/2.)*gfx_focal*2)
    # #     res_img = img.resize((res_h, res_w))#, preserve_range=True)
        
    # #     diff_w = canvas_w - res_w
    # #     lpad, rpad = int(diff_w/2.), int(diff_w/2.)
    # #     if diff_w % 2 != 0:
    # #         rpad += 1
            
    # #     diff_h = canvas_h - res_h
    # #     tpad, bpad = int(diff_h/2.), int(diff_h/2.)
    # #     if diff_h % 2 != 0:
    # #         bpad += 1
                           
    # #     bg = gfx.Background(None, gfx.BackgroundMaterial([0.086, 0.475, 0.671, 1]))
    # #     gfx_scene.add(bg)

    # #     cam_pos = gfx_camera.local.position
    # #     frustum = gfx_camera.frustum
    # #     corners_flat = frustum.reshape((-1, 3))
                
    # #     corners_by_plane = np.stack([
    # #         corners_flat[[0, 3, 7, 4], :],
    # #         corners_flat[[5, 6, 2, 1], :],
    # #         corners_flat[[3, 2, 6, 7], :],
    # #         corners_flat[[4, 5, 1, 0], :],
    # #         corners_flat[[1, 2, 3, 0], :],
    # #         corners_flat[[4, 7, 6, 5], :]], axis=0)
                    
    # #     # planes in normal form (normals point away from the frustum area)
    # #     normals = np.cross(
    # #         corners_by_plane[:, 0, :] - corners_by_plane[:, 3, :],
    # #         corners_by_plane[:, 2, :] - corners_by_plane[:, 3, :]
    # #     )
        
    # #     normals /= np.linalg.norm(normals, axis=-1)[:, None] # normal normals ^_^
    # #     # offset = np.sum(normals * corners_by_plane[:, 3, :], axis=-1)  #d=n*r0; r0 some point on the plane            
        
    # #     # end_time = time.time()
    # #     # print("%.6f" % (end_time - start_time))
        
    # #     # start_time = time.time()
    # #     for tile in tiles_data["tiles"]:
    # #         result = "INSIDE"
    # #         tile_cx = np.array(tile["cx_r"][:3])# - self.min_xyz
            
    # #         for nx in range(6):
                
    # #             #normal distance between any point on the plane and the sphere center                
    # #             #https://www.w3schools.blog/distance-of-a-point-from-a-plane
    # #             #simplest frustum culling technique; renderes more tiles than actually visible;
    # #             cx_c_vec = tile_cx - corners_by_plane[nx, 0, :]                    
    # #             cx_dist = np.dot(cx_c_vec, normals[nx, :])
                                
    # #             if cx_dist > tile["cx_r"][-1]:
    # #                 result="OUTSIDE"
    # #                 break
                                
    # #         # #first tile added to group has tid_pygfx = 0; Hence, we can use this id to directly access the 
    # #         # #respective children within the list; no need for an additional for loop;
    # #         if result == "INSIDE":
    # #             lod_lvl = "17"
                
    # #             terrain.children[int(tile["tid_int"])].material.map = tile["op"][lod_lvl]
    # #             terrain.children[int(tile["tid_int"])].visible = True
                
    # #         else:
    # #             terrain.children[int(tile["tid_int"])].visible = False
        
    # #     offscreen_canvas.request_draw(offscreen_renderer.render(gfx_scene, gfx_camera))
    # #     img_scene_arr = np.asarray(offscreen_canvas.draw())[:,:,:3]
    # #     img_scene = Image.fromarray(img_scene_arr)
    # #     img_scene.save(os.path.join(out_dir, "%s_wo.png" % (iid)))
        
    # #     img_scene_bits = BytesIO()
    # #     img_scene.save(img_scene_bits, format="png")
    # #     img_scene_str = "data:image/png;base64," + base64.b64encode(img_scene_bits.getvalue()).decode("utf-8")
        
    # #     cmat = np.array([[1, 0, -cam["img_x0"]], 
    # #                     [0, 1, -cam["img_y0"]],
    # #                     [0, 0, -cam["f"]]])
        
    # #     plane_pnts_img = np.array([[0, 0, 1],
    # #                         [img_w, 0, 1],
    # #                         [img_w, img_h*(-1), 1],
    # #                         [0, img_h*(-1), 1]]).T
        
    # #     plane_pnts_dir = (rmat@cmat@plane_pnts_img).T
    # #     plane_pnts_dir = plane_pnts_dir / np.linalg.norm(plane_pnts_dir, axis=1).reshape(-1, 1)
        
    # #     plane_pnts_obj = prc + dist_plane * plane_pnts_dir
    # #     plane_faces = np.array([[3, 1, 0], [3, 2, 1]]).astype(np.uint32)
    # #     plane_uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]]).astype(np.uint32)
        
    # #     plane_geom = gfx.geometries.Geometry(indices=plane_faces, 
    # #                                         positions=plane_pnts_obj.astype(np.float32),
    # #                                         texcoords=plane_uv.astype(np.float32))
        
    # #     img_array = np.asarray(img)
    # #     tex = gfx.Texture(img_array, dim=2)
        
    # #     plane_material = gfx.MeshBasicMaterial(map=tex, side="FRONT", map_interpolation="linear")
    # #     plane_mesh = gfx.Mesh(plane_geom, plane_material, visible=True)
    # #     gfx_scene.add(plane_mesh)

    # #     offscreen_canvas.request_draw(offscreen_renderer.render(gfx_scene, gfx_camera))
    # #     img_scene_with_arr = np.asarray(offscreen_canvas.draw())[:,:,:3]
    # #     img_scene_with = Image.fromarray(img_scene_with_arr)
    # #     img_scene_with.save(os.path.join(out_dir, "%s_w.png" % (iid)))
        
    # #     img_scene_with_bits = BytesIO()
    # #     img_scene_with.save(img_scene_with_bits, format="png")
    # #     img_scene_with_str = "data:image/png;base64," + base64.b64encode(img_scene_with_bits.getvalue()).decode("utf-8")
        
    # #     if create_csv:
    # #         csv_render_data.append({"iid": "H" + iid,
    # #                                 "render":img_scene_str, 
    # #                                 "render_with":img_scene_with_str,
    # #                                 })
            
    # #         csv_spot_data.append({"iid":"H" + iid,
    # #                         "image":img_pad_str,
    # #                         "thumb":thumb_str,
    # #                         "geom": "SRID=4326;POINT (%.6f %.6f)" % (prc_4326[1], prc_4326[0]),
    # #                         "altitude": prc[2],
    # #                         "hfov":hfov,
    # #                         "vfov":vfov,
    # #                         "alpha":euler[0],
    # #                         "heading":alpha2azi(euler[0])+np.pi,   #alpha appaers to be facing opposite direction; Hence, we need to add 180°
    # #                         "zeta":euler[1],
    # #                         "kappa":euler[2],
    # #                         "f":ior[2],                         
    # #                         "archive":cam["archiv"],
    # #                         "copy": cam["copy"],
    # #                         "von":"%s-01-01" % (cam["jahr"]),
    # #                         "bis":"%s-12-31" % (cam["jahr"])})
    
    # # if create_csv:
    # #     pd_spot = pd.DataFrame(csv_spot_data)
    # #     pd_spot.to_json(os.path.join(out_dir, "%s_spot.json" % (gpkg_name)), orient="records", indent=4)
        
    # #     pd_render = pd.DataFrame(csv_render_data)
    # #     pd_render.to_json(os.path.join(out_dir, "%s_render.json" % (gpkg_name)), orient="records", indent=4)