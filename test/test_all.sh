
echo "Deprecated !!!"
exit 0

cd ..
export PYT=python
$PYT setup.py build
export PYTHONPATH=../build/lib.linux-x86_64-2.6
cd test

# ls *.py | awk '{print "$PYT",$1}'

$PYT testheadernotsingleton.py
$PYT testadscimage.py
$PYT testbrukerimage.py
$PYT testedfimage.py
$PYT testfabioimage.py
$PYT testfilenames.py
$PYT test_filename_steps.py
$PYT test_file_series.py
$PYT testfit2dmaskimage.py
$PYT testGEimage.py
$PYT testmar345image.py
$PYT testmccdimage.py
$PYT testopenheader.py
$PYT testopenimage.py
$PYT testOXDimage.py
$PYT testtifgz.py

$PYT test_all_images.py > `hostname`_benchmark
$PYT benchheader.py > `hostname`_benchheaders

