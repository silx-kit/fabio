#!/bin/sh
rm -rf dist
python3 setup.py sdist
cd dist
tar -xzf  fabio-*.tar.gz
cd fabio*
export DEB_BUILD_OPTIONS=nocheck
python3 setup.py --command-packages=stdeb.command sdist_dsc --no-python3-scripts=True bdist_deb
#python setup.py --command-packages=stdeb.command bdist_deb
sudo dpkg -i deb_dist/python-fabio*.deb
sudo dpkg -i deb_dist/python3-fabio*.deb
cd ../..

