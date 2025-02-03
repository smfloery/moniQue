# AUSTRIA

import json
import os
import morecantile
import requests
import xml.etree.ElementTree as ET
from pyproj import CRS
from pyproj.transformer import Transformer
from io import StringIO
from PIL import Image
from osgeo import gdal, osr
import numpy as np
from tqdm import tqdm 

def tile2png(arr, path, prj, gt):
    driver = gdal.GetDriverByName("GTiff")
    outdata = driver.Create(path, 256, 256, 3, gdal.GDT_Byte)
    outdata.SetGeoTransform(gt)
    outdata.SetProjection(prj.ExportToWkt())
    outdata.GetRasterBand(1).WriteArray(arr[:, :, 0])        
    outdata.GetRasterBand(2).WriteArray(arr[:, :, 1])        
    outdata.GetRasterBand(3).WriteArray(arr[:, :, 2])        
    outdata.FlushCache() ##saves to disk!!
    outdata = None 

if __name__ == "__main__":
    
    wmts_url = "https://mapsneu.wien.gv.at/basemapneu/1.0.0/WMTSCapabilities.xml"
    tile_url = "https://mapsneu.wien.gv.at/basemap/bmaporthofoto30cm/normal/google3857/{z}/{y}/{x}.jpeg"
    tilematrix_set = "google3857_0-17"
    
    #17: ~1m; 16: ~2.5; 15: ~5m; 14: ~10m; 13: ~20; 12: ~40; 11: ~80; 10:~150;
    zoom_lvls = [10, 11, 12, 13, 14, 15, 16, 17]
    
    # json_path = "D:\\4_DATASETS\\at_10m_tirol\\grid_25832_25km\\tiles.json"
    # json_path = "D:\\4_DATASETS\\AKON\\innsbruck_25km_10m_25832\\tiles.json"
    # json_path = "D:\\4_DATASETS\\AKON\\grossglockner_25km_10m_25833\\tiles.json"
    # json_path = "D:\\4_DATASETS\\AKON\\pizbuin_25km_10m_25832\\tiles.json"
    json_path = "C:\\Users\\David\\Documents\\TU-Job\\QGIS\\grossvenediger_25km\\tiles.json"
    
    with open(json_path, "r") as f:
            tiles_data = json.load(f)
    
    odir_op = os.path.join(os.path.dirname(json_path), "op")
    if not os.path.exists(odir_op):
        os.mkdir(odir_op)
        
    from_crs = CRS.from_epsg(tiles_data["epsg"]) #bbox of whole mesh 
    to_crs = CRS.from_epsg(4326)
    trans = Transformer.from_crs(from_crs, to_crs)
    lat_ll, lon_ll = trans.transform(tiles_data["min_xyz"][0], tiles_data["min_xyz"][1])
    lat_ur, lon_ur = trans.transform(tiles_data["max_xyz"][0], tiles_data["max_xyz"][1])  
            
    wmts_ns = {"ows" : 'http://www.opengis.net/ows/1.1', 
               "wmts" : 'http://www.opengis.net/wmts/1.0'}
        
    wmts_xml_str = requests.get(wmts_url).content  
    wmts_xml = ET.fromstring(wmts_xml_str)
    
    wmts_contents = wmts_xml.findall("wmts:Contents", wmts_ns)[0]
    wmts_tilematrixsets = wmts_contents.findall("wmts:TileMatrixSet", wmts_ns)
    
    for tms in wmts_tilematrixsets:
        tms_identifier = tms.find("ows:Identifier", wmts_ns).text
        
        if tms_identifier == tilematrix_set:
        
            tms_bbox = tms.find("ows:BoundingBox", wmts_ns)
            tms_bbox_crs = tms_bbox.get("crs")
                
            tms_bbox_man = [-20037508.342800, -20037508.342800, 20037508.342800, 20037508.343346]
            
            tms_mc = morecantile.TileMatrixSet.custom(tms_bbox_man, CRS.from_epsg(3857), maxzoom=17)       
            
            for zlvl in zoom_lvls:
                
                odir_wms = os.path.join(odir_op, "%s" % (zlvl))
                os.makedirs(odir_wms, exist_ok=True)
                
                odir_tiles = os.path.join(odir_op, "%s_mesh" % (zlvl))
                os.makedirs(odir_tiles, exist_ok=True)
                
                ll_tile = tms_mc.tile(lon_ll, lat_ll, zlvl)
                ur_tile = tms_mc.tile(lon_ur, lat_ur, zlvl)
                        
                paths = []
                for cx in tqdm(range(ll_tile.x-2, ur_tile.x+3)):                #we add a buffer of tiles to make sure extent matches reprojected extent
                    for rx in tqdm(range(ur_tile.y-2, ll_tile.y+3)):
                        curr_tile_url = tile_url.format(x=cx, y=rx, z=zlvl)
                        curr_tile_bbox = tms_mc.xy_bounds(morecantile.Tile(cx, rx, zlvl))
                        
                        res_m = (curr_tile_bbox.right - curr_tile_bbox.left)/256
                                                
                        r = requests.get(curr_tile_url, stream=True)
                        if r.status_code == 200:
                            img = Image.open(r.raw)
                            img = np.array(img)
                            
                            tile_gt = [curr_tile_bbox.left, res_m, 0, curr_tile_bbox.top, 0, -res_m]
                            tile_prj = osr.SpatialReference()
                            tile_prj.ImportFromEPSG(3857)

                            tile_path = os.path.join(odir_wms, "%i_%i.tif" % (cx, rx))
                            paths.append(tile_path)
                            
                            tile2png(img, tile_path, tile_prj, tile_gt)
                
                vrt_options = gdal.BuildVRTOptions()#resampleAlg='cubic', addAlpha=True)
                vrt_path = os.path.join(os.path.dirname(odir_wms), "%s.vrt" % zlvl)
                my_vrt = gdal.BuildVRT(vrt_path, paths, options=vrt_options)
                my_vrt = None
                
                out_srs = osr.SpatialReference()
                out_srs.ImportFromEPSG(int(tiles_data["epsg"]))
                
                inp_srs = osr.SpatialReference()
                inp_srs.ImportFromEPSG(3857)
                
                for tile in tqdm(tiles_data["tiles"]):
                    kwargs = {'format': 'GTiff', 
                            'outputBounds':[tile["min_xyz"][0], tile["min_xyz"][1], 
                                            tile["max_xyz"][0], tile["max_xyz"][1]],
                            'outputBoundsSRS':out_srs,
                            'srcSRS':inp_srs,
                            'dstSRS':out_srs,
                            'xRes':res_m, 
                            'yRes':res_m,
                            'resampleAlg':'cubic',
                            'creationOptions' : {"COMPRESS":"JPEG", "JPEG_QUALITY":50}}
                    ds = gdal.Warp(os.path.join(odir_tiles, "%s.tif" % (tile["tid"])), vrt_path, **kwargs)
                    del ds