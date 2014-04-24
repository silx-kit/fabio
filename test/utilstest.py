# coding: utf-8
#
#    Project: Fabio tests class utilities
#             http://www.edna-site.org
#
#    File: "$Id:$"
#
#    Copyright (C) 2010 European Synchrotron Radiation Facility
#                       Grenoble, France
#
#    Principal authors: Jérôme KIEFFER (jerome.kieffer@esrf.fr)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Lesser GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "LGPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import os, imp, sys, subprocess, threading
import distutils.util
import logging
import bz2
import gzip
if sys.version_info >= (3, 0):
    import urllib as urllib2
else:
    import urllib2

logger = logging.getLogger("utilstest")

class UtilsTest(object):
    """
    Static class providing useful stuff for preparing tests.
    """
    timeout = 60        #timeout in seconds for downloading images
    url_base = "http://downloads.sourceforge.net/fable"
    test_home = os.path.dirname(os.path.abspath(__file__))
    name = "fabio"
    image_home = os.path.join(test_home, "testimages")
    if not os.path.isdir(image_home):
        os.makedirs(image_home)
    platform = distutils.util.get_platform()
    architecture = "lib.%s-%i.%i" % (platform,
                                    sys.version_info[0], sys.version_info[1])
    if os.environ.get("BUILDPYTHONPATH"):
        fabio_build_home = os.path.abspath(os.environ.get("BUILDPYTHONPATH", ""))
    else:
        fabio_build_home = os.path.join(os.path.dirname(test_home),
                                                    "build", architecture)
#    fabio_build_home = os.path.join(fabio_home, "build", architecture)
    print("Fabio Home is: %s" % fabio_build_home)
    if "fabio" in sys.modules:
        logger.info("Fabio module was already loaded from  %s" % sys.modules["fabio"])
        fabio = None
        sys.modules.pop("fabio")
    if not os.path.isdir(fabio_build_home):
        logger.warning("Building Fabio to %s" % fabio_build_home)
        p = subprocess.Popen([sys.executable, "setup.py", "build"],
                         shell=False, cwd=os.path.dirname(test_home))
        logger.info("subprocess ended with rc= %s" % p.wait())

    fabio = imp.load_module(*((name,) + imp.find_module(name, [fabio_build_home])))
    sys.modules[name] = fabio
    print("pyFAI loaded from %s" % fabio.__file__)

    @classmethod
    def forceBuild(cls):
        """
        force the recompilation of Fabio
        """
        logger.info("Building Fabio to %s" % cls.fabio_build_home)
        p = subprocess.Popen([sys.executable, "setup.py", "build"],
                         shell=False, cwd=os.path.dirname(cls.test_home))
        logger.info("subprocess ended with rc= %s" % p.wait())
        fabio = imp.load_module(*((cls.name,) + imp.find_module(cls.name, [cls.fabio_build_home])))
        sys.modules[cls.name] = fabio
        logger.info("fabio loaded from %s" % fabio.__file__)



    @classmethod
    def timeoutDuringDownload(cls):
        """
        Function called after a timeout in the download part ... 
        just raise an Exception.
        """
        raise RuntimeError("""Could not automatically download test images!
If you are behind a firewall, please set the environment variable http_proxy.
Otherwise please try to download the images manually from
""" + cls.url_base)


    @classmethod
    def getimage(cls, imagename):
        """
        Downloads the requested image
        @return:  path of the image, locally
        """
        logger.info("UtilsTest.getimage('%s')" % imagename)
        fullimagename = os.path.join(cls.image_home, imagename)
        if not os.path.isfile(fullimagename):
            logger.info("Trying to download image %s, timeout set to %ss"
                          % (imagename, cls.timeout))
            if "http_proxy" in os.environ:
                dictProxies = {'http': os.environ["http_proxy"]}
                proxy_handler = urllib2.ProxyHandler(dictProxies)
                opener = urllib2.build_opener(proxy_handler).open
            else:
                opener = urllib2.urlopen

#           Nota: since python2.6 there is a timeout in the urllib2
            timer = threading.Timer(cls.timeout + 1, cls.timeoutDuringDownload)
            timer.start()
            logger.info("wget %s/%s" % (cls.url_base, imagename))
            if sys.version > (2, 6):
                data = opener("%s/%s" % (cls.url_base, imagename),
                              data=None, timeout=cls.timeout).read()
            else:
                data = opener("%s/%s" % (cls.url_base, imagename),
                              data=None).read()
            timer.cancel()
            logger.info("Image %s successfully downloaded." % imagename)

            try:
                open(fullimagename, "wb").write(data)
            except IOError:
                raise IOError("unable to write downloaded \
                    data to disk at %s" % cls.image_home)

            if not os.path.isfile(fullimagename):
                raise RuntimeError("Could not automatically \
                download test images %s!\n \ If you are behind a firewall, \
                please set the environment variable http_proxy.\n \
                Otherwise please try to download the images manually from \n \
                %s" % (cls.url_base, imagename))
        else:
            data = open(fullimagename).read()
        fullimagename_bz2 = os.path.splitext(fullimagename)[0]+".bz2"
        fullimagename_gz = os.path.splitext(fullimagename)[0]+".gz"
        fullimagename_raw = os.path.splitext(fullimagename)[0]
        if not os.path.isfile(fullimagename_raw) or\
           not os.path.isfile(fullimagename_gz) or\
           not os.path.isfile(fullimagename_bz2):
            if imagename.endswith(".bz2"):
                decompressed = bz2.decompress(data)
                basename = fullimagename[:-4]
            elif imagename.endswith(".gz"):
                decompressed = gzip.open(fullimagename).read()
                basename = fullimagename[:-3]
            else:
                decompressed = data
                basename = fullimagename

            gzipname = basename + ".gz"
            bzip2name = basename + ".bz2"

            if basename != fullimagename:
                try:
                    open(basename, "wb").write(decompressed)
                except IOError:
                    raise IOError("unable to write decompressed \
                    data to disk at %s" % cls.image_home)
            if gzipname != fullimagename:
                try:
                    gzip.open(gzipname, "wb").write(decompressed)
                except IOError:
                    raise IOError("unable to write gzipped \
                    data to disk at %s" % cls.image_home)
            if bzip2name != fullimagename:
                try:
                    bz2.BZ2File(bzip2name, "wb").write(decompressed)
                except IOError:
                    raise IOError("unable to write bzipped2 \
                    data to disk at %s" % cls.image_home)
        return fullimagename

    @staticmethod
    def recursive_delete(strDirname):
        """
        Delete everything reachable from the directory named in "top",
        assuming there are no symbolic links.
        CAUTION:  This is dangerous!  For example, if top == '/', it
        could delete all your disk files.
        @param strDirname: top directory to delete
        @type strDirname: string 
        """
        for root, dirs, files in os.walk(strDirname, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(strDirname)
