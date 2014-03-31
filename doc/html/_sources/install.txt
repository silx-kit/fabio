Installation
============

FabIO can, as any Python module, be installed from its sources,
available on sourceforge but we advice to use binary
packages provided for the most common platforms on sourceforge:
Windows, MacOSX and Linux. Moreover FabIO is part of the common
Linux distributions Ubuntu (since 11.10) and Debian7 where the
package is named python-fabio and can be installed via:
::

    # apt-get install python-fabio

If you are using MS Windows or MacOSX; binary version have been packaged.
Windows installers are executable, just download the one corresponding to you python version and run it.
MacOSX builds are zipped: unzip them at the right place.


Dependencies
------------

* Python 2.6 or later (python 3.x is not yet ready)
* numpy - http://www.numpy.org

For full functionality of Fabio the following modules need to be installed:


* PIL (python imaging library) - http://www.pythonware.com
* lxml (library for reading XSDimages)


Installation from sources
-------------------------

FabIO can be downloaded from the fable download page on sourceforge.net.
Presently the source code has been distributed as a zip package and a compressed tarball.
Download either one and unpack it.

::

    http://sourceforge.net/projects/fable/files/fabio/

e.g.
::

    tar xvzf fabio-0.1.4.tar.gz

or

::

    unzip fabio-0.1.4.zip

all files are unpacked into the directory fabio-0.1.4. To install these do

::

     cd fabio-0.1.4

and install fabio with

::

    python setup.py build
    sudo python setup.py install

most likely you will need to gain root privileges (with sudo in front of the command) to install the built package.

Development versions
--------------------
The newest development version can be obtained by checking it out from the subversion (SVN) repository:

::

    svn checkout https://svn.sourceforge.net/svnroot/fable/fabio/trunk fabio
    cd fabio
    python setup.py build
    sudo python setup.py install

For Ubuntu/Debian users, you will need:

* python-imaging
* python-imaging-tk
* python-numpy
* python-dev

::

    sudo apt-get install python-imaging python-imaging-tk python-numpy

We provide also a debian-package builder based on stdeb:

::

	sudo apt-get install python-stdeb
	./build-deb.sh

which builds a debian package and installs it in a single command. Handy for testing.

Test suite
----------

FabIO has a comprehensive test-suite to ensure non regression.
When you run the test for the first time, many test images will be download and converted into various compressed format like gzip and bzip2 (this takes a lot of time).

Be sure you have an internet connection and your environment variable http_proxy is correctly set-up. For example if you are behind a firewall/proxy:

:: 

   export http_proxy=http://proxy.site.org:3128


To run the test:

::

   python setup.py test   

Many tests are there to deal with malformed files, don't worry if the programs complains in warnings about "bad files", it is done on purpose to ensure robustness in FabIO. 
  
FabIO comes with 25 test-suites (110 tests in total) representing a coverage of 60%.
This ensures both non regression over time and ease the distribution under different platforms:
FabIO runs under Linux, MacOSX and Windows (in each case in 32 and 64 bits) with python versions 2.6 and 2.7.

.. csv-table:: Test suite coverage
   :header: "Name", "Stmts", "Exec", "Cover"
   :widths: 35, 8, 8, 8
   
   "fabio/GEimage                 ", "   94", "     48", "    51%"
   "fabio/HiPiCimage              ", "   55", "      7", "    12%"
   "fabio/OXDimage                ", "  285", "    271", "    95%"
   "fabio/TiffIO                  ", "  794", "    534", "    67%"
   "fabio/__init__                ", "   15", "     15", "   100%"
   "fabio/adscimage               ", "   79", "     37", "    46%"
   "fabio/binaryimage             ", "   50", "     15", "    30%"
   "fabio/bruker100image          ", "   60", "     13", "    21%"
   "fabio/brukerimage             ", "  212", "    171", "    80%"
   "fabio/cbfimage                ", "  441", "    219", "    49%"
   "fabio/compression             ", "  223", "    136", "    60%"
   "fabio/converters              ", "   17", "     14", "    82%"
   "fabio/dm3image                ", "  133", "     16", "    12%"
   "fabio/edfimage                ", "  596", "    397", "    66%"
   "fabio/fabioimage              ", "  306", "    193", "    63%"
   "fabio/fabioutils              ", "  322", "    256", "    79%"
   "fabio/file_series             ", "  140", "     61", "    43%"
   "fabio/fit2dmaskimage          ", "   75", "     71", "    94%"
   "fabio/fit2dspreadsheetimage   ", "   47", "      7", "    14%"
   "fabio/hdf5image               ", "  146", "     25", "    17%"
   "fabio/kcdimage                ", "   80", "     65", "    81%"
   "fabio/mar345image             ", "  244", "    215", "    88%"
   "fabio/marccdimage             ", "   63", "     56", "    88%"
   "fabio/mrcimage                ", "   96", "      0", "     0%"
   "fabio/openimage               ", "  104", "     69", "    66%"
   "fabio/pilatusimage            ", "   34", "      5", "    14%"
   "fabio/pixiimage               ", "   95", "     22", "    23%"
   "fabio/pnmimage                ", "  109", "     21", "    19%"
   "fabio/raxisimage              ", "   98", "     88", "    89%"
   "fabio/readbytestream          ", "   26", "      5", "    19%"
   "fabio/tifimage                ", "  167", "     60", "    35%"
   "fabio/xsdimage                ", "   94", "     68", "    72%"
