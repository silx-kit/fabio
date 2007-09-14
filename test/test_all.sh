cd ..
export PYT=/sware/exp/fable/standalone/suse82/bin/python
$PYT setup.py build
export PYTHONPATH=../build/lib.linux-i686-2.5
cd test
$PYT testedfimage.py
$PYT testfabioimage.py
$PYT testfilenames.py
$PYT testmccdimage.py

