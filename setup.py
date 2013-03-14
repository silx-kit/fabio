#!/usr/bin/env python
#coding: utf8

"""
Setup script for python distutils package and fabio
"""
import os.path as op
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from distutils.core import Extension
from numpy.distutils.misc_util import get_numpy_include_dirs



cf_backend = Extension('cf_io', include_dirs=get_numpy_include_dirs(),
      sources=['src/cf_iomodule.c', 'src/columnfile.c'])

byteOffset_backend = Extension("byte_offset",
                       include_dirs=get_numpy_include_dirs(),
                           sources=['src/byte_offset.c'])

mar345_backend = Extension('mar345_IO',
                           include_dirs=get_numpy_include_dirs(),
                           sources=['src/mar345_IO.c',
                                    'src/ccp4_pack.c',
                                      ])

version = [eval(l.split("=")[1])
           for l in open(op.join(op.dirname(op.abspath(__file__)), "fabio-src", "__init__.py"))
           if l.strip().startswith("version")][0]


# See the distutils docs...
setup(name='fabio',
      version=version,
      author="Henning Sorensen, Erik Knudsen, Jon Wright, Regis Perdreau, Jérôme Kieffer and Gael Goret",
      author_email="fable-talk@lists.sourceforge.net",
      description='Image IO for fable',
      url="http://fable.wiki.sourceforge.net/fabio",
      download_url="http://sourceforge.net/projects/fable/files/fabio/0.1.1",
      ext_package="fabio",
      ext_modules=[mar345_backend, cf_backend, byteOffset_backend],
      packages=["fabio"],
      package_dir={"fabio": "fabio-src" },
      test_suite="test",
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Cython',
          'Programming Language :: C',
          'Topic :: Scientific/Engineering :: Chemistry',
          'Topic :: Scientific/Engineering :: Bio-Informatics',
          'Topic :: Scientific/Engineering :: Physics',
          'Topic :: Scientific/Engineering :: Visualization',
          'Topic :: Software Development :: Libraries :: Python Modules',
          ],)
