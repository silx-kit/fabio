Installation
============

FabIO can, as any Python module, be installed from its sources,
available on sourceforge but we advice to use binary
packages provided for the most common platforms on sourceforge:
Windows, MacOSX and Linux. Moreover FabIO is part of the common
Linux distributions Ubuntu (since 11.10) and Debian7 where the
package is named python-fabio and can be installed via:

::

    sudo apt-get install python-fabio

If you are using MS Windows or MacOSX; binary version have been packaged and should be PIP-installable.
PIP is the Python Installer Program, similar to ``apt-get`` for Python.
It runs under any architecture and can simply be installed from:

https://bootstrap.pypa.io/get-pip.py

then

::

  pip install fabio

Installation under windows
--------------------------

Install Python from http://python.org.
I would recommend Python 2.7 in 64 bits version if your operating system allows it.
Python3 (>=3.2) is OK while less tested.

If you are looking for an integrated distribution of Python on Windows,
WinPython is a good one, the Python2.7, 64 bit version is advised.
https://winpython.github.io/
It comes with pip pre-installed and configured.

Installation using PIP:
.......................
Download PIP and run:
https://bootstrap.pypa.io/get-pip.py

Then install the wheel package manager and all dependencies for :

::

    python get-pip.py
    pip install setuptools
    pip install wheel
    pip install fabio

Note: for now, PyQt4 is not yet pip-installable. you will need to get it from riverbankcomputing:
http://www.riverbankcomputing.co.uk/software/pyqt/download

Manual installation under windows
.................................

You will find all the scientific Python stack packaged for Windows on Christopher Gohlke' page (including FabIO):

http://www.lfd.uci.edu/~gohlke/pythonlibs/

Pay attention to the Python version (both number and architecture).
DO NOT MIX 32 and 64 bits version.
To determine the version of your Python:

.. highlight:: python

    >>> 8 * tuple.__itemsize__
    
This gives you the architecture width of the Python interpreter


Installation from sources
.........................

Install the required dependencies (via PIP or a repository), then retrieve the Microsoft compiler and install it from:
http://aka.ms/vcpython27

Once done, follow the classical procedure (similar to MacOSX or Linux):
* download sources of FabIO from fable.sourceforge.net.
* unzip the archive
* run ``python setup.py build install``


Installation on MacOSX
----------------------

Python 2.7, 64 bits and numpy are  natively available on MacOSX.

Install PIP
...........

Download PIP and run:
https://bootstrap.pypa.io/get-pip.py

Then install the wheel package manager:

::

    pip install setuptools
    pip install wheel
    pip install PIL
    pip install lxml
    pip install fabio

Note: for now, PyQt4 is not yet pip-installable. you will need to get it from riverbankcomputing:
http://www.riverbankcomputing.co.uk/software/pyqt/download

Get the compiler
................
Apple provides for free Xcode which contains the compiler needed to build binary extensions.
Xcode can be installed from the App-store.


Manual Installation for any operating system
--------------------------------------------

Install the dependencies
........................

* Python 2.6 - 2.7 or 3.2+
* numpy - http://www.numpy.org

For full functionality of FabIO the following modules need to be installed:

* PIL (python imaging library) - http://www.pythonware.com
* lxml (library for reading XSDimages)
* PyQt4 for the fabio_viewer program



FabIO can be downloaded from the fable download page on sourceforge.net.
Presently the source code has been distributed as a zip package and a compressed tarball.
Download either one and unpack it.

::

    http://sourceforge.net/projects/fable/files/fabio/

e.g.

::

    tar xvzf fabio-0.2.2.tar.gz

or

::

    unzip fabio-0.2.2.zip

all files are unpacked into the directory fabio-0.2.2. To install these do

::

     cd fabio-0.2.2

and install fabio: build it, run the tests and build the wheel package and install it.

::

    python setup.py build
    python setup.py bdist_wheel
    sudo pip install dist/fabio-0.2.2*.whl
    
most likely you will need to gain root privileges (with sudo in front of the command) to install the built package.

Development versions
--------------------
The newest development version can be obtained by checking it out from the git repository:

::

    git clone https://github.com/kif/fabio
    cd fabio
    python setup.py build bdist_wheel
    sudo pip install dist/fabio-0.2.2*.whl

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
	./build-deb.sh 3

which builds a couple of debian packages (actually one for python2 and another for python3) and installs them in a single command.
Handy for testing, but very clean, see hereafter

Debian packaging
----------------
FabIO features some helper function to make debian packaging easier:

::

    #to create the orig.tar.gz without cython generated C files for Sphinx built documentation:
    python setup.py debian_src
     
    # to create a tarball of all images needed to test the library 
    python setup.py debian_testimages

Two tarball are created, one with all source code (and only source code) and the other one with all test-data.

Test suite
----------

FabIO has a comprehensive test-suite to ensure non regression.
When you run the test for the first time, many test images will be download and converted into various compressed format like gzip and bzip2 (this takes a lot of time).

Be sure you have an internet connection and your environment variable http_proxy is correctly set-up. For example if you are behind a firewall/proxy:

::

   export http_proxy=http://proxy.site.org:3128

Many tests are there to deal with malformed files, don't worry if the programs complains in warnings about "bad files",
it is done on purpose to ensure robustness in FabIO.


Run test suite from installation directory
..........................................

To run the test:

::

   python setup.py build test


Run test suite from installed version
.....................................

Within Python (or ipython):

.. code-block:: python

   import fabio
   fabio.tests()


Test coverage
.............

FabIO comes with 25 test-suites (113 tests in total) representing a coverage of 60%.
This ensures both non regression over time and ease the distribution under different platforms:
FabIO runs under Linux, MacOSX and Windows (in each case in 32 and 64 bits) with Python versions 2.6, 2.7, 3.2 and 3.4.
Under linux it has been tested on i386, x86_64, arm, ppc, ppc64le.

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
