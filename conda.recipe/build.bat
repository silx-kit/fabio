%PYTHON% setup.py install --old-and-unmanageable

for %%G in (fabio_viewer.py) DO (
copy /Y %RECIPE_DIR%\temp.exe %SCRIPTS%\%%G.exe
move /Y %SCRIPTS%\%%G %SCRIPTS%\%%G-script.py)

if errorlevel 1 exit 1
