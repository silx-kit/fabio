Changelog
=========

FabIO-0.4.0 (07/2016):
......................

- Write support for Bruker100 (contribution from Sigmund Neher)
- Read support for Princeton instrumentation cameras (contribution from Clemens Percher)
- Read support for FIT2D binary format
- Read support for Eiger detector (Dectris) and generic HDF5 (partial)
- Switch ESRF-contributed file formats to MIT license (more liberal)
- Drop support for python 2.6, 3.2 and 3.3. Supports only 2.7 and 3.4+
- Include TiffIO into core of FabIO (no more third-party)
- Refactor mar345 (contributed by Henri Payno)
- Enhanced byte-offset compression using Cython
- Move master repository to silx-kit (https://github.com/silx-kit)

FabIO-0.3.0 (12/2015):
......................

- Migrate to PEP8 for class names.
- Use a factory & registry instead of fiddling in sys.modules for instance creation
- dim1, dim2, bpp and bytecode are properties. Use their private version while reading.
- FabioImage.header["filename"] has disappeared. Use FabioImage.filename instead.
- Automatic backported package down to debian-8
- Compatibility checked with 2.6, 2.7, 3.2, 3.3, 3.4 and 3.5
- Continuous integration based on appveyor (windows) and travis (linux)
- Support for numpy 2d-array and PNM saving
- Move away from Sourceforge -> Github.

FabIO-0.2.2 (07/2015):
......................

- work on the auto-documentation on ReadTheDocs (see http://fabio.readthedocs.org)
- fix regression when reading BytesIO
- Python3 compatibility
- prepare multiple package for debian

FabIO-0.2.1 (02/2015):
......................

- Fix issues with variable endianness (tested PPC, PPC64le, i386, x86-64, ARM processors)
- Optimization of byte-offset reader (about 20% faster on some processors)

FabIO-0.2.0 (01/2015):
......................

- Compatibility with Python3 (tested on Python 2.6, 2.7, 3.2 and 3.4)
- Support for Mar555 flat panel
- Optimization of CBF reader (about 2x faster)
- include tests into installed module (and download in /tmp)

FabIO-0.1.4:
............
- Work on compatibility with Python3
- Specific debian support with test images included but no auto-generated files
- Image viewer (fabio_viewer) based on Qt4 (Thanks for Gaël Goret)
- Reading images from HDF5 datasets
- Read support for "MRC" images
- Read support for "Pixi detector (Thanks for Jon Wright)
- Read support for "Raxis" images from Rigaku (Thanks to Brian Pauw)
- Write support for fit2d mask images
- Drop support for python 2.5 + Cythonization of other algorithms

FabIO-0.1.3:
............
- Fixed a memory-leak in mar345 module
- Improved support for bruker format (writer & reader)
- Fixed a bug in EDF headers (very long headers)
- Provide template for new file-formats
- Fix a bug related to PIL in new MacOSX
- Allow binary-images to be read from end

FabIO-0.1.2 (04/2013):
......................

- Fixed a bug in fabioimage.write (impacted all writers)
- added Sphinx documentation "python setup.py build_doc"
- PyLint compliance of some classes (rename, ...)
- tests from installer with "python setup.py build test"

FabIO-0.1.1:
............

- Merged Mar345 image reader and writer with cython bindings (towards python3 compliance)
- Improve CBF image writing under windows
- Bz2, Gzip and Flat files are managed through a common way ... classes are more (python v2.5) or less (python v2.7) overloaded
- Fast EDF reading if one assumes offsets are the same between files, same for ROIs

FabIO-0.1.0:
............

- OXD reader improved and writer implemented
- Mar345 reader improved and writer implemented
- CBF writer implemented
- Clean-up of the code & bug fixes
- Move towards python3
- Make PIL optional dependency
- Preliminary Python3 support (partial).

FabIO-0.0.8:
............

- Support for Tiff using TiffIO module from V.A.Solé
- Clean-up of the code & bug fixes

FabIO-0.0.7 (03/2011):
......................

- Support for multi-frames EDF files
- Support for XML images/2D arrays used in EDNA
- new method: fabio.open(filename) that is an alias for fabio.openimage.openimage(filename)

FabIO-0.0.6 (01/2011):
......................

- Support for CBF files from Pilatus detectors
- Support for KCD files from Nonius Kappa CCD images
- write EDF with their native data type (instead of uint16 by default)

FabIO-0.0.4 (2009):
...................

- Support for EDF and many other formats