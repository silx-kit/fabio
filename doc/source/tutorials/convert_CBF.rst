
Convert a bunch of CBF files into EDF format
============================================

This simple tutorial explains how to convert a bunch of CBF files to EDF
files.

.. code:: python

    import glob
    files = glob.glob("*.cbf")
    files.sort()
    print("Number of files: %s" % len(files))


.. parsed-literal::

    Number of files: 200


.. code:: python

    dest_format = "edf"
    dest_dir = "edf_format"

.. code:: python

    import fabio, os
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

.. code:: python

    %%time
    for onefile in files:
        dst_name = os.path.join(dest_dir, os.path.splitext(onefile)[0] + "." + dest_format)
        fabio.open(onefile).convert(dest_format).save(dst_name)


.. parsed-literal::

    CPU times: user 2.36 s, sys: 2.84 s, total: 5.21 s
    Wall time: 5.64 s


.. code:: python

    print("The overall speed is %.1f frame/second"%(len(files)/5.64))


.. parsed-literal::

    The overall speed is 35.5 frame/second


Conclusion
----------

This simple tutorial explains how to perform simple file conversion. It
is likely to be limited by the bandwidth available for the hard-drive of
your computer or by the compression/decompression algorithm as it the
case here for CBF decompression.
