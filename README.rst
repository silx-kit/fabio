FabIO: Fable Input/Output library
=================================

Main websites:

 * https://github.com/silx-kit/fabio
 * http://fable.sf.net (historical)


|Build Status| |Appveyor Status|

----

FabIO is an I/O library for images produced by 2D X-ray detectors and written in Python.
FabIO support images detectors from a dozen of companies (including Mar, Dectris, ADSC, Hamamatsu, Oxford, ...),
for a total of 30 different file formats (like CBF, EDF, TIFF, ...) and offers an unified interface to their
headers (as a Python dictionary) and datasets (as a numpy ndarray of integers or floats)


.. contents::
    :depth: 1

Installation
------------

FabIO is available from `PyPI <https://pypi.python.org/pypi/fabio>`_:

``pip install fabio``


`Debian/Ubuntu packages <http://www.silx.org/pub/debian/binary/>`_, and
`wheels <http://www.silx.org/pub/wheelhouse/>`_ are available
for Windows, Linux and MacOSX from the silx repository. 

See the `installation instructions <http://www.silx.org/doc/fabio/latest/install.html>`_ for more information.

Usage
-----

Open an image
.............

  >>> import fabio
  >>> obj = fabio.open("mydata0000.edf")
  >>> obj.data.shape
  (2048, 2048)
  >>> obj.header["Omega"]
  23.5
  >>> obj.data
  array([...])

Save an image (ex: EDF)
.......................

  >>> import fabio
  >>> obj = fabio.edfimage.EdfImage(data=[...])
  >>> obj.write("mydata0000.edf")


Documentation
-------------

See the `latest release documentation <http://www.silx.org/doc/fabio/latest/>`_ for further details.

Documentation of previous versions are available on `silx <http://www.silx.org/doc/fabio/>`_.

Changelog
---------

See http://www.silx.org/doc/fabio/latest/Changelog.html


Citation
--------

The general philosophy of the library is described in:
`FabIO: easy access to two-dimensional X-ray detector images in Python; E. B. Knudsen, H. O. Sørensen, J. P. Wright, G. Goret and J. Kieffer Journal of Applied Crystallography, Volume 46, Part 2, pages 537-539. <http://dx.doi.org/10.1107/S0021889813000150>`_

Transparent handling of compressed files
----------------------------------------

For FabIO to handle gzip and bzip2 compressed files transparently, ``bzip`` and ``gzip`` modules must be present when installing/building Python (e.g. ``libbz2-dev`` package for Ubuntu).

Benchmarking details have been collected at http://www.silx.org/doc/fabio/latest/performances.html.



Supported file formats
----------------------

* ADSC:

  + AdscImage

* Bruker:

  + BrukerImage
  + Bruker100Image
  + KcdImage: Nonius KappaCCD diffractometer

* D3M

  + D3mImage

* Dectris:

  + CbfImage (implements a fast byte offset de/compression scheme in python/cython)
  + PilatusImage (fileformat derived from Tiff)
  + EigerImage (derived from HDF5/NeXus format, depends on `h5py`)

* ESRF:

  + EdfImage: The ESRF data Format
  + XsdImage: XML serialized image from EDNA
  + Fit2dImage: Fit2d binary format
  + Fit2dmaskImage: Fit2d Mask format
  + Fit2dSpreadsheetImage: Fit2d ascii tables (spread-sheet)
  + LimaImage: image stacks written by the LImA aquisition system
  + SparseImage: single crystal diffractions images written by pyFAI

* General Electrics 

  + GEimage (including support for variant used at APS) 

* Hamamatsu

  + HiPiCImage

* HDF5: generic format for stack of images based on h5py

  + Hdf5Image
  + EigerImage
  + LimaImage
  + SparseImage

* JPEG image format:
  
  + JPEG using PIL
  + JPEG 2000 using Glymur 
  
* Mar Research:

  + MarccdImage (fileformat derived from Tiff)
  + Mar345Image imaging plate with PCK compression

* MPA multiwire 

  +	MpaImage

* Medical Research Council file format for 3D electron density and 2D images

  + MrcImage

* Nonius -> now owned by Bruker
  
  + KcdImage 

* Numpy: generic reader for 2D arrays saved

  + NumpyImage 

* Oxford Diffraction Sapphire 3

  + OXDimage uncompressed or with TY1 or TY5 compression scheme
  + Esperanto format (with bitfield compression)

* Pixirad Imaging

  + PixiImage
   
* PNM

  + PnmImage

* Princeton Instrument SPE

  + SpeImage

* Raw Binary without compression

* Rigaku

  + RaxisImage
  + DtrekImage
  
* Tiff

  + TifImage using either:
  	- Pillow (external dependency)
  	- TiffIO taken from PyMca



Design Specifications
---------------------

Name: 
.....

FabIO = Fable Input/Output

Idea:
.....

Have a base class for all our 2D diffraction greyscale images.
This consists of a 2D array (numpy ndarray)
and a python dictionary (actually an ordered dict) of header information in (string key, string value) pairs.

Class FabioImage
................

Needs a name which will not to be confused with an RGB color image.

Class attributes, often exposed as properties:

* data   					-> 2D array
* header 					-> ordered dictionary
* rows, columns, dim1, dim2 -> data.shape (propertiy)
* header_keys               -> property for list(header.keys()), formerly used to retain the order of the header
* bytecode                 	-> data.typecode() (property)
* m, minval, maxval, stddev	-> image statistics, could add others, eg roi[slice]

Class methods (functions):

* integrate_area()      -> return sum(self.data) within slice
* rebin(fact)           -> rebins data, adjusts dims
* toPIL16()             -> returns a PILimage
* getheader()           -> returns self.header
* resetvals()           -> resets the statistics
* getmean()             -> (computes) returns self.m
* getmin()              -> (computes) returns self.minval
* getmax()              -> (computes) returns self.maxval
* getstddev()           -> (computes) returns self.stddev
* read()        		-> read image from file [or stream, or shared memory]
* write()       		-> write image to file  [or stream, or shared memory]
* readheader()          -> read only the header [much faster for scanning files]

Each individual file format would then inherit all the functionality of this class and just make new read and write methods.

There are also fileseries related methods (next(), previous(), ...) which returns a FabioImage instance of the next/previous frame in a fileserie

Other feature:

* possibility for using on-the-fly external compression - i.e. if files are
  stored as something as .gz, .bz2 etc could decompress them, using an external
  compression mechanism (if available). 



.. |Build Status| image:: https://travis-ci.org/silx-kit/fabio.svg?branch=master
   :target: https://travis-ci.org/silx-kit/fabio
.. |Appveyor Status| image:: https://ci.appveyor.com/api/projects/status/4k6lol1vq30qhf66/branch/master?svg=true
   :target: https://ci.appveyor.com/project/ESRF/fabio/branch/master
