Eiger2CBF
=========

Purpose
-------

Convert a multiframe HDF5 Eiger data file into several CBF files.
 
Portable image converter based on FabIO library to export Eiger frames (``lima`` or ``eiger``) 
to CBF which mimic the header of a Dectris Pilatus detector.

Usage:
------

eiger2cbf [-h] [-V] [-v] [--debug] [-o OUTPUT] [-m MASK] [-O OFFSET] [-D DUMMY] [--pilatus] [--dry-run] [-e ENERGY]
[-w WAVELENGTH] [-d DISTANCE] [-b BEAM BEAM] [--alpha ALPHA] [--kappa KAPPA] [--chi CHI] [--phi PHI]
[--omega OMEGA] [--rotation ROTATION] [--transpose] [--flip-ud] [--flip-lr]
[IMAGE ...]

Positional arguments:
+++++++++++++++++++++

IMAGE
   File with input images

Options:
++++++++

**-h**, **--help**
   show this help message and exit

**-V**, **--version**
   output version and exit

**-v**, **--verbose**
   show information for each conversions

**--debug**
   show debug information

Main arguments:
+++++++++++++++

**-o** OUTPUT, **--output** OUTPUT
   output directory and filename template:
   ``eiger2cbf/frame_{index:04d}.cbf``

**-m** MASK, **--mask** MASK
   Read masked pixel from this file

**-O** OFFSET, **--offset** OFFSET
   index offset, CrysalisPro likes indexes to start at 1, 
   Python starts at 0 (default)

**-D** DUMMY, **--dummy** DUMMY
   Set masked values to this dummy value

**--pilatus**
   Select an image shape similar to Pilatus detectors for compatibiliy
   with Crysalis

Optional behaviour arguments:
+++++++++++++++++++++++++++++

**--dry-run**
   do everything except modifying the file system

Experimental setup options:
+++++++++++++++++++++++++++

**-e** ENERGY, **--energy** ENERGY
   Energy of the incident beam in keV

**-w** WAVELENGTH, **--wavelength** WAVELENGTH
   Wavelength of the incident beam in Angstrom

**-d** DISTANCE, **--distance** DISTANCE
   Detector distance in meters

**-b** BEAM BEAM, **--beam** BEAM BEAM
   Direct beam in pixels x, y

Goniometer setup:
-----------------

**--alpha** ALPHA
   Goniometer angle alpha value in deg. 
   Constant, angle between kappa and omega.

**--kappa** KAPPA
   Goniometer angle kappa value in degrees or formula f(index)
   ``-80 + 2*index``

**--chi** CHI
   Goniometer angle chi value in degres or formula f(index)

**--phi** PHI
   Goniometer angle phi value (inner-most rotation) in degrees or formula f(index)
   ``-180+0.7*index``

**--omega** OMEGA
   Goniometer angle omega value (outer-most rotation) in degrees or formula f(index)
   ``-180+0.5*index``

Image preprocessing:
++++++++++++++++++++

Images are patched onto the center of a square frame, and transformation are applied in this order:

**--rotation** ROTATION
   Rotate the initial image by this value in degrees. Must be a multiple
   of 90 degrees.

**--transpose**
   Flip the x/y axis

**--flip-ud**
   Flip the image upside-down

**--flip-lr**
   Flip the image left-right

Return code: 
++++++++++++

- 0 means a success. 
- 1 means the conversion contains a failure, 
- 2 means there was an error in the arguments

Nota:
-----

Images are made square, so the beam center found in the CBF-files differs from the one entered. 


.. command-output:: eiger2cbf --help
    :nostderr:
  