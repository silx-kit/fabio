#!/usr/bin/env python
#coding: utf8

"""
Setup script for python distutils package and fabio

Added Erik Knudsen's mar 345 code
"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils.core import  Extension


# for numpy
from numpy.distutils.misc_util import get_numpy_include_dirs



mar345_backend = Extension('mar345_io',
                           include_dirs=get_numpy_include_dirs(),
                           sources=['src/mar345_iomodule.c',
                                      'src/ccp4_pack.c'])

cf_backend = Extension('cf_io', include_dirs=get_numpy_include_dirs(),
      sources=['src/cf_iomodule.c', 'src/columnfile.c'])

byteOffset_backend = Extension("byte_offset",
                       include_dirs=get_numpy_include_dirs(),
                           sources=['src/byte_offset.c'])

# See the distutils docs...
setup(name='fabio',
      version="0.0.9",
      author="Henning Sorensen, Erik Knudsen, Jon Wright, Regis Perdreau and Jerome Kieffer",
      author_email="fable-talk@lists.sourceforge.net",
      description='Image IO for fable',
      url="http://fable.wiki.sourceforge.net/fabio",
      download_url="http://sourceforge.net/projects/fable/files/fabio/0.0.9",
      ext_package="fabio",
#      cmdclass = {'build_ext': build_ext},
      ext_modules=[mar345_backend, cf_backend, byteOffset_backend ],
      packages=["fabio"],
      package_dir={"fabio": "fabio" },
      test_suite="test"
      )


