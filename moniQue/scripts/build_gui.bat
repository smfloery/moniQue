call "C:\Program Files\QGIS 3.26.1\bin\o4w_env.bat"
call "C:\Program Files\QGIS 3.26.1\bin\qt5_env.bat"
call "C:\Program Files\QGIS 3.26.1\bin\py3_env.bat"

pyuic5 --import-from ".."  --resource-suffix "" ./gui/mono_plot_dialog_base.ui > ./gui/mono_plot_dialog_base.py & ^
pyuic5 --import-from "" --resource-suffix "" ./gui/mono_plot_create_dialog.ui > ./gui/mono_plot_create_dialog.py & ^
pyuic5 --import-from "" --resource-suffix "" ./gui/mono_plot_change_name_dialog.ui > ./gui/mono_plot_change_name_dialog.py & ^
pyuic5 --import-from "" --resource-suffix "" ./gui/mono_plot_create_ortho_dialog.ui > ./gui/mono_plot_create_ortho_dialog.py