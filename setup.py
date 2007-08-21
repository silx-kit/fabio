


"""
Setup script for python distutils package and fabio

Added Erik Knudsen's mar 345 code
"""

from distutils.core import setup , Extension

mar345_backend = Extension('mar345_io',
                           sources = ['src/mar345_iomodule.c',
                                      'src/ccp4_pack.c'])

# See the distutils docs...
setup(name='fabio',
      description='Image IO for fable',
      ext_modules=[mar345_backend],
      packages = ["fabio"] ,
      package_dir = {"fabio": "src" } )
      