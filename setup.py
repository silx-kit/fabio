#!/usr/bin/env python
# coding: utf-8
#
#    Project: Fable Input/Output
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import print_function, division, with_statement, absolute_import

__doc__ = """ Setup script for python distutils package and fabio """
__author__ = "Jerome Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "07/07/2016"
__status__ = "stable"

import os
import time
import sys
import glob
import shutil
import numpy


try:
    # setuptools allows the creation of wheels
    from setuptools import setup, Command
    from setuptools.command.sdist import sdist
    from setuptools.command.build_ext import build_ext
    from setuptools.command.install_data import install_data
    from setuptools.command.install import install
    from setuptools.command.build_py import build_py as _build_py
except ImportError:
    from distutils.core import setup, Command
    from distutils.command.sdist import sdist
    from distutils.command.build_ext import build_ext
    from distutils.command.install_data import install_data
    from distutils.command.install import install
    from distutils.command.build_py import build_py as _build_py
from numpy.distutils.core import Extension as _Extension
from distutils.filelist import FileList

PROJECT = "fabio"
install_warning = False
cmdclass = {}

################################################################################
# Remove MANIFEST file ... it needs to be re-generated on the fly
################################################################################
manifest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MANIFEST")
if os.path.isfile(manifest):
    os.unlink(manifest)


################################################################################
# Check for Cython and use it if it is available
################################################################################

def check_cython():
    """
    Check if cython must be activated fron te command line or the environment.
    """

    if "WITH_CYTHON" in os.environ and os.environ["WITH_CYTHON"] == "False":
        print("No Cython requested by environment")
        return False

    if ("--no-cython" in sys.argv):
        sys.argv.remove("--no-cython")
        os.environ["WITH_CYTHON"] = "False"
        print("No Cython requested by command line")
        return False

    try:
        import Cython.Compiler.Version
    except ImportError:
        return False
    else:
        if Cython.Compiler.Version.version < "0.17":
            return False
    return True


USE_CYTHON = check_cython()
USE_OPENMP = False
if USE_CYTHON:
    from Cython.Build import cythonize


def Extension(name, source=None, can_use_openmp=False, extra_sources=None, **kwargs):
    """
    Wrapper for distutils' Extension
    """
    if name.startswith(PROJECT + ".ext."):
        name = name[len(PROJECT) + 5:]
    if source is None:
        source = name
    cython_c_ext = ".pyx" if USE_CYTHON else ".c"
    sources = [os.path.join(PROJECT, "ext", source + cython_c_ext)]
    if extra_sources:
        sources.extend(extra_sources)
    if "include_dirs" in kwargs:
        include_dirs = set(kwargs.pop("include_dirs"))
        include_dirs.add(numpy.get_include())
        include_dirs.add(os.path.join(PROJECT, "ext"))
        include_dirs.add(os.path.join(PROJECT, "ext", "include"))
        include_dirs = list(include_dirs)
    else:
        include_dirs = [os.path.join(PROJECT, "ext", "include"),
                        os.path.join(PROJECT, "ext"), numpy.get_include()]

    if can_use_openmp and USE_OPENMP:
        extra_compile_args = set(kwargs.pop("extra_compile_args", []))
        extra_compile_args.add(USE_OPENMP)
        kwargs["extra_compile_args"] = list(extra_compile_args)

        extra_link_args = set(kwargs.pop("extra_link_args", []))
        extra_link_args.add(USE_OPENMP)
        kwargs["extra_link_args"] = list(extra_link_args)

    ext = _Extension(name=PROJECT + ".ext." + name, sources=sources, include_dirs=include_dirs, **kwargs)

    if USE_CYTHON:
        cext = cythonize([ext], compile_time_env={"HAVE_OPENMP": bool(USE_OPENMP)})
        if cext:
            ext = cext[0]
    return ext

ext_modules = [Extension('cf_io', extra_sources=['fabio/ext/src/columnfile.c']),
               Extension("byte_offset"),
               Extension('mar345_IO', extra_sources=['fabio/ext/src/ccp4_pack.c']),
               Extension('_cif')]


##############
# version.py #
##############
class build_py(_build_py):
    """
    Enhanced build_py which copies version.py to <PROJECT>._version.py
    """
    def find_package_modules(self, package, package_dir):
        modules = _build_py.find_package_modules(self, package, package_dir)
        if package == PROJECT:
            modules.append((PROJECT, '_version', 'version.py'))
        return modules

cmdclass['build_py'] = build_py

if install_warning:
    class InstallWarning(install):
        def __init__(self, *arg, **kwarg):
            print("The usage of 'python setup.py is deprecated. Please use 'pip install .' instead")
            time.sleep(0.5)
            install.__init__(self, *arg, **kwarg)
    cmdclass['install'] = InstallWarning


def get_version():
    import version
    return version.strictversion


def get_readme():
    """Provide the long description as an Unicode string"""
    dirname = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(dirname, "README.rst"), "rb") as fp:
        long_description = fp.read()
    return long_description.decode("utf-8")


#######################
# build_doc commandes #
#######################
try:
    import sphinx
    import sphinx.util.console
    sphinx.util.console.color_terminal = lambda: False
    from sphinx.setup_command import BuildDoc
except ImportError:
    sphinx = None

else:
    # i.e. if sphinx:
    class build_doc(BuildDoc):

        def run(self):
            # make sure the python path is pointing to the newly built
            # code so that the documentation is built on this and not a
            # previously installed version

            build = self.get_finalized_command('build')
            sys.path.insert(0, os.path.abspath(build.build_lib))
            script_dir = os.path.abspath("scripts")
            os.environ["PATH"] = "%s%s%s" % (script_dir, os.pathsep, os.environ.get("PATH", ""))
            # Build the Users Guide in HTML and TeX format
            for builder in ('html', 'latex'):
                self.builder = builder
                self.builder_target_dir = os.path.join(self.build_dir, builder)
                self.mkpath(self.builder_target_dir)
                BuildDoc.run(self)
            sys.path.pop(0)
            os.environ["PATH"] = os.pathsep.join(os.environ.get("PATH").split(os.pathsep)[1:])
    cmdclass['build_doc'] = build_doc


# We subclass the build_ext class in order to handle compiler flags
# for openmp and opencl etc in a cross platform way
translator = {
        # Compiler
        # name, compileflag, linkflag
        'msvc': {
                 'openmp': ('/openmp', ' '),
                 'debug': ('/Zi', ' '),
                 'OpenCL': 'OpenCL',
                },
        'mingw32': {
                    'openmp': ('-fopenmp', '-fopenmp'),
                    'debug': ('-g', '-g'),
                    'stdc++': 'stdc++',
                    'OpenCL': 'OpenCL'
                   },
        'default': {
                    'openmp': ('-fopenmp', '-fopenmp'),
                    'debug': ('-g', '-g'),
                    'stdc++': 'stdc++',
                    'OpenCL': 'OpenCL'
                   }
              }


class build_ext_FabIO(build_ext):
    def build_extensions(self):
        if self.compiler.compiler_type in translator:
            trans = translator[self.compiler.compiler_type]
        else:
            trans = translator['default']

        for e in self.extensions:
            e.extra_compile_args = [trans[a][0] if a in trans else a
                                    for a in e.extra_compile_args]
            e.extra_link_args = [trans[a][1] if a in trans else a
                                 for a in e.extra_link_args]
            e.libraries = [trans[arg] for arg in e.libraries if arg in trans]
        build_ext.build_extensions(self)
cmdclass['build_ext'] = build_ext_FabIO


################################################################################
# Debian source tree
################################################################################
def download_images():
    """
    Download all test images and
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(root_dir, PROJECT, "test")
    sys.path.insert(0, test_dir)
    from utilstest import UtilsTest
    image_home = os.path.join(root_dir, "testimages")
    testimages = os.path.join(root_dir, "all_testimages.json")
    UtilsTest.image_home = image_home
    UtilsTest.testimages = testimages
    if os.path.exists(testimages):
        import json
        with open(testimages) as f:
            all_files = set(json.load(f))
    else:
        raise(RuntimeError("Please run 'python setup.py build test' to download all images"))
    for afile in all_files.copy():
        if afile.endswith(".bz2"):
            all_files.add(afile[:-4] + ".gz")
            all_files.add(afile[:-4])
        elif afile.endswith(".gz"):
            all_files.add(afile[:-3] + ".bz2")
            all_files.add(afile[:-3])
        else:
            all_files.add(afile + ".gz")
            all_files.add(afile + ".bz2")
    UtilsTest.download_images(all_files)
    return list(all_files)


class sdist_debian(sdist):
    """
    Tailor made sdist for debian
    * remove auto-generated doc
    * remove cython generated .c files
    """
    @staticmethod
    def get_debian_name():
        import version
        name = "%s_%s" % (PROJECT, version.debianversion)
        return name

    def prune_file_list(self):
        sdist.prune_file_list(self)
        to_remove = ["doc/build", "doc/pdf", "doc/html", "pylint", "epydoc"]
        print("Removing files for debian")
        for rm in to_remove:
            self.filelist.exclude_pattern(pattern="*", anchor=False, prefix=rm)
        # this is for Cython files specifically
        self.filelist.exclude_pattern(pattern="*.html", anchor=True, prefix=PROJECT + "ext")
        for pyxf in glob.glob(PROJECT + "ext/*.pyx"):
            cf = os.path.splitext(pyxf)[0] + ".c"
            if os.path.isfile(cf):
                self.filelist.exclude_pattern(pattern=cf)

    def make_distribution(self):
        self.prune_file_list()
        sdist.make_distribution(self)
        dest = self.archive_files[0]
        dirname, basename = os.path.split(dest)
        base, ext = os.path.splitext(basename)
        while ext in [".zip", ".tar", ".bz2", ".gz", ".Z", ".lz", ".orig"]:
            base, ext = os.path.splitext(base)
        if ext:
            dest = "".join((base, ext))
        else:
            dest = base
#         sp = dest.split("-")
#         base = sp[:-1]
#         nr = sp[-1]
        debian_arch = os.path.join(dirname, self.get_debian_name() + ".orig.tar.gz")
        os.rename(self.archive_files[0], debian_arch)
        self.archive_files = [debian_arch]
        print("Building debian .orig.tar.gz in %s" % self.archive_files[0])

cmdclass['debian_src'] = sdist_debian


class TestData(Command):
    """
    Tailor made tarball with test data
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        datafiles = download_images()
        dist = "dist"
        arch = os.path.join(dist, PROJECT + "-testimages.tar.gz")
        print("Building testdata tarball in %s" % arch)
        if not os.path.isdir(dist):
            os.mkdir(dist)
        if os.path.exists(arch):
            os.unlink(arch)
        import tarfile
        with tarfile.open(name=arch, mode='w:gz') as tarball:
            for afile in datafiles:
                tarball.add(os.path.join("testimages", afile), afile)
cmdclass['testimages'] = TestData


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        errno = subprocess.call([sys.executable, 'run_tests.py', '-i'])
        if errno != 0:
            raise SystemExit(errno)
cmdclass['test'] = PyTest


if sys.platform == "win32":
    root = os.path.dirname(os.path.abspath(__file__))
    tocopy_files = []
    script_files = []
    for i in os.listdir(os.path.join(root, "scripts")):
        if os.path.isfile(os.path.join(root, "scripts", i)):
            if i.endswith(".py"):
                script_files.append(os.path.join("scripts", i))
            else:
                tocopy_files.append(os.path.join("scripts", i))
    for i in tocopy_files:
        filein = os.path.join(root, i)
        if (filein + ".py") not in script_files:
            shutil.copyfile(filein, filein + ".py")
            script_files.append(filein + ".py")
else:
    script_files = glob.glob("scripts/*")


install_requires = ["numpy"]
setup_requires = ["numpy", "cython"]


# adaptation for Debian packaging (without third_party)
packages = [PROJECT, PROJECT + ".test", PROJECT + ".ext", PROJECT + ".benchmark"]
package_dir = {PROJECT: PROJECT,
               PROJECT + ".test": PROJECT + "/test",
               PROJECT + ".ext": PROJECT + "/ext",
               PROJECT + ".benchmark": PROJECT + "/benchmark"}
if os.path.isdir("third_party"):
    package_dir[PROJECT + ".third_party"] = "third_party"
    packages.append(PROJECT + ".third_party")

classifiers = [
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
                ]

if __name__ == "__main__":
    setup(name=PROJECT,
          version=get_version(),
          author="Henning Sorensen, Erik Knudsen, Jon Wright, Regis Perdreau, Jérôme Kieffer, Gael Goret, Brian Pauw",
          author_email="fable-talk@lists.sourceforge.net",
          description='Image IO for fable',
          url="http://fable.wiki.sourceforge.net/fabio",
          download_url="https://github.com/silx-kit/fabio/releases",
          # ext_package="fabio",
          scripts=script_files,
          ext_modules=ext_modules,
          packages=packages,
          package_dir=package_dir,
          test_suite="test",
          cmdclass=cmdclass,
          classifiers=classifiers,
          license="GPL",
          long_description=get_readme(),
          install_requires=install_requires,
          setup_requires=setup_requires,
          )
