FabIO-Convert
=============

Purpose:
--------

`fabio-convert` is a portable image converter based on FabIO library.
By default, it converts the current image from each input file.
Use ``--split`` to convert every frame of a multi-frame file into separate
single-frame files. Combining files into a multi-frame image still requires
the Python API.

Usage:
------

fabio-convert [-h] [-V] [-v] [-\-debug] [-l] [-o OUTPUT] [-F FORMAT] [-f] [-n] [-\-remove-destination] [-u] [-i]
[-\-dry-run] [-\-split] [IMAGE ...]

Positional arguments:
+++++++++++++++++++++

IMAGE
   Input file images

Options:
++++++++

**-h**, **-\-help**
   show this help message and exit

**-V**, **-\-version**
   output version and exit

**-v**, **-\-verbose**
   show information for each conversion

**-\-debug**
   show debug information

Main arguments:
+++++++++++++++

**-l**, **-\-list**
   show the list of available formats and exit

**-o** OUTPUT, **-\-output** OUTPUT
   output file or directory

**-F** FORMAT, **-\-output-format** FORMAT
   output format

Optional behaviour arguments:
+++++++++++++++++++++++++++++

**-\-split**
   Write each frame to a separate file. Insert a zero-based frame number,
   padded to at least four digits, before the output extension. For example,
   ``fabio-convert --split stack.edf -F tif`` writes ``stack_0000.tif``,
   ``stack_0001.tif``, and so on. A single-frame input gets ``_0000`` too.

   With ``-o frames`` pointing to an existing directory, write the numbered
   files there. For one input, ``-o result.edf`` instead uses names such as
   ``result_0000.edf``. Multiple inputs require an output directory when
   ``-o`` is specified. Existing overwrite options apply to each frame;
   ``--dry-run`` writes no files. Inputs and duplicate destinations from
   different input files are protected even with ``--force``.

**-f**, **-\-force**
   if an existing destination file cannot be opened, remove it and try
   again (this option is ignored when the **-n** option is also used)

**-n**, **-\-no-clobber**
   do not overwrite an existing file (this option is ignored when the
   **-i** option is also used)

**-\-remove-destination**
   remove each existing destination file before attempting to open it
   (contrast with **--force**)

**-u**, **-\-update**
   copy only when the SOURCE file is newer than the destination file or
   when the destination file is missing

**-i**, **-\-interactive**
   prompt before overwrite (overrides a previous **-n** option)

**-\-dry-run**
   do everything except modifying the file system

Return code: 
++++++++++++

- 0 means a success. 
- 1 means the conversion contains a failure, 
- 2 means there was an error in the arguments


.. command-output:: fabio-convert --help
    :nostderr:
