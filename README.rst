FabIO: Fable Input/Output library
=================================

Main websites:

 * http://fable.sf.net
 * https://github.com/silx-kit/fabio


|Build Status| |Appveyor Status|

----

FabIO is an I/O library for images produced by 2D X-ray detectors and written in Python.
FabIO support images detectors from a dozen of companies (including Mar, Dectris, ADSC, Hamamatsu, Oxford, ...),
for a total of 20 different file formats (like CBF, EDF, TIFF, ...) and offers an unified interface to their
headers (as a python dictionary) and datasets (as a numpy ndarray of integers or floats)

Getting FabIO
-------------

FabIO is available from `PyPI <https://pypi.python.org/pypi/fabio>`_.

`Debian/Ubuntu packages <http://www.silx.org/pub/debian/binary/>`_, and
`wheels <http://www.silx.org/pub/wheelhouse/>`_ are available
for windows, linux and MacOSX from the silx repository:

Documentation is available at `PythonHosted <http://pythonhosted.org/fabio/>`_,
Continuous documentation at `ReadTheDocs <http://fabio.readthedocs.io>`_ and
Nightly build documentation at `silx <http://www.silx.org/doc/fabio/>`_.

Citation:
---------
The general philosophy of the library is described in:
`FabIO: easy access to two-dimensional X-ray detector images in Python; E. B. Knudsen, H. O. Sørensen, J. P. Wright, G. Goret and J. Kieffer Journal of Applied Crystallography, Volume 46, Part 2, pages 537-539. <http://dx.doi.org/10.1107/S0021889813000150>`_

Transparent handling of compressed files
----------------------------------------
Fabio is expected to handle gzip and bzip2 compressed files transparently.
Following a query about the performance of reading compressed data, some
benchmarking details have been collected at fabio_compressed_speed.
This means that when your python was configured and built you needed the
bzip and gzip modules to be present (eg libbz2-dev package for ubuntu)
Using fabio in your own python programs
Example::

  >>> import fabio
  >>> obj = fabio.edfimage("mydata0000.edf")
  >>> obj.data.shape
  (2048, 2048)
  >>> obj.header["Omega"]
  23.5


Design Specifications
---------------------
Name: Fabio = Fable Input/Output

Idea:
.....
Have a base class for all our 2D diffraction greyscale images.
This consists of a 2D array (numpy ndarray)
and a python dictionary (actually an ordered dict) of header information in (string key, string value) pairs.

Class FabioImage
................
Needs a name which will not to be confused with an RGB color image.

Class attributes:

* data   					-> 2D array
* header 					-> ordered dictionary
* rows, columns, dim1, dim2 -> data.shape (properties determined on the fly)
* header_keys               -> property for list(header.keys()), formerly used to retain the order of the header
* bytecode                 	-> data.typecode() (property)
* m, minval, maxval, stddev	-> image statistics, could add others, eg roi[slice]

Class methods (functions):
..........................

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

* possibility for using on-the-fly external compression - i.e. if files are stored as something as .gz, .bz2 etc could decompress them, using an external compression mechanism (if available). This is present in fabian but requires that images are edfs.


Known file formats
------------------

* Bruker:

  + BrukerImage
  + Bruker100Image
  + KcdImage: Nonius KappaCCD diffractometer

* Mar Research:

  + MarccdImage (fileformat derived from Tiff)
  + Mar345Image imaging plate with PCK compression

* Dectris:

  + CbfImage (implements a fast byte offset de/compression scheme in python/cython)
  + PilatusImage (fileformat derived from Tiff)
  * EigerImage (derived from HDF5/NeXus format)

* ESRF:

  + EdfImage: The ESRF data Format
  + XsdImage: XML serialized image from EDNA
  + Fit2dImage: Fit2d binary format
  + Fit2dmaskImage: Fit2d Mask format
  + Fit2dSpreadsheetImage: Fit2d ascii tables (spread-sheet)

* ADSC:

  + AdscImage

* GE detector at APS

  + GEimage

* PNM

  + PnmImage

* Tiff

  + TifImage
  + TiffIO from PyMca

* D3M

  + D3mImage

* Hamamatsu

  + HiPiCImage

* Oxford Diffraction Sapphire 3

  + OXDimage uncompressed
  + OXDimage with TY1 byte offset compression
  + OXDimage with TY5 byte offset compression (experimental)

* Nonius -> now owned by Bruker

* HDF5: generic format for stack of images
  + Hdf5Image
  + EigerImage

* Raw Binary without compression

Installation
------------

Please see doc/source/INSTALL.rst

Changelog
---------

Please see doc/source/Changelog.rst

.. |Build Status| image:: https://travis-ci.org/kif/fabio.svg?branch=master
   :target: https://travis-ci.org/kif/fabio
.. |Appveyor Status| image:: https://ci.appveyor.com/api/projects/status/4k6lol1vq30qhf66/branch/master?svg=true
   :target: https://ci.appveyor.com/project/ESRF/fabio/branch/master
