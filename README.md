![moniQue - Header](./moniQue/doc/monique_header_hr.jpg)

## Supported QGIS versions
We tested moniQue with the following QGIS versions:
| Version  | OS | Python |
| --- | --- | --- |
| 3.34.3 | Windows | Python 3.11
| 3.34.15 (LTR) | Windows | Python 3.12
| 3.34.40 | Windows | Python 3.12
| 3.40.5 (LTR) | Windows | Python 3.12

## Installation
### Required Python packages
Open the **OSGeo4W Shell** and install the required python packages using pip  

    pip install --user open3d pygfx==0.9.0 glfw lmfit

`open3d` is required for raycasting, `pygfx` and `glfw` for rendering the terrain in 3D, `lmfit` for the least squares spatial resection. Installation with the `--user` option is necessary as the default QGIS Python interpreter is located on ```C:\...``` which would require admin rights.  

> [!IMPORTANT]
> We recently switched to the newest version of pygfx which introduced some breaking changes. Hence, it might be necessary to upgrade pygfx!

### Plugin
<!-- After installing the additional Python packages, **moniQue** can be installed like any other QGIS plugin from `Plugins -> Manage plugins`. After the succesful installation you should see the logo in the QGIS main toolbar and a new entry in the `Plugin` menu is available. -->
> [!IMPORTANT]
> The provided version in the QGIS plugin repository is currently depreceated.
> Therefore it is recommended to use the current version of the plugin from 
> here. 

Click on ``Code`` and ``Download ZIP``. From the downloaded ZIP only the ``moniQue`` subdirectory is required. Create a new archive which only contains this directory. In QGIS go to `Plugins -> Mange and install plugins --> Install from ZIP` and select the newly created ZIP. 

## Usage
### Mesh generation
moniQue requires a digital terrain model (DTM) as mesh in the PLY format. We recommened to use [monique-helper](https://github.com/smfloery/moniQue-helper) to generate the mesh tiles as well as orthophoto tiles used to texture the mesh.

### Creat a new project from JSON
To create a new project select `File -> Create from *.json` in the moniQue main window. Select the .json file that was previously created with [monique-helper](https://github.com/smfloery/moniQue-helper). moniQue will now convert all the data and create a new monoplotting project. 

### Importing images
Images can be imported through `Images -> Import images`. The names of the images must be unique. It is recommened that the names do not contain special characters (&,ä,ö,...) or white spaces. To display an image in the image canvas, it has to be selected from the image list.

### Image orientation
The unknown camera parameters (exterior and interior orientation) are calculated by spatial resection. As 7 parameters are assumed to be unknown (coordinates of the projection center, euler angles, focal length), at least 4 ground control points (GCPs) are required. To identify GCPs both in image and object space open the spatial resection dialog click from the main dialog toolbar. As long as this dialog is opened, GCPs can be selected and edited. Both in the images and 3D canvas a new GCP can be added by clicking `Ctrl + Left Mouse`. This will open a new dialog where the ID of the GCP can be set. The image and object coordinates of GCPs are linked by their ID. Hence, if an image GCP and object GCP have the same ID, they will be treated together as one GCP. 

Furthermore, initial estimates for the unknown camera paramters are required. One of the advantadges of displaying the terrain in 3D is that the 3D viewer can be used for obtaining those values. Hence, first align the camera of the 3D viewer in such a way that it resembles the historical image. Subsequently, clicking on the icon above the camera paramters will automatically extract the required values from the 3D view. 

Now the spatial resection can be calcuted by clicking `Calculate`. If the calculation was successful, the 3D camera is automatically set to the calculated camera parameters. Furthermore, the historical image can be rendered in the 3D view to visually inspect the estimation result (Image icon in the main dialog). With the mouse wheel you can translate the historical image along the viewing direction. Within the spatial resection dialog one can see the estimated camera parameters, standard deviations and image residuals. To save the result, click `Save`. By that, the estimated camera parameters and GCP configuration will be saved to the project file.

In some cases, the estimated position of the camera will be below ground or behind a hill. This is mainly related to the simultaneous estimation of the coordinates of the projection center and the focal length. However, the estimated euler angles are quite accurate whereas only the position of the camera is displaced along the acquisition direction. Hence, to manually correct this one can mannually displace the camera along the acquisition direction. Open the "Displace camera along viewing direction" in the spatial resection dialog. This will open a line plot showing the profile of the terrain alogn the acqusition direction as well as the height of the camera. By selecting a new position within this plot the camera will be updated. 

### Monoplotting
After the camera parameters have been estimated, we can now use monoplotting. By that, object coordinates of the image pixels are directly obtained by intersection the projection rays with the terrain. Thus, one can directly document features of interest in the image. To activate monoplotting click the icon next to the camera symbol in the main dialog. If you now move your mouse over the image canvas, moniQue automatically intersects the respective image rays with the terrain mesh. As a result you see the intersection point in the QGIS main canvas. By clicking the left mouse button vertices of a polyline are created and stored. You can finish a polyline by clicking the right mouse button.

![moniQue - Main dialog](./moniQue/doc/monoplot.gif)

### Shortcuts
| Key(s)  | Action | Canvas
| --- | --- | --- |
| Left Mouse (drag) | Rotate camera / Translate Image | 3D / Image
| Mouse wheel | Zoom | 3D & Image
| Right Mouse (drag) | Translate camera | 3D
| Strg + Left click | Add GCP | 3D & Image (during orientation)
| Strg + Right click | Zoom to position | 3D
| Strg + Mouse wheel | Adjust FOV | 3D
| ALG + Right click  | Go back to previous position | 3D
| A W S D | Move camera in object space | 3D
| &uarr;  &darr;  &larr;  &rarr; | Rotate camera in object space | 3D
| Q E | Tilt camera | 3D
| F1 | Store current camera as .json | 3D

## Funding
moniQue was developed within the SEHAG project which was funded by the DFG (Deutsche Forschungsgemeinschaft) under the grant [FOR 2793](https://gepris.dfg.de/gepris/projekt/394200609) and FWF (Österreichischer Wissenschaftsfond) under the grant [I 4062](https://www.fwf.ac.at/forschungsradar/10.55776/I4062). 

## Contact
Sebastian Mikolka-Flöry (sebastian.floery@geo.tuwien.ac.at)

## References
