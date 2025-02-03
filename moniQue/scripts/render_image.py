from osgeo import gdal
import geopandas as gpd
import numpy as np
import sys
import os
import json
import pygfx as gfx
from wgpu.gui.offscreen import WgpuCanvas as offscreenCanvas
from PIL import Image
import base64
from io import BytesIO
import open3d as o3d
import pandas as pd
from pyproj import Transformer

def alpha2azi(alpha):
    return np.deg2rad((450 - np.rad2deg(alpha)) % 360)

def img2square(pil_img, background_color):
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result

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
    
def load_terrain(data):
    
    terrain = gfx.Group()
    lod_lvls = data["op_lvls"]
    
    for tile in data["tiles"]:
        tile["op"] = {}
        tile_path = os.path.join(data["tile_dir"], "1", "%s.ply" % (tile["tid"]))
        tile_mesh = o3d.io.read_triangle_mesh(tile_path)

        verts = np.asarray(tile_mesh.vertices)
        
        u = (verts[:, 0] - tile["min_xyz"][0])/(tile["max_xyz"][0] - tile["min_xyz"][0])
        v = (verts[:, 1] - tile["min_xyz"][1])/(tile["max_xyz"][1] - tile["min_xyz"][1])
        uv = np.hstack((u.reshape(-1, 1), v.reshape(-1, 1)))
        
        # verts -= self.min_xyz
        faces = np.asarray(tile_mesh.triangles).astype(np.uint32)
                            
        mesh_geom = gfx.geometries.Geometry(indices=faces, 
                                            positions=verts.astype(np.float32),
                                            texcoords=uv.astype(np.float32),
                                            tid=[int(tile["tid_int"])])
        
        if len(lod_lvls) > 0:
        
            for lod in lod_lvls:
                lod_path = os.path.join(data["op_dir"], "%s_mesh" % lod, "%s.tif" % (tile["tid"]))
                            
                img_ds = gdal.Open(lod_path)
                img_h = img_ds.RasterYSize
                img_w = img_ds.RasterXSize
                img_arr = np.zeros((img_h, img_w, 3), dtype=np.uint8)
                            
                for bx in range(3):
                    bx_arr = img_ds.GetRasterBand(bx+1).ReadAsArray()
                    img_arr[:, :, bx] = bx_arr
                                
                img_arr = np.flipud(img_arr)
                tex = gfx.Texture(img_arr, dim=2)
                mesh_material = gfx.MeshBasicMaterial(map=tex, side="FRONT", map_interpolation="linear")
                
                tile["op"][lod] = tex
            
        else:
            mesh_material = gfx.MeshNormalMaterial(side="FRONT")
        
        #add lowest resolution material to mesh at startup
        mesh = gfx.Mesh(mesh_geom, mesh_material, visible=False)
        terrain.add(mesh)
    return terrain

if __name__ == "__main__":
    
    # gpkg_name = "wildspitze_25km_10m_akon"
    # gpkg_path = "D:\\4_DATASETS\\AKON\\%s.gpkg" % (gpkg_name)
    
    gpkg_name = "felix"
    gpkg_path = "D:\\1_PROJECTS\\24_HABER\\%s.gpkg" % (gpkg_name)


    create_csv = False
    
    canvas_w = 2000
    canvas_h = 2000
    
    min_dist_cam = 10 #default: 10
    dist_plane = 50   #default: 100
    
    # out_dir = os.path.join("D:\\1_PROJECTS\\24_SEHAG4CS\\import\\%s" % (gpkg_name))
    # out_dir = os.path.join("D:\\1_PROJECTS\\24_SEHAG4CS\\render\\")
    out_dir = "D:\\1_PROJECTS\\24_HABER\\render\\"
    
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
        
    cids = ["WolfgangHaber-Archiv-ialeD_10-490"]

    gpd_cams = gpd.read_file(gpkg_path, layer="cameras")
    gpd_cams = gpd_cams[gpd_cams["iid"].isin(cids)]
    
    #only necessary if csv output
    # gpd_cams["jahr"] = ["1938", "1935", "1911"]                                 #!CHANGE
    # gpd_cams["archiv"] = ["AKON (OenB)"]*len(cids)                              #!CHANGE
    # gpd_cams["copy"] = ["AKON/Österreichische Nationalbibliothek"]*len(cids)    #!CHANGE
        
    cams_epsg = gpd_cams.crs.to_epsg()

    gpd_reg = gpd.read_file(gpkg_path, layer="region")

    json_path = gpd_reg["json_path"].values[0]
    tiles_data = load_json(json_path)
    
    gfx_scene = gfx.Scene()
    terrain = load_terrain(tiles_data)
    gfx_scene.add(terrain)
    
    offscreen_canvas = offscreenCanvas(size=(canvas_w, canvas_h), pixel_ratio=1)
    offscreen_renderer = gfx.WgpuRenderer(offscreen_canvas)
    
    trans = Transformer.from_crs(cams_epsg, "EPSG:4326")
    
    csv_spot_data = []
    csv_render_data = []
    
    for cx, cam in gpd_cams.iterrows():
        
        iid = cam["iid"]
        
        img_path = cam["path"]
        img = Image.open(img_path)

        if create_csv:
            bg_color = (255, 255, 255)    
            img.thumbnail((canvas_h, canvas_w))
            img_pad = img2square(img, background_color=bg_color)
            # img_pad.save(os.path.join(out_dir, "%s.png" % (iid)))
                    
            img_pad_bits = BytesIO()
            img_pad.save(img_pad_bits, format="png")
            img_pad_str = "data:image/png;base64," + base64.b64encode(img_pad_bits.getvalue()).decode("utf-8")

            img_w, img_h = img.size
                    
            if img_w > img_h:
                diff = img_w-img_h
                bbox = [diff/2., 0, img_w-(diff/2.), img_h]
            else:
                diff = img_h-img_w
                bbox = [0, diff/2., img_w, img_h-(diff/2.)]

            thumb_img = img.resize((50, 50), box=bbox)
            # thumb_img.save("C:\\Users\\sfloery\\Desktop\\thumbs\\%i.png" % (row.iid))
            thumb_bits = BytesIO()
            thumb_img.save(thumb_bits, format="png")
            thumb_str = "data:image/png;base64," + base64.b64encode(thumb_bits.getvalue()).decode("utf-8")
        
        prc = np.array([cam["obj_x0"], cam["obj_y0"], cam["obj_z0"]])
        prc_4326 = trans.transform(cam["obj_x0"], cam["obj_y0"])

        euler = np.array([cam["alpha"], cam["zeta"], cam["kappa"]])
        rmat = alzeka2rot(euler)
        ior = np.array([cam["img_x0"], cam["img_y0"], cam["f"]])
        
        hfov = cam["hfov"]
        vfov = cam["vfov"]
        
        img_h = cam["img_h"]
        img_w = cam["img_w"]
        
        rmat_gfx = np.zeros((4,4))
        rmat_gfx[3, 3] = 1
        rmat_gfx[:3, :3] = rmat
                
        if hfov > vfov:
            gfx_camera = gfx.PerspectiveCamera(fov=np.rad2deg(hfov)+5, depth_range=(min_dist_cam, 100000))
        else:
            gfx_camera = gfx.PerspectiveCamera(fov=np.rad2deg(vfov)+5, depth_range=(min_dist_cam, 100000))
        gfx_camera.local.position = prc
        gfx_camera.local.rotation_matrix = rmat_gfx

        gfx_focal = (canvas_w/2)/np.tan(np.deg2rad(gfx_camera.fov/2.))
        
        res_w = int(np.tan(hfov/2.)*gfx_focal*2)
        res_h = int(np.tan(vfov/2.)*gfx_focal*2)
        res_img = img.resize((res_h, res_w))#, preserve_range=True)
        
        diff_w = canvas_w - res_w
        lpad, rpad = int(diff_w/2.), int(diff_w/2.)
        if diff_w % 2 != 0:
            rpad += 1
            
        diff_h = canvas_h - res_h
        tpad, bpad = int(diff_h/2.), int(diff_h/2.)
        if diff_h % 2 != 0:
            bpad += 1
                           
        bg = gfx.Background(None, gfx.BackgroundMaterial([0.086, 0.475, 0.671, 1]))
        gfx_scene.add(bg)

        cam_pos = gfx_camera.local.position
        frustum = gfx_camera.frustum
        corners_flat = frustum.reshape((-1, 3))
                
        corners_by_plane = np.stack([
            corners_flat[[0, 3, 7, 4], :],
            corners_flat[[5, 6, 2, 1], :],
            corners_flat[[3, 2, 6, 7], :],
            corners_flat[[4, 5, 1, 0], :],
            corners_flat[[1, 2, 3, 0], :],
            corners_flat[[4, 7, 6, 5], :]], axis=0)
                    
        # planes in normal form (normals point away from the frustum area)
        normals = np.cross(
            corners_by_plane[:, 0, :] - corners_by_plane[:, 3, :],
            corners_by_plane[:, 2, :] - corners_by_plane[:, 3, :]
        )
        
        normals /= np.linalg.norm(normals, axis=-1)[:, None] # normal normals ^_^
        # offset = np.sum(normals * corners_by_plane[:, 3, :], axis=-1)  #d=n*r0; r0 some point on the plane            
        
        # end_time = time.time()
        # print("%.6f" % (end_time - start_time))
        
        # start_time = time.time()
        for tile in tiles_data["tiles"]:
            result = "INSIDE"
            tile_cx = np.array(tile["cx_r"][:3])# - self.min_xyz
            
            for nx in range(6):
                
                #normal distance between any point on the plane and the sphere center                
                #https://www.w3schools.blog/distance-of-a-point-from-a-plane
                #simplest frustum culling technique; renderes more tiles than actually visible;
                cx_c_vec = tile_cx - corners_by_plane[nx, 0, :]                    
                cx_dist = np.dot(cx_c_vec, normals[nx, :])
                                
                if cx_dist > tile["cx_r"][-1]:
                    result="OUTSIDE"
                    break
                                
            # #first tile added to group has tid_pygfx = 0; Hence, we can use this id to directly access the 
            # #respective children within the list; no need for an additional for loop;
            if result == "INSIDE":
                lod_lvl = "17"
                
                terrain.children[int(tile["tid_int"])].material.map = tile["op"][lod_lvl]
                terrain.children[int(tile["tid_int"])].visible = True
                
            else:
                terrain.children[int(tile["tid_int"])].visible = False
        
        offscreen_canvas.request_draw(offscreen_renderer.render(gfx_scene, gfx_camera))
        img_scene_arr = np.asarray(offscreen_canvas.draw())[:,:,:3]
        img_scene = Image.fromarray(img_scene_arr)
        img_scene.save(os.path.join(out_dir, "%s_wo.png" % (iid)))
        
        img_scene_bits = BytesIO()
        img_scene.save(img_scene_bits, format="png")
        img_scene_str = "data:image/png;base64," + base64.b64encode(img_scene_bits.getvalue()).decode("utf-8")
        
        cmat = np.array([[1, 0, -cam["img_x0"]], 
                        [0, 1, -cam["img_y0"]],
                        [0, 0, -cam["f"]]])
        
        plane_pnts_img = np.array([[0, 0, 1],
                            [img_w, 0, 1],
                            [img_w, img_h*(-1), 1],
                            [0, img_h*(-1), 1]]).T
        
        plane_pnts_dir = (rmat@cmat@plane_pnts_img).T
        plane_pnts_dir = plane_pnts_dir / np.linalg.norm(plane_pnts_dir, axis=1).reshape(-1, 1)
        
        plane_pnts_obj = prc + dist_plane * plane_pnts_dir
        plane_faces = np.array([[3, 1, 0], [3, 2, 1]]).astype(np.uint32)
        plane_uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]]).astype(np.uint32)
        
        plane_geom = gfx.geometries.Geometry(indices=plane_faces, 
                                            positions=plane_pnts_obj.astype(np.float32),
                                            texcoords=plane_uv.astype(np.float32))
        
        img_array = np.asarray(img)
        tex = gfx.Texture(img_array, dim=2)
        
        plane_material = gfx.MeshBasicMaterial(map=tex, side="FRONT", map_interpolation="linear")
        plane_mesh = gfx.Mesh(plane_geom, plane_material, visible=True)
        gfx_scene.add(plane_mesh)

        offscreen_canvas.request_draw(offscreen_renderer.render(gfx_scene, gfx_camera))
        img_scene_with_arr = np.asarray(offscreen_canvas.draw())[:,:,:3]
        img_scene_with = Image.fromarray(img_scene_with_arr)
        img_scene_with.save(os.path.join(out_dir, "%s_w.png" % (iid)))
        
        img_scene_with_bits = BytesIO()
        img_scene_with.save(img_scene_with_bits, format="png")
        img_scene_with_str = "data:image/png;base64," + base64.b64encode(img_scene_with_bits.getvalue()).decode("utf-8")
        
        if create_csv:
            csv_render_data.append({"iid": "H" + iid,
                                    "render":img_scene_str, 
                                    "render_with":img_scene_with_str,
                                    })
            
            csv_spot_data.append({"iid":"H" + iid,
                            "image":img_pad_str,
                            "thumb":thumb_str,
                            "geom": "SRID=4326;POINT (%.6f %.6f)" % (prc_4326[1], prc_4326[0]),
                            "altitude": prc[2],
                            "hfov":hfov,
                            "vfov":vfov,
                            "alpha":euler[0],
                            "heading":alpha2azi(euler[0])+np.pi,   #alpha appaers to be facing opposite direction; Hence, we need to add 180°
                            "zeta":euler[1],
                            "kappa":euler[2],
                            "f":ior[2],                         
                            "archive":cam["archiv"],
                            "copy": cam["copy"],
                            "von":"%s-01-01" % (cam["jahr"]),
                            "bis":"%s-12-31" % (cam["jahr"])})
    
    if create_csv:
        pd_spot = pd.DataFrame(csv_spot_data)
        pd_spot.to_json(os.path.join(out_dir, "%s_spot.json" % (gpkg_name)), orient="records", indent=4)
        
        pd_render = pd.DataFrame(csv_render_data)
        pd_render.to_json(os.path.join(out_dir, "%s_render.json" % (gpkg_name)), orient="records", indent=4)