Eiger2Crysalis
==============

Purpose:
--------

Convert a stack of images acquires with an Eiger detector (HDF5, format `eiger` or `lima`) into a CrysalisPro project

CrysalisPro is a single-crystal data reduction program developped by Mathias Meyer 
and gracefully made available free of charge by Rigaku.

The Crysalis project directory is populated with:

- a set of Esperanto files, corresponding to the different frames of the HDF5 file
- a set-file, ascii format, with the description of the detector (mostly unused)
- a ccd-file, binary format, with the description of the mask of the detector
- a par-file, ascii format, with the description of the sample, goniometer, source, ...
- a run-file, binary format, with the description of the scans (sometimes called sweep in MX)  

The directory can directly be opened with CrysalisPro.

Usage:
------
 
eiger2crysalis [-h] [-V] [-v] [--debug] [-l] [-o OUTPUT] [-O OFFSET] [-D DUMMY] [--dry-run] [--calc-mask] [-e ENERGY]
[-w WAVELENGTH] [-d DISTANCE] [-b BEAM BEAM] [-p POLARIZATION] [--alpha ALPHA] [--kappa KAPPA]
[--phi PHI] [--omega OMEGA] [--theta THETA] [--rotation ROTATION] [--transpose] [--flip-ud]
[--flip-lr] [IMAGE ...]


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

**-l**, **--list**
   show the list of available formats and exit
   
Main arguments:
+++++++++++++++

**-o** OUTPUT, **--output** OUTPUT
   output directory and filename template, for example 
   `{basename}/crysalis/scan_1_{index}.esperanto`

**-O** OFFSET, **--offset** OFFSET
   index offset, CrysalisPro likes indexes to start at 1, 
   Python starts at 0. The default is 1

**-D** DUMMY, **--dummy** DUMMY
   Set masked values to this dummy value

Optional behaviour arguments:
+++++++++++++++++++++++++++++

**--dry-run**
   do everything except modifying the file system

**--calc-mask**
   Generate a fine mask from pixels marked as invalid. 
   By default, only treats gaps (faster)
   
Experimental setup options:
+++++++++++++++++++++++++++

**-e** ENERGY, **--energy** ENERGY
   Energy of the incident beam in keV

**-w** WAVELENGTH, **--wavelength** WAVELENGTH
   Wavelength of the incident beam in Angstrom

**-d** DISTANCE, **--distance** DISTANCE
   Detector distance in millimeters

**-b** BEAM BEAM, **--beam** BEAM BEAM
   Direct beam in pixels x, y

**-p** POLARIZATION, **--polarization** POLARIZATION
   Polarization factor (0.99 by default on synchrotron)

Goniometer setup:
+++++++++++++++++

**--alpha** ALPHA
   Goniometer angle alpha value in deg. 
   Constant, angle between kappa and omega.

**--kappa** KAPPA
   Goniometer angle kappa value in degrees or formula f(index)
   ``-80 + 2*index``

**--phi** PHI
   Goniometer angle phi value (inner-most rotation) in degrees or formula f(index)
   ``-180+0.7*index``

**--omega** OMEGA
   Goniometer angle omega value (outer-most rotation) in degrees or formula f(index)
   ``-180+0.5*index``

**--theta** THETA
   Goniometer angle theta value (angle of the detector arm) in degrees or formula f(index).
   ``-50+5*index``

**Nota:** only one angle can vary during a given scan. 

Image preprocessing:
++++++++++++++++++++

Images are patched onto the center of a square frame, and transformation are applied in this order:

**--rotation** ROTATION
   Rotate the initial image by this value in degrees. Must be a multiple
   of 90??. By default 180 deg (flip_up with origin=lower and flip_lr
   because the image is seen from the sample).

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

Images are made square, so the beam center found in the eperanto image differs from the one entered. 

.. command-output:: eiger2crysalis --help
    :nostderr: