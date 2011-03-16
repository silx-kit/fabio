FabIO 
=====

FabIO is an I/O library for diffraction images written in python. It combines the functionalities which evolved in Fabian and ImageD11.
The design specification can be viewed at: PyImageIO.

Changelog from FabIO-0.0.6 to FabIO-0.0.7:
- Support for mutli-frames EDF files
- Support for XML images/2D arrays used in EDNA 
- new method: fabio.open(filename) that is an alias for fabio.openimage.openimage(filename)
 
Changelog from FabIO-0.0.4 to FabIO-0.0.6:
- Support for CBF files from Pilatus detectors
- Support for KCD files from Nonius Kappa CCD images 
- write EDF with their native data type (instead of uint16 by default)

Installation
============
fabio can be downloaded from the fable download page on sourceforge.net. Presently the source code has been distributed as a zip package and a compressed tarball. Download either one and unpack it.
http://sourceforge.net/projects/fable/files/fabio/

e.g.
tar xvzf fabio-0.0.7.tar.gz
or
unzip fabio-0.0.7.zip

all files are unpacked into the directory fabio-0.0.7. To install these do

cd fabio-0.0.7

and install fabio with

python setup.py install

most likely you will need to do this with root privileges (e.g. put sudo in front of the command).
The newest development version can be obtained by checking it out from the subversion (SVN) repository. Do

svn checkout https://svn.sourceforge.net/svnroot/fable/ fabio
cd fabio/trunk
sudo python setup.py install

If you are using MS Windows you also download a binary version packaged as executable installation files. Dependant on your python version open either

fabio-0.0.7.win32-py2.4.exe

or

fabio-0.0.7.win32-py2.5.exe

Dependencies
============

Python 2.5 or later (but not python 3.0)
For full functionality of fabio the following modules need to be installed.

    * PIL (python imaging library) - http://www.pythonware.com
    * numpy - http://www.numpy.org 

Ubuntu and Debian Like linux distributions:
-------------------------------------------
To use fabio on Ubuntu (a linux distribution based on Debian) the needed python modules can be installed either through the Synaptic Package Manager (found in System -> Administration) or using apt-get on from the command line in a terminal.
The extra ubuntu packages needed are:

    * python-imaging
    * python-imaging-tk
    * python-numpy
    * python-dev

using apt-get these can be installed as:

sudo apt-get install python-imaging python-imaging-tk python-numpy


using Synaptic Package Manager:

**search** to find the specific ubuntu packages instead
**mark** them for installation
**Apply** to install

Transparent handling of compressed files
========================================

Fabio is expected to handle gzip and bzip2 compressed files transparently. Perhaps also zip if someone adds it. Following a query about the performance of reading compressed data, some benchmarking details have been collected at fabio_compressed_speed. This means that when your python was configured and built you needed the bzip and gzip modules to be present (eg libbz2-dev package for ubuntu)
Using fabio in your own python programs 
Example:

>>> import fabio
>>> obj = fabio.edfimage("mydata0000.edf")
>>> obj.data.shape
(2048, 2048)
>>> obj.header["Omega"]
23.5

Adding new file formats 
=======================

We hope it will be relatively easy to add new file formats to fabio in the future. The basic idea is the following:

   1. inherit from fabioimage overriding the methods _readheader, read and optionally write. Name your new module XXXimage where XXX means something (eg tifimage).
   2. readheader fills in a dictionary of "name":"value" pairs in self.header. No one expects to find anything much in there.
   3. read fills in self.data with a numpy array holding the image. Some redundant info which also appears are self.dim1 and self.dim2: the image dimensions, self.bpp is the bytes per pixel and self.bytecode is the numpy.dtype.type of the data.
   4. The member variables "_need_a_seek_to_read" and "_need_a_real_file" are there in case you have trouble with the transparent handling of bz2 and gz files.
   5. Register the file type (extension naming) in init__.py:FILETYPES
   6. Add your new module as an import into fabio.openimage
   7. Fill out the magic numbers for your format in fabio.openimage if you know them (the characteristic first few bytes in the file)
   8. Upload a testimage to the file release system and create a unittest testcase which opens an example of your new format, confirming the image has actually been read in successfully (eg check the mean, max, min and esd are all correct, perhaps orientation too)
   9. Run pylint on your code and then please go clean it up. Have a go at mine while you are at it.
  10. Bask in the warm glow of appreciation when someone unexpectedly learns they don't need to convert their data into another format 

