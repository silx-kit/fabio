#!/usr/bin/env python
# coding: utf8

"""
Setup script for python distutils package and fabio
"""
import os, sys
import os.path as op
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from distutils.core import Extension, Command
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
#######################
# build_doc commandes #
#######################
cmdclass = {}

try:
    import sphinx
    import sphinx.util.console
    sphinx.util.console.color_terminal = lambda: False
    from sphinx.setup_command import BuildDoc
except ImportError:
    sphinx = None

if sphinx:
    class build_doc(BuildDoc):

        def run(self):
            # make sure the python path is pointing to the newly built
            # code so that the documentation is built on this and not a
            # previously installed version

            build = self.get_finalized_command('build')
            print(os.path.abspath(build.build_lib))
            sys.path.insert(0, os.path.abspath(build.build_lib))
            # we need to reload PyMca from the build directory and not
            # the one from the source directory which does not contain
            # the extensions
            BuildDoc.run(self)
            sys.path.pop(0)
    cmdclass['build_doc'] = build_doc

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import subprocess
        os.chdir("test")
        errno = subprocess.call([sys.executable, 'test_all.py'])
        if errno != 0:
            raise SystemExit(errno)
        else:
            os.chdir("..")
cmdclass['test'] = PyTest

# See the distutils docs...
setup(name='fabio',
      version=version,
      author="Henning Sorensen, Erik Knudsen, Jon Wright, Regis Perdreau, Jérôme Kieffer and Gael Goret",
      author_email="fable-talk@lists.sourceforge.net",
      description='Image IO for fable',
      url="http://fable.wiki.sourceforge.net/fabio",
      download_url="http://sourceforge.net/projects/fable/files/fabio/0.1.2",
      ext_package="fabio",
      ext_modules=[mar345_backend, cf_backend, byteOffset_backend],
      packages=["fabio"],
      package_dir={"fabio": "fabio-src" },
      test_suite="test",
      cmdclass=cmdclass,
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
