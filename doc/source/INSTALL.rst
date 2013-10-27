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

* Python 2.5 or later (python 3.x is not yet ready)
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

    tar xvzf fabio-0.1.3.tar.gz

or

::

    unzip fabio-0.1.3.zip

all files are unpacked into the directory fabio-0.1.3. To install these do

::

     cd fabio-0.1.3

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

FabIO has a comprehensive test-suite to ensure non regression (about 100 tests).
When you run the test for the first time, many test images will be download and converted into various compressed format like gzip and bzip2 (this takes a lot of time).
Be sure you have an internet connection (and your environment variable http_proxy is correctly set-up, if you are behind a proxy).

::

    python setup.py build
    cd test
    python test_all.py
    ........................................WARNING:compression:Encounter the python-gzip bug with trailing garbage, trying subprocess gzip
    ..............................WARNING:edfimage:Non complete datablock: got 6928, expected 8388608
    WARNING:edfimage:Non complete datablock: got 6928, expected 8388608
    WARNING:edfimage:Non complete datablock: got 6928, expected 8388608
    .....................WARNING:edfimage:Unknown compression scheme TY1
    .....WARNING:edfimage:Unknown compression scheme FALSE
    ...WARNING: Non standard TIFF. Rows per strip TAG missing
    WARNING: Non standard TIFF. Strip byte counts TAG missing
    ....
    ----------------------------------------------------------------------
    Ran 103 tests in 21.696s
    OK

Many tests are there to deal with malformed files, don't worry if the programs comaplins in warnings about "bad files", it is done on purpose.
