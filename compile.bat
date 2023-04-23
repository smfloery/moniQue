@echo off
call "C:\Program Files\QGIS 3.26.1\bin\o4w_env.bat"
call "C:\Program Files\QGIS 3.26.1\bin\qt5_env.bat"
call "C:\Program Files\QGIS 3.26.1\bin\py3_env.bat"

@echo on
pyrcc5 -o resources.py resources.qrc