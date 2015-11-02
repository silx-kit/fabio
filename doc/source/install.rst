:Author: Jérôme Kieffer
:Date: 31/10/2015
:Keywords: Installation procedure
:Target: System administrators

Installation
============

FabIO can, as any Python module, be installed from its sources,
available on the `Python cheese shop <https://pypi.python.org/pypi/fabio/0.2.2>`_
but we advice to use binary wheels packages provided for the most common platforms:
Windows, MacOSX. For Debian Linux and its derivatives (Ubuntu, Mint, ...), FabIO
is part of the distributions and itss package is named *python-fabio* and can be installed via:

.. code::

    sudo apt-get install python-fabio

If you are using MS Windows or MacOSX; binary version (as wheel packages) are
PIP-installable.
PIP is the Python Installer Program, similar to ``apt-get`` for Python.
It runs under any architecture.
Since Python 2.7.10 and 3.4, PIP is installed together with Python itself.
If your Python is elder, PIP can be simply `downloaded <https://bootstrap.pypa.io/get-pip.py>`_
and executed using your standard Python:

.. code::
   python get-pip.py
   pip install fabio

Installation under windows
--------------------------

Install `Python <http://python.org>`_ from the official web page.
I would recommend Python 2.7 in 64 bits version if your operating system allows it.
Python3 (>=3.2) is OK.

If you are looking for an integrated scientific Python distribution on Windows,
`WinPython <https://winpython.github.io/>`_ is a good one, the Python2.7, 64 bit
 version is advised.

It comes with pip pre-installed and configured.

Installation using PIP:
.......................

If you use a Python2 elder than 2.7.10 or a Python3 <3.4, you will need
`Download PIP <https://bootstrap.pypa.io/get-pip.py>`_.
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

You will find all the `scientific Python stack packaged for Windows<http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_ on Christoph
Gohlke' page (including FabIO):

Pay attention to the Python version (both number and architecture).
**DO NOT MIX 32 and 64 bits version**.
To determine the version of your Python:

.. highlight:: python

    >>> 8 * tuple.__itemsize__

This gives you the architecture width of the Python interpreter


Installation from sources
.........................

Get the compiler
^^^^^^^^^^^^^^^^
Install the required dependencies, then retrieve the
`Microsoft compiler <http://aka.ms/vcpython27>`_ and install it.

**Nota**: the version of the compiler and the version of the Microsoft SDK
have to match the Python version you are using.
This link is for Python2.7.
Other version of Python require differents compiler and runtime.

Compile the sources
^^^^^^^^^^^^^^^^^^^

Once done, follow the classical procedure (similar to MacOSX or Linux):
* download sources of `the latest release <https://github.com/kif/fabio/releases/latest>`_
or `the development version <https://github.com/kif/fabio/archive/master.zip>`_.
* unzip the archive
* open a cmd.exe console in the unzipped archive directory
* run::
   pip install setuptools wheel
   pip install -r requirements.txt
   python setup.py build
   python setup.py test
   pip install .


Testing version of FabIO
........................

Continuous integration runs the complete test suite on multiple operating
systems and python version.
Under Windows, this is done using the
`AppVeyor cloud service <https://ci.appveyor.com/project/kif/fabio>`_
Select the environment which matches your setup like
**Environment: PYTHON=C:\Python34-x64, PYTHON_VERSION=3.4.3, PYTHON_ARCH=64**
and go to **artifacts** where wheels and MSI-installers are available.


Installation on MacOSX
----------------------

Python 2.7, 64 bits and numpy are natively available on MacOSX.

Install via PIP
...............

Since MacOSX 10.11 (El-Captain), PIP is available as part of the standard python installation.
For elder MacOSX, `download PIP and run <https://bootstrap.pypa.io/get-pip.py>`_.
Then install FabIO directly:

.. code::
    sudo pip install fabio


**Note:** for now, PyQt4, used by the *fabio-viewer* is not yet pip-installable.
You will need to get it from
`riverbankcomputing <http://www.riverbankcomputing.co.uk/software/pyqt/download>`_.

Compile from sources
....................

Get the compiler
^^^^^^^^^^^^^^^^
Apple provides for free Xcode which contains the compiler needed to build binary extensions.
Xcode can be installed from the App-store.

Compile the sources
^^^^^^^^^^^^^^^^^^^

Once done, follow the classical procedure (similar to Windows or Linux):
* download sources of `the latest release <https://github.com/kif/fabio/releases/latest>`_
or `the development version <https://github.com/kif/fabio/archive/master.zip>`_.
* unzip the archive
* open a terminal in the unzipped archive directory
* run::
   sudo pip install setuptools wheel
   sudo pip install -r requirements.txt
   python setup.py build
   python setup.py test
   sudo pip install .


Manual Installation for any operating system
--------------------------------------------

Install the dependencies
........................

Most Linux distribution come with a Python environment configured. Complete
it with the needed dependencies.

* Python 2.6 - 2.7 or 3.2+
* numpy - http://www.numpy.org

For full functionality of FabIO the following modules need to be installed:

* PIL (python imaging library) - http://www.pythonware.com
* lxml (library for reading XSDimages)
* PyQt4 for the fabio_viewer program

Once done, follow the classical procedure (similar to Windows or MacOSX):
* download sources of `the latest release <https://github.com/kif/fabio/releases/latest>`_
or `the development version <https://github.com/kif/fabio/archive/master.zip>`_.
* unzip the archive
* open a terminal in the unzipped archive directory
* run::
   sudo pip install setuptools wheel
   sudo pip install -r requirements.txt
   python setup.py build
   python setup.py test
   sudo pip install .


Most likely you will need to gain root privileges (with sudo in front of the
command) to install packages.

Development versions
--------------------
The newest development version can be obtained by checking it out from the git repository:

::

    git clone https://github.com/kif/fabio
    cd fabio
    python setup.py build test
    sudo pip install .

For Ubuntu/Debian users, you will need:

* python-imaging
* python-imaging-tk
* python-numpy
* python-dev

::

    sudo apt-get install python-imaging python-imaging-tk python-numpy

Automatic debian packaging
..........................

Debian 6 and 7:
^^^^^^^^^^^^^^^
We provide a debian-package builder based on stdeb, building a package for Python2:

::

	sudo apt-get install python-stdeb
	./build-deb.sh

which builds a debian package and installs them in a single command.
Handy for testing, but very clean, see hereafter

Debian 8 and newer
------------------
FabIO features some helper function to make debian packaging easier:

::

    #to create the orig.tar.gz without cython generated C files for Sphinx built documentation:
    python setup.py debian_src

    # to create a tarball of all images needed to test the library
    python setup.py debian_testimages

Two tarball are created, one with all source code (and only source code) and the other one with all test-data.

There is also a script which builds a bunch of *real* debian packages:

* *fabio-viewer*: the GUI for visualizing diffraction images
* *fabio-doc*: the documumentation package
* *python3-fabio*: library built for Python3
* *python3-fabio-dbg*: debug symbols for Python3
* *python-fabio*: library built for Python2
* *python-fabio-dbg*: debug symbols for Python2

For this, you need a complete debian build environment:

::

   sudo apt-get install cython cython-dbg cython3 cython3-dbg debhelper dh-python \
   python-all-dev python-all-dbg python-h5py \
   python-lxml python-lxml-dbg python-matplotlib python-matplotlib-dbg python-numpy\
   python-numpy-dbg python-qt4 python-qt4-dbg python-sphinx \
   python-sphinxcontrib.programoutput python-tk python-tk-dbg python3-all-dev python3-all-dbg \
   python3-lxml python3-lxml-dbg python3-matplotlib \
   python3-matplotlib-dbg python3-numpy python3-numpy-dbg python3-pyqt4 python3-pyqt4-dbg \
    python3-sphinx python3-sphinxcontrib.programoutput \
   python3-tk python3-tk-dbg

   ./build-debian-full.sh


Test suite
----------

FabIO has a comprehensive test-suite to ensure non regression.
When you run the test for the first time, many test images will be download and converted into various compressed format like gzip and bzip2 (this takes a lot of time).

Be sure you have an internet connection and your proxy setting are correctly defined in the environment variable *http_proxy*.
For example if you are behind a firewall/proxy:

Under Linux and MacOSX::

   export http_proxy=http://proxy.site.org:3128

Under Windows::

   set http_proxy=http://proxy.site.org:3128

Where *proxy.site.org* and *3128* correspond to the proxy server and port on your network.
At ESRF, you can get this piece of information by phoning to the hotline: 24-24.

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

FabIO comes with 27 test-suites (120 tests in total) representing a coverage of 60%.
This ensures both non regression over time and ease the distribution under different platforms:
FabIO runs under Linux, MacOSX and Windows (in each case in 32 and 64 bits) with Python versions 2.6, 2.7, 3.2, 3.3, 3.4 and 3.5.
Under linux it has been tested on i386, x86_64, arm, ppc, ppc64le.

.. toctree::
   :maxdepth: 2
    
   coverage

