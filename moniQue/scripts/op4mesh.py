import os
import geopandas as gpd
from osgeo import gdal, osr
import numpy as np
from pyproj import CRS
from pyproj.transformer import Transformer
import shapely
import json
from tqdm import tqdm 
if __name__ == "__main__":
    
    # op_path = "C:\\Users\\sfloery\\Downloads\\felix\\op_solnhofen_20cm_utm32.vrt"
    op_path = "D:\\1_PROJECTS\\01_SEHAG\\05_STEREO_PAIRS\\mt_stereo\\op_stereo_25832_1m.vrt"
    op_path = "C:\\Users\\sfloery\\Downloads\\gp_sued_sulden_10000\\suldental_1m_25832.vrt"
    
    op_data = gdal.Open(op_path)
    op_proj = osr.SpatialReference(wkt=op_data.GetProjection())
    op_epsg = op_proj.GetAttrValue('AUTHORITY', 1)
    op_gt = op_data.GetGeoTransform()
    
    # json_path = "D:\\4_DATASETS\\HABER\\solnhofen_1m_utm32_felix\\tiles.json"  
    # json_path = "D:\\1_PROJECTS\\01_SEHAG\\05_STEREO_PAIRS\\mt_stereo\\tiles.json"      
    json_path = "D:\\4_DATASETS\\monique\\suldental\\tiles.json"
    
    with open(json_path, "r") as f:
        tiles_data = json.load(f)
    
    tiles_epsg = tiles_data["epsg"]
    
    print(tiles_epsg, op_epsg)
    
    # assert op_epsg == tiles_epsg
    
    op_dir = os.path.join(os.path.dirname(json_path), "op", "17_mesh")
    if not os.path.exists(op_dir):
        os.makedirs(op_dir)    
    
    for tile in tqdm(tiles_data["tiles"]):
        tid = tile["tid"]
        out_path = os.path.join(op_dir, "%s.tif" % (tid))
        
        min_xyz = tile["min_xyz"]
        max_xyz = tile["max_xyz"]
        
        bbox = [min_xyz[0], min_xyz[1], max_xyz[0], max_xyz[1]]
        
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(int(tiles_epsg))
        
        inp_srs = osr.SpatialReference()
        inp_srs.ImportFromEPSG(int(op_epsg))
        
        kwargs = {'format': 'GTiff', 
                'outputBounds':bbox,
                'outputBoundsSRS':out_srs,
                'srcSRS':inp_srs,
                'dstSRS':out_srs,
                'xRes':op_gt[1], 
                'yRes':op_gt[5],
                'resampleAlg':'cubic'}
        ds = gdal.Warp(out_path, op_path, **kwargs)
        del ds    
        
    
    
    
    