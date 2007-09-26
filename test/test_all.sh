cd ..
export PYT=python2.5
$PYT setup.py build
export PYTHONPATH=../build/lib.linux-i686-2.5
cd test
$PYT testedfimage.py
$PYT testfabioimage.py
$PYT testfilenames.py
$PYT testmccdimage.py
$PYT testfit2dmaskimage.py
$PYT testbrukerimage.py
