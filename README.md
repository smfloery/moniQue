# moniQue
QGIS plugin for monoplotting of oblique images.

## Installation
### Additional python packages
From the OSGeo4W Shell install the additional packages using pip
pip install --user open3d pygfx

--user is required as the default QGIS Python Interpreter is located on C:\ which would require admin rights.
Using --user installs the additional packages in C:\Users\$USER\AppData\Roaming\Python\Python39. This might
interfere with an already existing Pytho39 installation?