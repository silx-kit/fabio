FabIO 
=====
FabIO is an I/O library for images produced by 2D X-ray detectors and written in python.
FabIO support images detectors from a dozen of companies (including Mar, Dectris, ADSC, Hamamatsu, Oxford, ...), 
for a total of 20 different file formats (like CBF, EDF, TIFF, ...) and offers an unified interface to their 
headers (as a python dictionary) and datasets (as a numpy ndarray of integers or floats)
  


Changelog
=========
From FabIO-0.0.8 to FabIO-0.1.0:
- OXD reader improved and writer implemented
- Mar345 reader improved and writer implemented
- CBF writer implemented 
- Clean-up of the code & bug fixes 
- Move towards python3
- Make PIL optional dependency  
Python3 is not yet tested but some blocking points have been identified and some fixed. 

From FabIO-0.0.7 to FabIO-0.0.8:
- Support for Tiff using TiffIO module from V.A.Solé
- Clean-up of the code & bug fixes 

From FabIO-0.0.6 to FabIO-0.0.7:
- Support for multi-frames EDF files
- Support for XML images/2D arrays used in EDNA 
- new method: fabio.open(filename) that is an alias for fabio.openimage.openimage(filename)
 
From FabIO-0.0.4 to FabIO-0.0.6:
- Support for CBF files from Pilatus detectors
- Support for KCD files from Nonius Kappa CCD images 
- write EDF with their native data type (instead of uint16 by default)


Installation
============
fabio can be downloaded from the fable download page on sourceforge.net. Presently the source code has been distributed as a zip package and a compressed tarball. Download either one and unpack it.
http://sourceforge.net/projects/fable/files/fabio/

e.g.
tar xvzf fabio-0.1.0.tar.gz
or
unzip fabio-0.1.0.zip

all files are unpacked into the directory fabio-0.1.0. To install these do

cd fabio-0.1.0

and install fabio with

python setup.py install

most likely you will need to do this with root privileges (e.g. put sudo in front of the command).
The newest development version can be obtained by checking it out from the subversion (SVN) repository. Do

svn checkout https://svn.sourceforge.net/svnroot/fable/ fabio
cd fabio/trunk
sudo python setup.py install

If you are using MS Windows you also download a binary version packaged as executable installation files. 
Dependent on your python version open either:

fabio-0.1.0.win32-py2.6.msi or fabio-0.1.0.win32-py2.6.msi or fabio-0.0.8.win32-py2.7.msi


Dependencies
============
Python 2.5 or later (we are workin on python 3.x)
For full functionality of fabio the following modules need to be installed.
* numpy - http://www.numpy.org

Optional dependency
* PIL (python imaging library) - http://www.pythonware.com
* lxml (library for reading XSDimages) 

Ubuntu and Debian Like linux distributions:
-------------------------------------------

Fabio is included in latest development versions of Debian, it can be installed by apt-get:
sudo apt-get install python-fabio

If fabio is not yet available for you flavor of linux, you will need to install it from the sources:
To install the needed python modules can be installed either through the Synaptic Package Manager (found in System -> Administration) 
or using apt-get on from the command line in a terminal.
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
Fabio is expected to handle gzip and bzip2 compressed files transparently. 
Following a query about the performance of reading compressed data, some 
benchmarking details have been collected at fabio_compressed_speed. 
This means that when your python was configured and built you needed the 
bzip and gzip modules to be present (eg libbz2-dev package for ubuntu)
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


Design Specifications
=====================
Name: Fabio = Fable Input/Output 

Idea: 
-----
Have a base class for all our 2D diffraction greyscale images. This consists of a 2D array (numpy ndarray) 
and a python dictionary of header information in (string key, string value) pairs.

Class fabioimage  
----------------
Needs a name which will not to be confused with an RGB color image.

Class attributes:
* data   					-> 2D array
* header 					-> dictionary
* rows, columns, dim1, dim2 -> data.shape
* header_keys               -> header.keys() used to retain the order of the header when writing an image to disk
* bytecode                 	-> data.typecode()
* m, minval, maxval, stddev	-> image statistics, could add others, eg roi[slice]

Class methods (functions):
--------------------------
integrate_area()      -> return sum(self.data) within slice
rebin(fact)           -> rebins data, adjusts dims
toPIL16()             -> returns a PILimage
getheader()           -> returns self.header
resetvals()           -> resets the statistics
getmean()             -> (computes) returns self.m
getmin()              -> (computes) returns self.minval
getmax()              -> (computes) returns self.maxval
getstddev()           -> (computes) returns self.stddev
read()        		  -> read image from file [or stream, or shared memory]
write()       		  -> write image to file  [or stream, or shared memory]
readheader()          -> read only the header [much faster for scanning files]

Each individual file format would then inherit all the functionality of this class and just make new read and write methods.
There are also fileseries related methods (next(), previous(), ...) which return a fabioimage instance of the next/previous frame in a fileserie 

Other feature:
    * possibility for using on-the-fly external compression - i.e. if files are stored as something as .gz, .bz2 etc could decompress them, using an external compression mechanism (if available). This is present in fabian but requires that images are edfs. 


Known file formats
===================
* Bruker
  o brukerimage
  o bruker100image
  o kcdimage: Nonius KappaCCD diffractometer
* Mar Research
  o marccd (fileformat derived from Tiff)
  o mar345 imaging plate
* Dectris 
  o cbfimage (implements a fast byte offset decompression scheme in python/cython)
  o pilatusimage (fileformat derived from Tiff)
* ESRF
  o edfimage: The ESRF data Format 
  o xsdimage: XML serialized image from EDNA
  o fit2dmaskimage: Fit2d Mask format
  o fit2dspreadsheetimage: Fit2d ascii tables (spread-sheet)
* ADSC
  o adscimage 
* GE detector at APS
  o GEimage 
* PNM
  o pnmimage 
* Tiff
  o tifimage  
* D3M
  o d3mimage
* Hamamatsu
  o HiPiCimage 
* Oxford Diffraction Sapphire 3 
  o OXDimage
 
  
