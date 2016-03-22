#!/usr/bin/env python
# coding: utf-8
#
#    Project: FabIO tests class utilities
#
#    Copyright (C) 2010-2016 European Synchrotron Radiation Facility
#                       Grenoble, France
#
#    Principal authors: Jérôme KIEFFER (jerome.kieffer@esrf.fr)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
from __future__ import print_function, division, absolute_import, with_statement

__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "22/03/2016"

PACKAGE = "fabio"
DATA_KEY = "FABIO_DATA"

import os
import imp
import sys
import getpass
import subprocess
import threading
import distutils.util
import logging
import bz2
import gzip
import json
import tempfile


try:  # Python3
    from urllib.request import urlopen, ProxyHandler, build_opener
except ImportError:  # Python2
    from urllib2 import urlopen, ProxyHandler, build_opener
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("%s.utilstest" % PACKAGE)

TEST_HOME = os.path.dirname(os.path.abspath(__file__))


class UtilsTest(object):
    """
    Static class providing useful stuff for preparing tests.
    """
    options = None
    timeout = 60  # timeout in seconds for downloading images
    # url_base = "http://downloads.sourceforge.net/fable"
    url_base = "http://www.edna-site.org/pub/fabio/testimages"
    sem = threading.Semaphore()
    recompiled = False
    reloaded = False
    name = PACKAGE
    try:
        fabio = __import__("%s.directories" % name)
        image_home = fabio.directories.testimages
    except Exception as err:
        logger.warning("in loading directories %s", err)
        image_home = None
    else:
        image_home = fabio.directories.testimages
    if image_home is None:
        image_home = os.path.join(tempfile.gettempdir(), "%s_testimages_%s" % (name, getpass.getuser()))
        if not os.path.exists(image_home):
            os.makedirs(image_home)
    testimages = os.path.join(image_home, "all_testimages.json")
    if os.path.exists(testimages):
        with open(testimages) as f:
            ALL_DOWNLOADED_FILES = set(json.load(f))
    else:
        ALL_DOWNLOADED_FILES = set()
    tempdir = tempfile.mkdtemp("_" + getpass.getuser(), name + "_")

    @classmethod
    def deep_reload(cls):
        cls.fabio = __import__(cls.name)
        return cls.fabio

    @classmethod
    def forceBuild(cls, remove_first=True):
        """
        Force the recompilation of FabIO

        Nonesense, kept for legacy reasons
        """
        return

    @classmethod
    def timeoutDuringDownload(cls, imagename=None):
            """
            Function called after a timeout in the download part ...
            just raise an Exception.
            """
            if imagename is None:
                imagename = "2252/testimages.tar.bz2 unzip it "
            raise RuntimeError("Could not automatically \
                download test images!\n \ If you are behind a firewall, \
                please set both environment variable http_proxy and https_proxy.\
                This even works under windows ! \n \
                Otherwise please try to download the images manually from \n %s/%s and put it in in test/testimages." % (cls.url_base, imagename))

    @classmethod
    def getimage(cls, imagename):
        """
        Downloads the requested image from Forge.EPN-campus.eu

        @param: name of the image.
        For the RedMine forge, the filename contains a directory name that is removed
        @return: full path of the locally saved file
        """
        if imagename not in cls.ALL_DOWNLOADED_FILES:
            cls.ALL_DOWNLOADED_FILES.add(imagename)
            image_list = list(cls.ALL_DOWNLOADED_FILES)
            image_list.sort()
            try:
                with open(cls.testimages, "w") as fp:
                    json.dump(image_list, fp, indent=4)
            except IOError:
                logger.debug("Unable to save JSON list")
        baseimage = os.path.basename(imagename)
        logger.info("UtilsTest.getimage('%s')" % baseimage)
        if not os.path.exists(cls.image_home):
            os.makedirs(cls.image_home)
        fullimagename = os.path.abspath(os.path.join(cls.image_home, baseimage))
        if os.path.exists(fullimagename):
            return fullimagename

        if baseimage.endswith(".bz2"):
            bzip2name = baseimage
            basename = baseimage[:-4]
            gzipname = basename + ".gz"
        elif baseimage.endswith(".gz"):
            gzipname = baseimage
            basename = baseimage[:-3]
            bzip2name = basename + ".bz2"
        else:
            basename = baseimage
            gzipname = baseimage + "gz2"
            bzip2name = basename + ".bz2"

        fullimagename_gz = os.path.abspath(os.path.join(cls.image_home, gzipname))
        fullimagename_raw = os.path.abspath(os.path.join(cls.image_home, basename))
        fullimagename_bz2 = os.path.abspath(os.path.join(cls.image_home, bzip2name))

        data = None

        if not os.path.isfile(fullimagename_bz2):
            logger.info("Trying to download image %s, timeout set to %ss",
                        bzip2name, cls.timeout)
            dictProxies = {}
            if "http_proxy" in os.environ:
                dictProxies['http'] = os.environ["http_proxy"]
                dictProxies['https'] = os.environ["http_proxy"]
            if "https_proxy" in os.environ:
                dictProxies['https'] = os.environ["https_proxy"]
            if dictProxies:
                proxy_handler = ProxyHandler(dictProxies)
                opener = build_opener(proxy_handler).open
            else:
                opener = urlopen

            logger.info("wget %s/%s" % (cls.url_base, imagename))
            data = opener("%s/%s" % (cls.url_base, imagename),
                          data=None, timeout=cls.timeout).read()
            logger.info("Image %s successfully downloaded." % baseimage)

            try:
                with open(fullimagename_bz2, "wb") as outfile:
                    outfile.write(data)
            except IOError:
                raise IOError("unable to write downloaded \
                    data to disk at %s" % cls.image_home)

            if not os.path.isfile(fullimagename_bz2):
                raise RuntimeError("Could not automatically \
                download test images %s!\n \ If you are behind a firewall, \
                please set the environment variable http_proxy.\n \
                Otherwise please try to download the images manually from \n \
                %s" % (cls.url_base, imagename))
        if not os.path.isfile(fullimagename_raw) or\
           not os.path.isfile(fullimagename_gz):

            if data is None:
                data = open(fullimagename_bz2, "rb").read()
            decompressed = bz2.decompress(data)

            if not os.path.exists(fullimagename_raw):
                try:
                    open(fullimagename_raw, "wb").write(decompressed)
                except IOError:
                    raise IOError("unable to write decompressed \
                    data to disk at %s" % cls.image_home)
            if not os.path.exists(fullimagename_gz):
                try:
                    gzip.open(fullimagename_gz, "wb").write(decompressed)
                except IOError:
                    raise IOError("unable to write gzipped \
                    data to disk at %s" % cls.image_home)
        return fullimagename

    @classmethod
    def download_images(cls, imgs=None):
        """
        Download all images needed for the test/benchmarks

        @param imgs: list of files to download
        """
        if not imgs:
            imgs = cls.ALL_DOWNLOADED_FILES
        for fn in imgs:
            print("Downloading from internet: %s" % fn)
            if fn[-4:] != ".bz2":
                if fn[-3:] == ".gz":
                    fn = fn[:-2] + "bz2"
                else:
                    fn = fn + ".bz2"
                print("  actually " + fn)
            cls.getimage(fn)

    @classmethod
    def get_logger(cls, filename=__file__):
        """
        small helper function that initialized the logger and returns it
        """
        dirname, basename = os.path.split(os.path.abspath(filename))
        basename = os.path.splitext(basename)[0]
        level = logging.root.level
        mylogger = logging.getLogger(basename)
        logger.setLevel(level)
        mylogger.setLevel(level)
        mylogger.debug("tests loaded from file: %s" % basename)
        return mylogger


def recursive_delete(dirname):
    """
    Delete everything reachable from the directory named in "top",
    assuming there are no symbolic links.
    CAUTION:  This is dangerous!  For example, if top == '/', it
    could delete all your disk files.

    @param dirname: top directory to delete
    @type dirname: string
    """
    if not os.path.isdir(dirname):
        return
    for root, dirs, files in os.walk(dirname, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(dirname)
