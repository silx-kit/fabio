:Author: Jérôme Kieffer
:Date: 03/04/2020
:Keywords: Installation procedure
:Target: System administrators

Installation
============

FabIO can, as any Python module, be installed from its sources,
available on the `Python cheese shop <https://pypi.python.org/pypi/fabio>`_
but we advice to use binary wheels packages provided for the most common platforms:
Windows, MacOSX. For Debian Linux and its derivatives (Ubuntu, Mint, ...), FabIO
is part of the distributions and itss package is named *python-fabio* and can be installed via:

.. code-block:: shell

    sudo apt-get install fabio-bin

If you are using MS Windows or MacOSX; binary version (as wheel packages) are
PIP-installable.
PIP is the Python Installer Program, similar to ``apt-get`` for Python.
It runs under any architecture. It should best be used in a virtual environament:

.. code-block:: shell

	python3 -m venv py3
	py3\bin\activate.bat
	pip install setuptools wheel pip --upgrade
    pip install fabio

Installation under windows
--------------------------

Python is not installed by default under Windows operating system. 
We suggest you install `Python3 <http://python.org>`_ from the official web page.
Python 3.7 is recommended, in 64 bits version if your operating system allows it; 
but any Python3 (>=3.5) are OK. The support for Python2 has ended in 2020 and FabIO 
is no more tested there.

If you are looking for an integrated scientific Python distribution on Windows,
`WinPython <https://winpython.github.io/>`_ is a good one, Anaconda is also very popular.
Please use Python3 as the support of Python2 has ended.

Then install using PIP as previously

Manual installation under windows
.................................

You will find all the `scientific Python stack packaged for Windows <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_ on Christoph
Gohlke' page (including FabIO):

Pay attention to the Python version (both number and architecture).
**DO NOT MIX 32 and 64 bits version**.
To determine the version and architecture width of the Python interpreter:

.. code-block:: python
    
    >>> import sys
    >>> print(sys.version)
    3.7.1 (default, Mar  1 2019, 12:57:24) 
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

.. code-block:: shell

    pip install -r ci/requirements_appveyor.txt --trusted-host www.silx.org

Get the compiler and install it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The version of the compiler and the version of the Microsoft SDK
have to match the Python version you are using.
Please refer to the 
`Microsoft Visual studio compatibility with Python <https://wiki.python.org/moin/WindowsCompilers>`_ list. 

Compile the sources
^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

   pip install setuptools wheel
   pip install -r ci\requirements_appveyor.txt
   python setup.py build
   python setup.py test.py
   python bdist_wheel
   pip install dist\fabio*.whl

Testing version of FabIO
........................

Continuous integration runs the complete test suite on multiple operating
systems and python version.
Under Windows, this is done using the
`AppVeyor cloud service <https://ci.appveyor.com/project/ESRF/fabio>`_
Select the environment which matches your setup like
**Environment: PYTHON=C:\Python37-x64, PYTHON_VERSION=3.7.1, PYTHON_ARCH=64**
and go to **artifacts** where wheels and MSI-installers are available.


Installation on MacOSX
----------------------

Python 2.7, 64 bits and numpy are natively available on MacOSX but Python2 has reached its end on like.
You have to install `Python3 <http://python.org>`_ from the official web page.

Install via PIP
...............

It is recommended to install Fabio into a virtual environment we will call `py3` and then install
FabIO directly in it:

.. code-block:: shell

	python3 -m venv ~/py3
	source ~/py3/bin/activate
	pip install setuptools wheel pip --upgrade
    pip install fabio
    

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
* run:

.. code-block:: shell

   pip install -r ci/requirements_travis.txt --trusted-host www.silx.org
   python setup.py build
   python setup.py test
   python setup.py bdist_wheel 
   pip install dist/fabio*.whel


Manual Installation for any operating system
--------------------------------------------

Install the dependencies
........................

Most Linux distribution come with a Python environment configured. Complete
it with the needed dependencies. Please ensure you use Python3.x x>=5 and
that numpy is installed on your computer.

For full functionality of FabIO the following modules need to be installed:

* Pillow (python imaging library) - http://www.pythonware.com
* lxml (library for reading XSDimages)
* PyQt for the fabio_viewer program

Once done, follow the classical procedure (similar to Windows or MacOSX):

* Retrieve the sources from github:

  + `The master development branch <https://github.com/silx-kit/fabio/archive/master.zip>`_
  + `The latest release <https://github.com/silx-kit/fabio/releases/latest>`_

* unzip the file in a directory
* open a terminal in the unzipped archive directory
* run:

.. code-block:: shell

	# Create a virtual env:
	python3 -m venv ~/py3
	source ~/py3/bin/activate
	pip install setuptools wheel pip --upgrade
	# Install the dependencies 	
	pip install -r ci/requirements_travis.txt --trusted-host www.silx.org
    python setup.py build
    python setup.py test
    python setup.py bdist_wheel
    # Install the freshly build package
   	pip install dist/fabio*.whl


Development versions
--------------------
The newest development version can be obtained by checking it out from the git repository:

.. code-block:: shell

    git clone https://github.com/silx-kit/fabio
    cd fabio
	pip install -r ci/requirements_travis.txt --trusted-host www.silx.org
    python setup.py build
    python setup.py test
    python setup.py bdist_wheel
    # Install the freshly build package
   	pip install dist/fabio*.whl


Automatic debian packaging
..........................

Debian 8 and newer
^^^^^^^^^^^^^^^^^^

The same script, *build-deb.sh*, will create *real* debian packages:
It will build a bunch of 6 debian packages:

* *fabio-bin*: the GUI for visualizing diffraction images
* *fabio-doc*: the documumentation package
* *python3-fabio*: library built for Python3
* *python3-fabio-dbg*: debug symbols for Python3

For this, you need a complete debian build environment:

::

   sudo apt-get build-dep python3-fabio
   ./build-deb.sh

This script works the same way with Debian-9 stretch and newer.

Test suite
----------

FabIO has a comprehensive test-suite to ensure non regression.
When you run the test for the first time, many test images will be download and converted into various compressed format like gzip and bzip2 
(this takes a lot of time).

Be sure you have an internet connection and your proxy setting are correctly defined in the environment variable *http_proxy*.
For example if you are behind a firewall/proxy (No more needed at ESRF):

Under Linux and MacOSX::

   export http_proxy=http://proxy.site.org:3128

Under Windows::

   set http_proxy=http://proxy.site.org:3128

Where *proxy.site.org* and *3128* correspond to the proxy server and port on your network.

Many tests are there to deal with malformed files, don't worry if the programs complains in warnings about "bad files",
it is done on purpose to ensure robustness in FabIO.


Run test suite from installation directory
..........................................

To run the test:

.. code-block:: shell

   python setup.py build test


Run test suite from installed version
.....................................

Within Python (or ipython):

.. code-block:: python

   >>> import fabio
   >>> fabio.tests()


Test coverage
.............

FabIO comes with 49 test-suites (315 tests in total) representing a coverage of 73%.
This ensures both non regression over time and ease the distribution under different platforms:
FabIO runs under Linux, MacOSX and Windows (in each case in 32 and 64 bits) with Python versions 3.5, 3.6, 3.7 and 3.8.
Under linux it has been tested on i386, x86_64, arm, arm64, ppc, ppc64le.
FabIO may run on other untested systems but without warranty.

.. toctree::
   :maxdepth: 2
    
   coverage

