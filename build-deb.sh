#!/bin/sh
rm -rf deb_dist
python setup.py --command-packages=stdeb.command bdist_deb
sudo dpkg -i deb_dist/python-fabio*.deb

