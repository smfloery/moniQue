import os
import geopandas as gpd
from osgeo import gdal, osr
import numpy as np
from pyproj import CRS
from pyproj.transformer import Transformer
import shapely

if __name__ == "__main__":

    gpkg_path = "C:\\Users\\David\\Documents\\TU-Job\\DATA\\AOIs\\grossvenediger_25km.gpkg"
    out_path = "C:\\Users\\David\\Documents\\TU-Job\\DATA\\AOIs\\grossvenediger_25km.tif"

    dgm_path = "C:\\Users\\David\\Documents\\TU-Job\\DATA\\AUSTRIA\\dhm_at_lamb_10m_2018.tif"
    dgm_data = gdal.Open(dgm_path)
    dgm_proj = osr.SpatialReference(wkt=dgm_data.GetProjection())
    dgm_epsg = dgm_proj.GetAttrValue('AUTHORITY', 1)
    dgm_gt = dgm_data.GetGeoTransform()
    
    gpd_gpkg = gpd.read_file(gpkg_path)
    
    gpkg_epsg = gpd_gpkg.crs.to_epsg()
            
    gpkg_bounds = gpd_gpkg["geometry"].bounds.values[0]
    minx, miny, maxx, maxy = np.floor(gpkg_bounds).astype(np.int32)
    
    out_srs = osr.SpatialReference()
    out_srs.ImportFromEPSG(int(gpkg_epsg))
    
    inp_srs = osr.SpatialReference()
    inp_srs.ImportFromEPSG(int(dgm_epsg))
    
    kwargs = {'format': 'GTiff', 
            'outputBounds':[minx, miny, maxx, maxy],
            'outputBoundsSRS':out_srs,
            'srcSRS':inp_srs,
            'dstSRS':out_srs,
            'xRes':dgm_gt[1], 
            'yRes':dgm_gt[5],
            'resampleAlg':'cubic'}
    ds = gdal.Warp(out_path, dgm_path, **kwargs)
    del ds    
    
    
    
    
    