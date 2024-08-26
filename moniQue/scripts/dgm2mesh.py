import sys
sys.path.append(r"H:\Software\moniQue\monique")

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

dtm_path = "D:\\4_DATASETS\\AKON\\bozen_25km_10m_25832.tif"
out_dir = "D:\\4_DATASETS\\AKON\\bozen_25km_10m_25832"

tile_grid = MeshGrid(path=dtm_path, tile_size=512, max_error=1)
tile_grid.snap_boundaries()
tile_grid.save_tiles(odir=out_dir)

# tile_grid.merge_tiles(opath=mesh_path)
