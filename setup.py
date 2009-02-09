


"""
Setup script for python distutils package and fabio

Added Erik Knudsen's mar 345 code
"""

from distutils.core import setup , Extension

# for numpy
from numpy.distutils.misc_util import get_numpy_include_dirs


mar345_backend = Extension('mar345_io',
                           include_dirs = get_numpy_include_dirs(),
                           sources = ['src/mar345_iomodule.c',
                                      'src/ccp4_pack.c'])

# See the distutils docs...
setup(name='fabio',
      version="0.0.4",
      author = "Henning Sorensen, Erik Knudsen and Jon Wright",
      author_email = "fable-talk@lists.sourceforge.net",
      description='Image IO for fable',
      url = "http://fable.wiki.sourceforge.net/fabio",
      ext_modules=[mar345_backend],
      packages = ["fabio"] ,
      package_dir = {"fabio": "src" } )
      
