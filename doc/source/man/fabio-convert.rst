FabIO-Convert
=============

Purpose:
--------

`fabio-convert` is a portable image converter based on FabIO library.
It best work when converting single-frame files from one format to another.
For multi-frame files, the best is to use the Python API.

Usage:
------

fabio-convert [-h] [-V] [-v] [--debug] [-l] [-o OUTPUT] [-F FORMAT] [-f] [-n] [--remove-destination] [-u] [-i]
[--dry-run] [IMAGE ...]

Positional arguments:
+++++++++++++++++++++

IMAGE
   Input file images

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

**-l**, **--list**
   show the list of available formats and exit

**-o** OUTPUT, **--output** OUTPUT
   output file or directory

**-F** FORMAT, **--output-format** FORMAT
   output format

Optional behaviour arguments:
+++++++++++++++++++++++++++++

**-f**, **--force**
   if an existing destination file cannot be opened, remove it and try
   again (this option is ignored when the **-n** option is also used)

**-n**, **--no-clobber**
   do not overwrite an existing file (this option is ignored when the
   **-i** option is also used)

**--remove-destination**
   remove each existing destination file before attempting to open it
   (contrast with **--force**)

**-u**, **--update**
   copy only when the SOURCE file is newer than the destination file or
   when the destination file is missing

**-i**, **--interactive**
   prompt before overwrite (overrides a previous **-n** option)

**--dry-run**
   do everything except modifying the file system

Return code: 
++++++++++++

- 0 means a success. 
- 1 means the conversion contains a failure, 
- 2 means there was an error in the arguments


.. command-output:: fabio-convert --help
    :nostderr: