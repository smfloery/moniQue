import sys
sys.path.append(r"C:\Users\David\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\moniQue")

import argparse
from terramesh import MeshGrid

# dtm_path = "E:\sehag\kt_dtm_2017_1m.tif"
# out_dir = "C:\\Users\\sfloe\\Desktop\\kt_dtm_2017_1m_tiles_a"

# dtm_path = "D:\\1_PROJECTS\\01_SEHAG\\02_REGIONS\\02_kaunertal\\01_DTM\\1m_land_tirol\\kt_dtm_2017_1m.tif"
# out_dir = "D:\\1_PROJECTS\\01_SEHAG\\02_REGIONS\\02_kaunertal\\01_DTM\\1m_land_tirol\\tiles_grid_new"

# dtm_path = "D:\\4_DATASETS\\at_10m_tirol\\at_10m_tirol.tif"
# out_dir = "D:\\4_DATASETS\\at_10m_tirol\\grid_neu\\"

# dtm_path = "D:\\4_DATASETS\\at_10m_tirol\\at_10m_tirol_25832.tif"
# out_dir = "D:\\4_DATASETS\\at_10m_tirol\\grid_25832\\"

# dtm_path = "D:\\4_DATASETS\\AKON\\grossglockner_25km_10m_25833.tif"
# out_dir = "D:\\4_DATASETS\\AKON\\grossglockner_25km_10m_25833"

# dtm_path = "D:\\4_DATASETS\\AKON\\innsbruck_25km_10m_25832.tif"
# out_dir = "D:\\4_DATASETS\\AKON\\innsbruck_25km_10m_25832"

# dtm_path = "D:\\4_DATASETS\\AKON\\bozen_25km_10m_25832.tif"
# out_dir = "D:\\4_DATASETS\\AKON\\bozen_25km_10m_25832"

dtm_path = "C:\\Users\\David\\Documents\\TU-Job\\DATA\\AOIs\\grossvenediger_25km.tif"
out_dir = "C:\\Users\\David\\Documents\\TU-Job\\QGIS\\grossvenediger_25km"
# dtm_path = "D:\\4_DATASETS\\AKON\\wolkenstein_25km_10m_25832.tif"
# out_dir = "D:\\4_DATASETS\\AKON\\wolkenstein_25km_10m_25832_lod"

# dtm_path = "C:\\Users\\sfloery\\Desktop\\lech_25km_1m.tif"
# out_dir = "D:\\4_DATASETS\\AKON\\lech_25km_1m_25832_lod"

# tile_grid = MeshGrid(path=dtm_path, tile_size=2048, max_error=1)
# tile_grid.snap_boundaries()
# tile_grid.save_tiles(odir=out_dir, olvl="1")

# tile_grid = MeshGrid(path=dtm_path, tile_size=2048, max_error=5)
# tile_grid.snap_boundaries()
# tile_grid.save_tiles(odir=out_dir, olvl="2", save_json=False)

# tile_grid = MeshGrid(path=dtm_path, tile_size=2048, max_error=10)
# tile_grid.snap_boundaries()
# tile_grid.save_tiles(odir=out_dir, olvl="3", save_json=False)

# tile_grid.merge_tiles(opath=mesh_path)

# dtm_path = "C:\\Users\\sfloery\\Downloads\\felix\\dgm_solnhofen_1m_utm32.tif"
# out_dir = "D:\\4_DATASETS\\HABER\\solnhofen_1m_utm32_felix"

# dtm_path = "D:\\1_PROJECTS\\01_SEHAG\\05_STEREO_PAIRS\\mt_stereo_10m.tif"
# out_dir = "D:\\1_PROJECTS\\01_SEHAG\\05_STEREO_PAIRS\\mt_stereo"

dtm_path = "D:\\4_DATASETS\\monique\\suldental\\suldental_10m.tif"
out_dir = "D:\\4_DATASETS\\monique\\suldental"

tile_grid = MeshGrid(path=dtm_path, tile_size=1024, max_error=1)
tile_grid.snap_boundaries()
tile_grid.save_tiles(odir=out_dir, olvl="1")
