#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function, division

"""
Setup script for python distutils package and fabio
"""
import os, sys
import os.path as op
import glob
import shutil
from distutils.core import setup
from distutils.core import Extension, Command
import numpy as np
from distutils.command.sdist import sdist

################################################################################
# Remove MANIFEST file ... it needs to be re-generated on the fly
################################################################################
if op.isfile("MANIFEST"):
    os.unlink("MANIFEST")


################################################################################
# Check for Cython and use it if it is available
################################################################################
USE_CYTHON = True
try:
    import Cython.Compiler.Version
    from Cython.Distutils import build_ext
except ImportError:
    USE_CYTHON = False
else:
    if Cython.Compiler.Version.version < "0.17":
        USE_CYTHON = False
    else:
        USE_CYTHON = True

if USE_CYTHON:
    ext = ".pyx"
else:
    from distutils.command.build_ext import build_ext
    ext = ".c"


cf_backend = Extension('cf_io',
                       include_dirs=[np.get_include()],
                       sources=['src/cf_io' + ext, 'src/columnfile.c'])
byteOffset_backend = Extension("byte_offset",
                       include_dirs=[np.get_include()],
                       sources=['src/byte_offset' + ext])

mar345_backend = Extension('mar345_IO',
                           include_dirs=[np.get_include()],
                           sources=['src/mar345_IO' + ext,
                                    'src/ccp4_pack.c',
                                      ])

extensions = [cf_backend, byteOffset_backend, mar345_backend]

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
            print(op.abspath(build.build_lib))
            sys.path.insert(0, op.abspath(build.build_lib))
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
        os.chdir(op.join(op.dirname(op.abspath(__file__)), "test"))
        errno = subprocess.call([sys.executable, 'test_all.py'])
        if errno != 0:
            raise SystemExit(errno)
        else:
            os.chdir("..")
cmdclass['test'] = PyTest

# We subclass the build_ext class in order to handle compiler flags
# for openmp and opencl etc in a cross platform way
translator = {
        # Compiler
            # name, compileflag, linkflag
        'msvc' : {
            'openmp' : ('/openmp', ' '),
            'debug'  : ('/Zi', ' '),
            'OpenCL' : 'OpenCL',
            },
        'mingw32':{
            'openmp' : ('-fopenmp', '-fopenmp'),
            'debug'  : ('-g', '-g'),
            'stdc++' : 'stdc++',
            'OpenCL' : 'OpenCL'
            },
        'default':{
            'openmp' : ('-fopenmp', '-fopenmp'),
            'debug'  : ('-g', '-g'),
            'stdc++' : 'stdc++',
            'OpenCL' : 'OpenCL'
            }
        }


class build_ext_FabIO(build_ext):
    def build_extensions(self):
        if self.compiler.compiler_type in translator:
            trans = translator[self.compiler.compiler_type]
        else:
            trans = translator['default']

        for e in self.extensions:
            e.extra_compile_args = [ trans[a][0] if a in trans else a
                                    for a in e.extra_compile_args]
            e.extra_link_args = [ trans[a][1] if a in trans else a
                                 for a in e.extra_link_args]
            e.libraries = list(filter(None, [ trans[a] if a in trans else None
                                        for a in e.libraries]))
        build_ext.build_extensions(self)
cmdclass['build_ext'] = build_ext_FabIO


################################################################################
# Debian source tree
################################################################################

class sdist_debian(sdist):
    """
    Tailor made sdist for debian
    * remove auto-generated doc
    * remove cython generated .c files
    * add image files from test/testimages/*
    """
    def prune_file_list(self):
        sdist.prune_file_list(self)
        to_remove = ["doc/build", "doc/pdf", "doc/html", "pylint", "epydoc"]
        print("Removing files for debian")
        for rm in to_remove:
            self.filelist.exclude_pattern(pattern="*", anchor=False, prefix=rm)
        #this is for Cython files specifically
        self.filelist.exclude_pattern(pattern="*.html", anchor=True, prefix="src")
        for pyxf in glob.glob("src/*.pyx"):
            cf = op.splitext(pyxf)[0] + ".c"
            if op.isfile(cf):
                self.filelist.exclude_pattern(pattern=cf)
        for ex in ["argparse", "gzip"]:
            self.filelist.exclude_pattern(pattern=ex + ".py", anchor=True, prefix="fabio-src")
        print("Adding test_files for debian")
        self.filelist.allfiles += (glob.glob("test/testimages/*"))
        self.filelist.include_pattern(pattern="*.bz2", anchor=True,
                                     prefix="test/testimages")
    def make_distribution(self):
        sdist.make_distribution(self)
        dest = self.archive_files[0]
        dirname, basename = op.split(dest)
        base, ext = op.splitext(basename)
        while ext in [".zip", ".tar", ".bz2", ".gz", ".Z", ".lz", ".orig"]:
            base, ext = op.splitext(base)
        if ext:
            dest = "".join((base, ext))
        else:
            dest = base
        sp = dest.split("-")
        base = sp[:-1]
        nr = sp[-1]
        debian_arch = op.join(dirname, "-".join(base) + "_" + nr + ".orig.tar.gz")
        os.rename(self.archive_files[0], debian_arch)
        self.archive_files = [debian_arch]
        print("Building debian .orig.tar.gz in %s" % self.archive_files[0])

cmdclass['debian_src'] = sdist_debian


if sys.platform == "win32":
    root = op.dirname(op.abspath(__file__))
    tocopy_files = []
    script_files = []
    for i in os.listdir(op.join(root, "scripts")):
        if op.isfile(op.join(root, "scripts", i)):
            if i.endswith(".py"):
                script_files.append(op.join("scripts", i))
            else:
                tocopy_files.append(op.join("scripts", i))
    for i in tocopy_files:
        filein = op.join(root, i)
        if (filein + ".py") not in script_files:
            shutil.copyfile(filein, filein + ".py")
            script_files.append(filein + ".py")
else:
    script_files = glob.glob("scripts/*")


setup(name='fabio',
      version=version,
      author="Henning Sorensen, Erik Knudsen, Jon Wright, Regis Perdreau, Jérôme Kieffer, Gael Goret, Brian Pauw",
      author_email="fable-talk@lists.sourceforge.net",
      description='Image IO for fable',
      url="http://fable.wiki.sourceforge.net/fabio",
      download_url="http://sourceforge.net/projects/fable/files/fabio/0.1.4",
      ext_package="fabio",
      ext_modules=extensions,
      packages=["fabio"],
      package_dir={"fabio": "fabio-src" },
      test_suite="test",
      cmdclass=cmdclass,
      scripts=script_files,
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
