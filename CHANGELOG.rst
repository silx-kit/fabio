Change Log
==========

0.10.0:
-------

- `edfimage`:

  - Improved robustness (PR #315)
  - Read without all restrictions of the "Klora" convention (PR #318)
  - Fixed example (PR #322)
  - Improved performances: Do not create a temporary string (PR #323)
  - Recognize a Global Header Section and using it as default (PR #328)
  - Fixed cleaning header block reading (PR #332)
  - Reading binary data from files and tests (PR #333)
  - Make magic readable (PR #339)

- `mar345image`: Provide all the default file extension for mar345 (PR #354)
- `numpyimage`: Fixes (PR #314, #344)
- `pixiimage`: Improved file series filename parsing (PR #317)
- `tifimage`: Improved TIFF via Pillow (PR #321)
- Added support of esperanto format (PR #347, #351)
- Fixed minor issues (PR #338) and compatibility with `h5py` (PR #350)
- Improved tests (PR #320, #341, #345) and `requirement.txt` (PR #331)
- Updated debian packaging (PR #324, #326), added debian11/ubuntu20.04 support (PR #355)


0.9.0: 2019/03/29
-----------------

- Separate the concept of FabioFrame from FabioImage
- FileSeries are available from fabio.open_series
- Shape and dtype are directly exposed
- Support d*TREK format which is a superset of ADSC
- Improve code coverage on PiXi image
- Major refactoring of EdfImage (for better performances, padding, ...)
- Clean up TiffIO (remove tests & demo from source)
- Improved binning handling in DM3 images, and more quiet
- Implement deprecation warnings àla *silx*
- Enhanced installation on unsupported architectures
- Enhanced tests (spr, Fit2dSpreadsheet, Rigaku, ...)
- Tested on Python (2.7, 3.4), 3.5, 3.6 & 3.7 on mac, win & linux


0.8.0: 2018/10/26
-----------------

- Increased maximum header size for EDF (Thanks from OlivierU38)
- Fix EDF header (contribution from Yann Diorcet)
- MRC format is now tested (thanks to Aidan Campbell)
- Fix EDF regex in Python 3.7 (thanks to Serhiy Storchaka)
- New explicit registry (no more metaclass)
- Lazy iterator for EDF (useful for huge multi-frames)
- Improved JPEG 2000 support via glymur
- Manylinux1 wheels built against the oldest numpy possible
- Improved debian packaging
- clean up repository and tests
- Fix compilation with Python 3.7, Python 2.7 still works but for how long ?


0.7.0: 2018/06/26
-----------------

- Improve CBF support (support Python3, better support of loops)
- Improve Bruker100 image detection (contribution from Tomoya Onozuka)
- Support TIFF multi-frames
- Improve Pilatus TIFF support (contribution from Mika Pflüger)
- Improve support of TIFF using indexed colors
- Support pathlib and pathlib2 as opennable paths
- Provide a copy operator for single frame images
- Clean up EDF image API (contribution from Yann Diorcet)
- Fix parsing of EDF headers
- Fix convertion from EDF to TIFF
- Fix support of `#` in filenames
- Clean up of code and documentation (including contribution from Thomas Kluyver)


0.6.0: 2018/01/16
-----------------

- Improve CBF support (support Python3, better support of loops)
- Improve Bruker100 image detection (contribution from Tomoya Onozuka)
- Support TIFF multi-frames
- Improve Pilatus TIFF support (contribution from Mika Pflüger)
- Improve support of TIFF using indexed colors
- Support pathlib and pathlib2 as opennable paths
- Provide a copy operator for single frame images
- Clean up EDF image API (contribution from Yann Diorcet)
- Fix parsing of EDF headers
- Fix convertion from EDF to TIFF
- Fix support of `#` in filenames
- Clean up of code and documentation (including contribution from Thomas Kluyver)


0.5.0: 2017/08/29
-----------------

The main new features are:

- All source files are now under MIT license (re-implement PCK/packbits
in Cython)
- Context manager for fabio.open + automatic closing of files.
- Iterator over all frames in a file.
- Debian packaging for debian 7, 8 and 9.
- Use (patched-) ordered dictionaries for storing headers.
- Many clean up and bug-fixes
- New formats: mpa, jpeg and jpeg2000
- Provide "convert" and "viewer" scripts in the fabio-bin debian
package.


0.4.0: 2016/07/15
-----------------

- Write support for Bruker100 (contribution from Sigmund Neher)
- Read support for Princeton instrumentation cameras (contribution from Clemens Prescher)
- Read support for FIT2D binary format
- Read support for Eiger detector (Dectris) and generic HDF5 (partial)
- Switch ESRF-contributed file formats to MIT license (more liberal)
- Drop support for python 2.6, 3.2 and 3.3. Supports only 2.7 and 3.4+
- Include TiffIO into core of FabIO (no more third-party)
- Refactor mar345 (contributed by Henri Payno)
- Enhanced byte-offset compression using Cython
- Move master repository to silx-kit (https://github.com/silx-kit)


0.3.0: 2015/12/17
-----------------

- Migrate to PEP8 for class names.
- Use a factory & registry instead of fiddling in sys.modules for instance creation
- dim1, dim2, bpp and bytecode are properties. Use their private version while reading.
- FabioImage.header[“filename”] has disappeared. Use FabioImage.filename instead.
- Automatic backported package down to debian-8
- Compatibility checked with 2.6, 2.7, 3.2, 3.3, 3.4 and 3.5
- Continuous integration based on appveyor (windows) and travis (linux)
- Support for numpy 2d-array and PNM saving
- Move away from Sourceforge.


0.2.2: 2015/07/22
-----------------

- Fix bug in fabio_viewer
- Compatibility with ReadTheDocs.org
- Prepare multiple package for debian
- Fix regression when reading BytesIO


0.2.1: 2015/02/06
-----------------

Bugfix release for v0.2: all fileformat have been checked for endianness issues.


0.2.0: 2015/01/21
-----------------

Most noticeable changes are:

- Compatibility with Python3 (tested on Python 2.6, 2.7, 3.2 and 3.4)
- Support for Mar555 flat panel
- Optimization of CBF reader (about 2x faster)
- Include tests into installed module: fabio.tests()
- Tests data can be found in /usr/share/fabio/testimages or dynamically downloades into a temporary folder


0.1.3: 2013/10/28
-----------------

Version 0.1.3


0.1.2: 2013/04/02
-----------------

Release for version 0.1.2
