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
                                    'src/pack_c.c',
                                      ])

version = [eval(l.split("=")[1])
           for l in open(op.join(op.dirname(op.abspath(__file__)), "fabio", "__init__.py"))
           if l.strip().startswith("version")][0]


# See the distutils docs...
setup(name='fabio',
      version=version,
      author="Henning Sorensen, Erik Knudsen, Jon Wright, Regis Perdreau and Jérôme Kieffer",
      author_email="fable-talk@lists.sourceforge.net",
      description='Image IO for fable',
      url="http://fable.wiki.sourceforge.net/fabio",
      download_url="http://sourceforge.net/projects/fable/files/fabio/0.0.9",
      ext_package="fabio",
      ext_modules=[mar345_backend, cf_backend, byteOffset_backend],
      packages=["fabio"],
      package_dir={"fabio": "fabio" },
      test_suite="test"
      )


