try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils.core import  Extension
from Cython.Distutils import build_ext

# for numpy
from numpy.distutils.misc_util import get_numpy_include_dirs


mar345_ext = Extension("mar345_IO",
                    include_dirs=get_numpy_include_dirs(),
                    sources=["pack_c.c", 'mar345_IO.c', "ccp4_pack.c"])


setup(name='mar345_IO',
      version="0.0.0",
      author="Jerome Kieffer",
      author_email="jerome.kieffer@esrf.eu",
      description='Mar345 writer',
      ext_modules=[mar345_ext],
      cmdclass={'build_ext': build_ext},
      )


