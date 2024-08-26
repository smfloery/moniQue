import json
import os
from osgeo import gdal, osr
import requests
from io import StringIO
from PIL import Image
import numpy as np
from tqdm import tqdm 
import matplotlib.pyplot as plt

def tile2tif(arr, path, prj, gt):
    driver = gdal.GetDriverByName("GTiff")
    outdata = driver.Create(path, arr.shape[1], arr.shape[0], 3, gdal.GDT_Byte, options={"COMPRESS":"JPEG", "JPEG_QUALITY":50})
    outdata.SetGeoTransform(gt)
    outdata.SetProjection(prj.ExportToWkt())
    outdata.GetRasterBand(1).WriteArray(arr[:, :, 0])        
    outdata.GetRasterBand(2).WriteArray(arr[:, :, 1])        
    outdata.GetRasterBand(3).WriteArray(arr[:, :, 2])        
    outdata.FlushCache() ##saves to disk!!
    outdata = None 

if __name__ == "__main__":
        
    wms_url = "https://geoservices.buergernetz.bz.it/mapproxy/wms?request=getMap"
    wms_lyr = "p_bz-Orthoimagery:Aerial-2023-RGB"
    wms_crs = "EPSG:25832"
    wms_img_fmt = "image/jpeg"
    wms_style = ""
    wms_version = "1.3.0"
    
    wms_max_size = 2000
    
    zoom_lvls = [10, 11, 12, 13, 14, 15, 16, 17]
    zoom_lvls_res = [150, 80, 40, 20, 10, 5, 2.5, 1]
    json_path = "D:\\4_DATASETS\\AKON\\bozen_25km_10m_25832\\tiles.json"
    
    odir_op = os.path.join(os.path.dirname(json_path), "op")
    if not os.path.exists(odir_op):
        os.mkdir(odir_op)
    
    for zlvl in zoom_lvls:
        zlvl_dir = os.path.join(odir_op, "%i_mesh" % (zlvl))
        if not os.path.exists(zlvl_dir):
            os.mkdir(zlvl_dir)
    
    with open(json_path, "r") as f:
        tiles_data = json.load(f)
        
    for tile in tqdm(tiles_data["tiles"]):
        tid = tile["tid"]
        min_xyz = tile["min_xyz"]
        max_xyz = tile["max_xyz"]
        
        bbox = [min_xyz[0], min_xyz[1], max_xyz[0], max_xyz[1]]
        bbox_str = ",".join(map(str, bbox))
        
        for zx, zlvl in enumerate(zoom_lvls):
            pix_res = zoom_lvls_res[zx]
            img_w = int((max_xyz[0] - min_xyz[0])/pix_res)
            img_h = int((max_xyz[1] - min_xyz[1])/pix_res)
            
            if img_w < wms_max_size:
                # pass
                wms_getmap = "%s&version=%s&crs=%s&layers=%s&styles=%s&format=%s&width=%i&height=%i&bbox=%s" % (wms_url, wms_version, wms_crs, wms_lyr, wms_style, wms_img_fmt, img_w, img_h, bbox_str)
        
                r = requests.get(wms_getmap, stream=True)
                if r.status_code == 200:
                    
                    img = Image.open(r.raw)
                    tile_arr = np.array(img, dtype=np.uint8)
                                    
            else:
                
                tile_arr = np.zeros(shape=(img_h, img_w, 3), dtype=np.uint8)
                
                c_steps = np.append(np.arange(0, img_w, wms_max_size), [img_w])
                r_steps = np.append(np.arange(0, img_h, wms_max_size), [img_h])
                
                for cx in range(len(c_steps)-1):
                    for rx in range(len(r_steps)-1):
                        min_c = c_steps[cx]
                        max_c = c_steps[cx+1]
                        
                        min_r = r_steps[rx]
                        max_r = r_steps[rx+1]
                        
                        curr_minx = bbox[0] + min_c*pix_res
                        curr_maxx = bbox[0] + max_c*pix_res
                        curr_miny = bbox[1] + min_r*pix_res
                        curr_maxy = bbox[1] + max_r*pix_res
                        
                        curr_bbox = [curr_minx, curr_miny, curr_maxx, curr_maxy]
                        curr_bbox_str = ",".join(map(str, curr_bbox))
                        
                        wms_getmap = "%s&version=%s&crs=%s&layers=%s&styles=%s&format=%s&width=%i&height=%i&bbox=%s" % (wms_url, wms_version, wms_crs, wms_lyr, wms_style, wms_img_fmt, max_c - min_c, max_r-min_r, curr_bbox_str)

                        r = requests.get(wms_getmap, stream=True)
                        if r.status_code == 200:
                            
                            img = Image.open(r.raw)
                            img = np.array(img, dtype=np.uint8)
                            
                            tile_arr[img_h-max_r:img_h-min_r, min_c:max_c, :] = img[:, :, :]
            
            tile_gt = [min_xyz[0], pix_res, 0, max_xyz[1], 0, -pix_res]
            tile_prj = osr.SpatialReference()
            tile_prj.ImportFromEPSG(int(wms_crs.split(":")[1]))

            tile_path = os.path.join(odir_op, "%i_mesh" % (zlvl), "%s.tif" % (tid))
            
            tile2tif(tile_arr, tile_path, tile_prj, tile_gt)