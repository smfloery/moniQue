REM call "C:\Program Files\QGIS 3.28.5\bin\o4w_env.bat"
REM call "C:\Program Files\QGIS 3.28.5\bin\qt5_env.bat"
REM call "C:\Program Files\QGIS 3.28.5\bin\py3_env.bat"

cd /d "H:\py_projects\moniQue\moniQue"

pyuic5 --import-from ".."  --resource-suffix "" .\gui\src\mono_dlg_base.ui > .\gui\src\mono_dlg_base.py & ^
pyuic5 --import-from "" --resource-suffix "" .\gui\src\create_dlg_base.ui > .\gui\src\create_dlg_base.py & ^
pyuic5 --import-from "" --resource-suffix "" .\gui\src\change_name_dlg_base.ui > .\gui\src\change_name_dlg_base.py & ^
pyuic5 --import-from "" --resource-suffix "" .\gui\src\create_ortho_dlg_base.ui > .\gui\src\create_ortho_dlg_base.py & ^
pyuic5 --import-from ".." --resource-suffix "" .\gui\src\orient_dlg_base.ui > .\gui\src\orient_dlg_base.py