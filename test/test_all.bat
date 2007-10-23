cd ..
set PYT=c:\python25\python
%PYT% setup.py build --compiler=mingw32
set PYTHONPATH=..\build\lib.win32-2.5
cd test



%PYT% testopenimage.py
%PYT% testfilenames.py
%PYT% testfabioimage.py
%PYT% test_file_series.py
%PYT% testedfimage.py
%PYT% testmccdimage.py
%PYT% testfit2dmaskimage.py
%PYT% testbrukerimage.py
%PYT% testadscimage.py
%PYT% testtifgz.py
%PYT% test_filename_steps.py
:END
