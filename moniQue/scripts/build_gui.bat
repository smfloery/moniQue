REM call "C:\Program Files\QGIS 3.28.5\bin\o4w_env.bat"
REM call "C:\Program Files\QGIS 3.28.5\bin\qt5_env.bat"
REM call "C:\Program Files\QGIS 3.28.5\bin\py3_env.bat"

cd /d "C:\Users\sfloe\Software\moniQue\moniQue\"

pyuic5 --import-from ".."  --resource-suffix "" .\gui\mono_plot_dialog_base.ui > .\gui\mono_plot_dialog_base.py & ^
pyuic5 --import-from "" --resource-suffix "" .\gui\mono_plot_create_dialog.ui > .\gui\mono_plot_create_dialog.py & ^
pyuic5 --import-from "" --resource-suffix "" .\gui\mono_plot_change_name_dialog.ui > .\gui\mono_plot_change_name_dialog.py & ^
pyuic5 --import-from "" --resource-suffix "" .\gui\mono_plot_create_ortho_dialog.ui > .\gui\mono_plot_create_ortho_dialog.py & ^
pyuic5 --import-from "" --resource-suffix "" .\gui\mono_plot_orient_dialog.ui > .\gui\mono_plot_orient_dialog.py