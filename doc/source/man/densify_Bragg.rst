Densify_Bragg
=============

``densify_Bragg`` is a tool to decompress the sparse data-format used at the ESRF-ID29 beamline with the 
Jungfrau detector.

Each file stores the information for a few thousands frames, each frame is composed of:

* a background profile with the associated uncertainties
* a list of pixel values and positions. 

The decompression is called densification since only sparse pixel positions were recorded.
The background can be made more realistic by regenerating some natural looking noise.
Depending on the data reduction software used later-on, noise is needed (XDS) or detrimental (Crysalis)
for subsequent analysis.

Usage
-----

densify_Bragg [-h] [-V] [-v] [--debug] [-l] [-o OUTPUT] [-O FORMAT]
[-D DUMMY] [--dry-run] [-N NOISY] [IMAGE ...]

Positional arguments:
---------------------

IMAGE
   File with sparse images stored in them

Pptions:
--------

**-h**, **--help**
   show this help message and exit

**-V**, **--version**
   output version and exit

**-v**, **--verbose**
   show information for each conversions

**--debug**
   show debug information

Main arguments:
---------------

**-l**, **--list**
   show the list of available output formats and exit

**-o** OUTPUT, **--output** OUTPUT
   output filename, by default {baseame}_densify.h5

**-O** FORMAT, **--output-format** FORMAT
   output format among ``lima``, ``eiger`` ...

**-D** DUMMY, **--dummy** DUMMY
   Set masked values to this dummy value

optional behaviour arguments:
-----------------------------

**--dry-run**
   do everything except modifying the file system

**-N** NOISY, **--noise** NOISY
   Noise scaling factor, from 0 to 1, set to 0 to disable the noise
   reconstruction

Return code: 
++++++++++++

- 0 means a success. 
- 1 means the conversion contains a failure, 
- 2 means there was an error in the arguments


.. command-output:: densify_Bragg --help
    :nostderr:
