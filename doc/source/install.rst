:Author: Jérôme Kieffer
:Date: 15/07/2016
:Keywords: Installation procedure
:Target: System administrators

Installation
============

FabIO can, as any Python module, be installed from its sources,
available on the `Python cheese shop <https://pypi.python.org/pypi/fabio>`_
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
Python3 (>=3.4) is OK.

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

You will find all the `scientific Python stack packaged for Windows <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_ on Christoph
Gohlke' page (including FabIO):

Pay attention to the Python version (both number and architecture).
**DO NOT MIX 32 and 64 bits version**.
To determine the version and architecture width of the Python interpreter:

.. highlight:: python
    
    >>> import sys
    >>> print(sys.version)
    2.7.9 (default, Mar  1 2015, 12:57:24) 
    >>> print("%s bits"%(8 * tuple.__itemsize__))
    64 bits

Installation from sources
.........................

* Retrieve the sources from github:

  + `The master development branch <https://github.com/silx-kit/fabio/archive/master.zip>`_
  + `The latest release <https://github.com/silx-kit/fabio/releases/latest>`_

* unzip the file in a directory
* open a console (cmd.exe) in this directory.
* install the required dependencies using PIP::

    pip install -r ci/requirements_appveyor.txt --trusted-host www.silx.org

Get the compiler and install it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The version of the compiler and the version of the Microsoft SDK
have to match the Python version you are using. Here are a couple of examples:

* Python2.7: `Microsoft compiler 2008 <http://aka.ms/vcpython27>`_
* Python 3.5: `Microsoft Visual studio community edition 2015 <https://go.microsoft.com/fwlink/?LinkId=691978&clcid=0x40c>`_

Compile the sources
^^^^^^^^^^^^^^^^^^^

::

   python setup.py build
   python setup.py test
   pip install .

Testing version of FabIO
........................

Continuous integration runs the complete test suite on multiple operating
systems and python version.
Under Windows, this is done using the
`AppVeyor cloud service <https://ci.appveyor.com/project/ESRF/fabio>`_
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

* Retrieve the sources from github:

  + `The master development branch <https://github.com/silx-kit/fabio/archive/master.zip>`_
  + `The latest release <https://github.com/silx-kit/fabio/releases/latest>`_

* unzip the file in a directory
* open a terminal in the unzipped archive directory
* run::

   sudo pip install -r ci/requirements_travis.txt --trusted-host www.silx.org
   python setup.py build
   python setup.py test
   sudo pip install .


Manual Installation for any operating system
--------------------------------------------

Install the dependencies
........................

Most Linux distribution come with a Python environment configured. Complete
it with the needed dependencies.

* Python 2.7 or 3.4+
* numpy - http://www.numpy.org

For full functionality of FabIO the following modules need to be installed:

* Pillow (python imaging library) - http://www.pythonware.com
* lxml (library for reading XSDimages)
* PyQt4 for the fabio_viewer program

Once done, follow the classical procedure (similar to Windows or MacOSX):

* Retrieve the sources from github:

  + `The master development branch <https://github.com/silx-kit/fabio/archive/master.zip>`_
  + `The latest release <https://github.com/silx-kit/fabio/releases/latest>`_

* unzip the file in a directory
* open a terminal in the unzipped archive directory
* run::

   sudo pip install -r ci/requirements_travis.txt --trusted-host www.silx.org
   python setup.py build
   python setup.py test
   sudo pip install .


Most likely you will need to gain root privileges (with sudo in front of the
command) to install packages.

Development versions
--------------------
The newest development version can be obtained by checking it out from the git repository:

::

    git clone https://github.com/silx-kit/fabio
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
	./build-deb7.sh

which builds a debian package and installs them in a single command.
Handy for testing, but very clean, see hereafter

Debian 8 and newer
------------------

There is also a script which builds a bunch of *real* debian packages: *build-deb8.sh*
It will build a bunch of 6 debian packages::
 
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

   >>> import fabio
   >>> fabio.tests()


Test coverage
.............

FabIO comes with 33 test-suites (145 tests in total) representing a coverage of 60%.
This ensures both non regression over time and ease the distribution under different platforms:
FabIO runs under Linux, MacOSX and Windows (in each case in 32 and 64 bits) with Python versions 2.7, 3.4 and 3.5.
Under linux it has been tested on i386, x86_64, arm, ppc, ppc64le.
FabIO may run on other untested systems but without warranty.

.. toctree::
   :maxdepth: 2
    
   coverage

