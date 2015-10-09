Changelog
=========

From FabIO-0.2.1 to FabIO-0.2.2:
................................
- work on the auto-documentation on ReadTheDocs (see http://fabio.readthedocs.org)
- fix regression when reading BytesIO
- Python3 compatibility
- prepare multiple package for debian

From FabIO-0.2.0 to FabIO-0.2.1:
................................
- Fix issues with variable endianness (tested PPC, PPC64le, i386, x86-64, ARM processors)
- Optimization of byte-offset reader (about 20% faster on some processors)

From FabIO-0.1.4 to FabIO-0.2.0:
................................
- Compatibility with Python3 (tested on Python 2.6, 2.7, 3.2 and 3.4)
- Support for Mar555 flat panel
- Optimization of CBF reader (about 2x faster)
- include tests into installed module (and download in /tmp)

From FabIO-0.1.3 to FabIO-0.1.4:
................................
- Work on compatibility with Python3
- Specific debian support with test images included but no auto-generated files
- Image viewer (fabio_viewer) based on Qt4 (Thanks for Gaël Goret)
- Reading images from HDF5 datasets
- Read support for "MRC" images
- Read support for "Pixi detector (Thanks for Jon Wright)
- Read support for "Raxis" images from Rigaku (Thanks to Brian Pauw)
- Write support for fit2d mask images
- Drop support for python 2.5 + Cythonization of other algorithms

From FabIO-0.1.2 to FabIO-0.1.3:
................................
- Fixed a memory-leak in mar345 module
- Improved support for bruker format (writer & reader)
- Fixed a bug in EDF headers (very long headers)
- Provide template for new file-formats
- Fix a bug related to PIL in new MacOSX
- Allow binary-images to be read from end

From FabIO-0.1.1 to FabIO-0.1.2:
................................
- Fixed a bug in fabioimage.write (impacted all writers)
- added Sphinx documentation "python setup.py build_doc"
- PyLint compliance of some classes (rename, ...)
- tests from installer with "python setup.py build test"

From FabIO-0.1.0 to FabIO-0.1.1:
................................
- Merged Mar345 image reader and writer with cython bindings (towards python3 compliance)
- Improve CBF image writing under windows
- Bz2, Gzip and Flat files are managed through a common way ... classes are more (python v2.5) or less (python v2.7) overloaded
- Fast EDF reading if one assumes offsets are the same between files, same for ROIs

From FabIO-0.0.8 to FabIO-0.1.0:
................................
- OXD reader improved and writer implemented
- Mar345 reader improved and writer implemented
- CBF writer implemented
- Clean-up of the code & bug fixes
- Move towards python3
- Make PIL optional dependency

Python3 is not yet tested but some blocking points have been identified and some fixed.

From FabIO-0.0.7 to FabIO-0.0.8:
................................
- Support for Tiff using TiffIO module from V.A.Solé
- Clean-up of the code & bug fixes

From FabIO-0.0.6 to FabIO-0.0.7:
................................
- Support for multi-frames EDF files
- Support for XML images/2D arrays used in EDNA
- new method: fabio.open(filename) that is an alias for fabio.openimage.openimage(filename)

From FabIO-0.0.4 to FabIO-0.0.6:
................................
- Support for CBF files from Pilatus detectors
- Support for KCD files from Nonius Kappa CCD images
- write EDF with their native data type (instead of uint16 by default)
