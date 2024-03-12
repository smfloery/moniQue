# moniQue
QGIS plugin for monoplotting of oblique images.

## Installation
Open the OSGeo4W Shell and install From the OSGeo4W Shell install required python packages using pip  

    pip install --user open3d pygfx lmfit pymartini

`open3d` is required for raycasting, `pygfx` for rendering the terrain in 3D, `lmfit` for the least squares spatial resection `pymartini` for the simplifcation of the initial digital terrain model (DTM). Installation with the `--user` option is required as the default QGIS Python Interpreter is located on C:\ which would require admin rights.  

AFter installing the additional Python packages you can install the plugin 

## Usage
### Terrain simplification
For the rendering of the terrain in 3D and raycasting we represent the terrain as mesh. If you already have a DTM as mesh you can directly use it and skip this step. Otherwise moniQque offers the functionality to convert an existing DTM, available as grid (.tif), to a simplified mesh (.ply). Go to `Plugins -> moniQue -> Convert DTM to mesh` which opens a new dialog. From the new dialog select the input grid, output path and the maximum error of the simplified mesh.

### Create new project

### Spatial resection

### Monoplotting