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
import math 

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

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 1 << zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return xtile, ytile

if __name__ == "__main__":
    
    # wmts_url = "https://mapsneu.wien.gv.at/basemapneu/1.0.0/WMTSCapabilities.xml"
    # tile_url = "https://mapsneu.wien.gv.at/basemap/bmaporthofoto30cm/normal/google3857/{z}/{y}/{x}.jpeg"
    # tilematrix_set = "google3857_0-17"
    
    # wmts_url = "https://geoservices.bayern.de/od/wmts/geobasis/v1/1.0.0/WMTSCapabilities.xml"
    # tile_url = "https://wmtsod1.bayernwolke.de/wmts/by_dop/adv_utm32/{z}/{y}/{x}"
    # tilematrix_set = "adv_utm32"
    
    wmts_url = "https://www.cartografia.servizirl.it/arcgis2/rest/services/BaseMap/ortofoto2015UTM32N/ImageServer/WMTS?REQUEST=GetCapabilities&service=WMTS&_jsfBridgeRedirect=true"
    tile_url = "https://www.cartografia.servizirl.it/arcgis2/rest/services/BaseMap/ortofoto2015UTM32N/ImageServer/WMTS/tile/1.0.0/BaseMap_ortofoto2015UTM32N/default/default028mm/{z}/{row}/{col}.jpg"
    tilematrix_set = "default028mm"
    
    #17: ~1m; 16: ~2.5; 15: ~5m; 14: ~10m; 13: ~20; 12: ~40; 11: ~80; 10:~150;
    # zoom_lvls = [10, 11, 12, 13, 14, 15, 16, 17]
    zoom_lvls = [12]
    
    # json_path = "D:\\4_DATASETS\\at_10m_tirol\\grid_25832_25km\\tiles.json"
    # json_path = "D:\\4_DATASETS\\AKON\\innsbruck_25km_10m_25832\\tiles.json"
    # json_path = "D:\\4_DATASETS\\AKON\\grossglockner_25km_10m_25833\\tiles.json"
    # json_path = "D:\\4_DATASETS\\AKON\\pizbuin_25km_10m_25832\\tiles.json"
    # json_path = "D:\\4_DATASETS\\AKON\\lech_25km_10m_25832\\tiles.json"
    # json_path = "D:\\4_DATASETS\\HABER\\solnhofen_1m_utm32_felix\\tiles.json"
    json_path = "D:\\1_PROJECTS\\01_SEHAG\\05_STEREO_PAIRS\\mt_stereo\\tiles.json"

    with open(json_path, "r") as f:
            tiles_data = json.load(f)
    
    odir_op = os.path.join(os.path.dirname(json_path), "op")
    if not os.path.exists(odir_op):
        os.mkdir(odir_op)
    
    reg_min_x = tiles_data["min_xyz"][0]
    reg_min_y = tiles_data["min_xyz"][1]
    reg_max_x = tiles_data["max_xyz"][0]
    reg_max_y = tiles_data["max_xyz"][1]

    wmts_ns = {"ows" : 'http://www.opengis.net/ows/1.1', 
               "wmts" : 'http://www.opengis.net/wmts/1.0'}
        
    wmts_xml_str = requests.get(wmts_url).content  
    wmts_xml = ET.fromstring(wmts_xml_str)
    
    wmts_contents = wmts_xml.findall("wmts:Contents", wmts_ns)[0]
    wmts_tilematrixsets = wmts_contents.findall("wmts:TileMatrixSet", wmts_ns)
    
    for tms in wmts_tilematrixsets:
        tms_identifier = tms.find("ows:Identifier", wmts_ns).text
        tms_epsg = tms.find("ows:SupportedCRS", wmts_ns).text.split("::")[1]
        tms_crs = osr.SpatialReference()
        tms_crs.ImportFromEPSG(int(tms_epsg))
                        
        if tms_identifier == tilematrix_set:
                
            for zlvl in zoom_lvls:
                
                tm = tms.findall("wmts:TileMatrix", wmts_ns)
                
                for tm_z in tm:
                    if tm_z.find("ows:Identifier", wmts_ns).text == str(zlvl):
        
                        odir_wms = os.path.join(odir_op, "%s" % (zlvl))
                        os.makedirs(odir_wms, exist_ok=True)
                        
                        odir_tiles = os.path.join(odir_op, "%s_mesh" % (zlvl))
                        os.makedirs(odir_tiles, exist_ok=True)

                                                
                        scale_denom = float(tm_z.find("wmts:ScaleDenominator", wmts_ns).text)
                        tl_corner = tm_z.find("wmts:TopLeftCorner", wmts_ns).text
                        tile_width = int(tm_z.find("wmts:TileWidth", wmts_ns).text)
                        tile_height = int(tm_z.find("wmts:TileHeight", wmts_ns).text)
                        matrix_width = int(tm_z.find("wmts:MatrixWidth", wmts_ns).text)
                        matrix_height = int(tm_z.find("wmts:MatrixHeight", wmts_ns).text)
                        
                        tl_x, tl_y = map(float, tl_corner.split(" "))
                        
                        tile_w_m = tile_width * 0.28*10**-3 * scale_denom
                        tile_h_m = tile_height * 0.28*10**-3 * scale_denom
                        
                        lr_x = tl_x + tile_w_m * matrix_width
                        lr_y = tl_y - tile_h_m * matrix_height                              
                        
                        x_steps = np.arange(tl_x, lr_x, tile_w_m)
                        y_steps = np.arange(tl_y, lr_y, -tile_h_m)
                        
                        min_col = np.digitize(reg_min_x, x_steps)-1
                        max_col = np.digitize(reg_max_x, x_steps)
                        max_row = np.digitize(reg_min_y, y_steps)
                        min_row = np.digitize(reg_max_y, y_steps)-1
                        
                        paths = []
                        for cx in tqdm(range(min_col, max_col)):                #we add a buffer of tiles to make sure extent matches reprojected extent
                            for rx in tqdm(range(min_row, max_row)):
                                
                                curr_tile_url = tile_url.format(col=cx, row=rx, z=zlvl)
                                
                                curr_min_x = tl_x + tile_w_m * cx
                                curr_max_x = tl_x + tile_w_m * (cx+1)
                                curr_min_y = tl_y - tile_h_m * rx
                                curr_max_y = tl_y - tile_h_m * (rx+1)
                                
                                res_m = (curr_max_x - curr_min_x) / tile_width
                                
                                r = requests.get(curr_tile_url, stream=True)
                                
                                if r.status_code == 200:
                                    img = Image.open(r.raw)
                                    img = np.array(img)
                                    
                                    #all pixels are equal
                                    if int(np.std(img)) == 0:
                                        continue
                                    
                                    tile_gt = [curr_min_x, res_m, 0, curr_min_y, 0, -res_m]

                                    tile_path = os.path.join(odir_wms, "%i_%i.tif" % (cx, rx))
                                    paths.append(tile_path)
                                    
                                    tile2png(img, tile_path, tms_crs, tile_gt)
                        
                        vrt_options = gdal.BuildVRTOptions()#resampleAlg='cubic', addAlpha=True)
                        vrt_path = os.path.join(os.path.dirname(odir_wms), "%s.vrt" % zlvl)
                        my_vrt = gdal.BuildVRT(vrt_path, paths, options=vrt_options)
                        my_vrt = None
                        
                        out_srs = osr.SpatialReference()
                        out_srs.ImportFromEPSG(int(tiles_data["epsg"]))
                        
                        for tile in tqdm(tiles_data["tiles"]):
                            kwargs = {'format': 'GTiff', 
                                    'outputBounds':[tile["min_xyz"][0], tile["min_xyz"][1], 
                                                    tile["max_xyz"][0], tile["max_xyz"][1]],
                                    'outputBoundsSRS':out_srs,
                                    'srcSRS':tms_crs,
                                    'dstSRS':out_srs,
                                    'xRes':res_m, 
                                    'yRes':res_m,
                                    'resampleAlg':'cubic',
                                    'creationOptions' : {"COMPRESS":"JPEG", "JPEG_QUALITY":50}}
                            ds = gdal.Warp(os.path.join(odir_tiles, "%s.tif" % (tile["tid"])), vrt_path, **kwargs)
                            del ds