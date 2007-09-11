cd ..
python2.5 setup.py build
export PYTHONPATH=../build/lib.linux-i686-2.5
cd test
python2.5 testedfimage.py
python2.5 testfabioimage.py
python2.5 testfilenames.py
python2.5 testmccdimage.py

cd ..
python2.4 setup.py build
export PYTHONPATH=../build/lib.linux-i686-2.4
cd test
python2.4 testedfimage.py
python2.4 testfabioimage.py
python2.4 testfilenames.py
python2.4 testmccdimage.py
