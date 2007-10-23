cd ..
export PYT=python2.5
$PYT setup.py build
export PYTHONPATH=../build/lib.linux-i686-2.5
cd test

$PYT testfabioimage.py
$PYT testfilenames.py
$PYT test_file_series.py
$PYT testopenimage.py
$PYT testedfimage.py
$PYT testmccdimage.py
$PYT testfit2dmaskimage.py
$PYT testbrukerimage.py
$PYT testadscimage.py
$PYT testtifgz.py
$PYT test_filename_steps.py
