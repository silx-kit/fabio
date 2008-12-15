cd ..
set PYT=c:\python25\python
%PYT% setup.py build --compiler=mingw32
set PYTHONPATH=..\build\lib.win32-2.5
cd test

%PYT% testheadernotsingleton.py
%PYT% testadscimage.py
%PYT% testbrukerimage.py
%PYT% testedfimage.py
%PYT% testfabioimage.py
%PYT% testfilenames.py
%PYT% test_filename_steps.py
%PYT% test_file_series.py
%PYT% testfit2dmaskimage.py
%PYT% testGEimage.py
%PYT% testmar345image.py
%PYT% testmccdimage.py
%PYT% testopenheader.py
%PYT% testopenimage.py
%PYT% testOXDimage.py
%PYT% testtifgz.py

%PYT% test_all_images.py > win32_benchmark
%PYT% benchheader.py > win32_benchheaders
:END
