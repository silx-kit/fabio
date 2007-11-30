
cd ..
export PYT=python2.5
$PYT setup.py build
export PYTHONPATH=../build/lib.linux-i686-2.5
cd test

# ls *.py | awk '{print "$PYT",$1}'

$PYT testadscimage.py
$PYT testbrukerimage.py
$PYT testedfimage.py
$PYT testfabioimage.py
$PYT testfilenames.py
$PYT test_filename_steps.py
$PYT test_file_series.py
$PYT testfit2dmaskimage.py
$PYT testGEimage.py
$PYT testmccdimage.py
$PYT testopenimage.py
$PYT testOXDimage.py
$PYT testtifgz.py
$PYT testopenheader.py