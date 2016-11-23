#!/bin/sh
rm -rf dist
python setup.py sdist
cd dist
tar -xzf  fabio-*.tar.gz
cd fabio*
export DEB_BUILD_OPTIONS=nocheck
if [ $1 = 3 ]
then
  echo Python 2+3 
  python3 setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True --with-python3=True --no-python3-scripts=True bdist_deb
  sudo dpkg -i deb_dist/python3-fabio*.deb
else
  echo Python 2
  python setup.py --command-packages=stdeb.command bdist_deb
fi
sudo dpkg -i deb_dist/python-fabio*.deb
cd ../..

