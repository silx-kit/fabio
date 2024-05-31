# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction,
#  including without limitation the rights to use, copy, modify, merge,
#  publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.

#
"""General purpose utilities functions for fabio

"""

__author__ = "Jérôme Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "03/11/2020"
__status__ = "stable"
__docformat__ = 'restructuredtext'

import re
import os
import logging
import sys
import json

logger = logging.getLogger(__name__)

from collections import OrderedDict as _OrderedDict

try:
    import pathlib
except ImportError:
    try:
        import pathlib2 as pathlib
    except ImportError:
        pathlib = None

StringTypes = (str, bytes)
from io import FileIO, BytesIO as _BytesIO


def to_str(s):
    return str(s, "ASCII")


PathTypes = StringTypes
if pathlib is not None:
    PathTypes += (pathlib.PurePath,)

from .compression import bz2, gzip, COMPRESSORS
import traceback
from math import ceil

import threading

dictAscii = {None: [chr(i) for i in range(32, 127)]}


def pad(mystr, pattern=" ", size=80):
    """
    Performs the padding of the string to the right size with the right pattern

    :param mystr: input string
    :param pattern: the filling pattern
    :param size: the size of the block
    :return: the padded string to a multiple of size
    """
    size = int(size)
    padded_size = (len(mystr) + size - 1) // size * size
    if len(pattern) == 1:
        return mystr.ljust(padded_size, pattern)
    else:
        return (mystr + pattern * int(ceil(float(padded_size - len(mystr)) / len(pattern))))[:padded_size]


def getnum(name):
    """
    # try to figure out a file number
    # guess it starts at the back
    """
    _stem, num, _post_num = numstem(name)
    try:
        return int(num)
    except ValueError:
        return None


COMPRESSED_EXTENSIONS = set(["gz", "bz2"])
"""Set of compressed file extensions provided by Fabio"""


class FilenameObject(object):
    """
    The 'meaning' of a filename ...
    """

    def __init__(self, stem=None,
                 num=None,
                 directory=None,
                 format_=None,
                 extension=None,
                 postnum=None,
                 digits=4,
                 filename=None):
        """
        This class can either be instanciated by a set of parameters like  directory, prefix, num, extension, ...

        :param stem: the stem is a kind of prefix (str)
        :param num: image number in the serie (int)
        :param directory: name of the directory (str)
        :param format_: ??
        :param extension:
        :param postnum:
        :param digits: Number of digits used to print num

        Alternative constructor:

        :param filename: fullpath of an image file to be deconstructed into directory, prefix, num, extension, ...

        """
        self.stem = stem
        self.num = num
        self.format = format_
        self.extension = extension
        self.digits = digits
        self.postnum = postnum
        self.directory = directory
        self.compressed = None
        if filename is not None:
            self.deconstruct_filename(filename)

    def str(self):
        """ Return a string representation """
        fmt = "stem %s, num %s format %s extension %s " + \
              "postnum = %s digits %s dir %s"
        attrs = [self.stem,
                 self.num,
                 self.format,
                 self.extension,
                 self.postnum,
                 self.digits,
                 self.directory]
        return fmt % tuple([str(x) for x in attrs])

    __repr__ = str

    def tostring(self):
        """
        convert yourself to a string
        """
        name = self.stem
        if self.digits is not None and self.num is not None:
            fmt = "%0" + str(self.digits) + "d"
            name += fmt % self.num
        if self.postnum is not None:
            name += self.postnum
        if self.extension is not None:
            name += self.extension
        if self.directory is not None:
            name = os.path.join(self.directory, name)
        return name

    def deconstruct_filename(self, filename):
        """
        Break up a filename to get image type and number
        """
        from . import fabioformats
        direc, name = os.path.split(filename)
        direc = direc or None
        parts = name.split(".")
        compressed = False
        stem = parts[0]
        extn = ""
        postnum = ""
        ndigit = 4
        num = None
        typ = None
        if parts[-1].lower() in COMPRESSED_EXTENSIONS:
            extn = "." + parts[-1]
            parts = parts[:-1]
            compressed = True
        codec_classes = fabioformats.get_classes_from_extension(parts[-1])
        if len(codec_classes) > 0:
            typ = []
            for codec in codec_classes:
                name = codec.codec_name()
                if name.endswith("image"):
                    name = name[:-5]
                typ.append(name)
            extn = "." + parts[-1] + extn
            try:
                stem, numstring, postnum = numstem(".".join(parts[:-1]))
                num = int(numstring)
                ndigit = len(numstring)
            except Exception as err:
                # There is no number - hence make num be None, not 0
                logger.debug("l242: %s" % err)
                num = None
                stem = "".join(parts[:-1])
        else:
            # Probably two type left
            if len(parts) == 1:
                # Probably GE format stem_numb
                parts2 = parts[0].split("_")
                if parts2[-1].isdigit():
                    num = int(parts2[-1])
                    ndigit = len(parts2[-1])
                    typ = ['GE']
                    stem = "_".join(parts2[:-1]) + "_"
            else:
                try:
                    num = int(parts[-1])
                    ndigit = len(parts[-1])
                    typ = ['bruker']
                    stem = ".".join(parts[:-1]) + "."
                except Exception as err:
                    logger.debug("l262: %s" % err)
                    typ = None
                    extn = "." + parts[-1] + extn
                    numstring = ""
                    try:
                        stem, numstring, postnum = numstem(".".join(parts[:-1]))
                    except Exception as err:
                        logger.debug("l269: %s" % err)
                        raise
                    if numstring.isdigit():
                        num = int(numstring)
                        ndigit = len(numstring)
                #            raise Exception("Cannot decode "+filename)

        self.codec_classes = codec_classes
        self.stem = stem
        self.num = num
        self.directory = direc
        self.format = typ
        self.extension = extn
        self.postnum = postnum
        self.digits = ndigit
        self.compressed = compressed


def numstem(name):
    """ cant see how to do without reversing strings
    Match 1 or more digits going backwards from the end of the string
    """
    reg = re.compile(r"^(.*?)(-?[0-9]{0,9})(\D*)$")
    # reg = re.compile("""(\D*)(\d\d*)(\w*)""")
    try:
        res = reg.match(name).groups()
        # res = reg.match(name[::-1]).groups()
        # return [ r[::-1] for r in res[::-1]]
        if len(res[0]) == len(res[1]) == 0:  # Hack for file without number
            return [res[2], '', '']
        return [r for r in res]
    except AttributeError:  # no digits found
        return [name, "", ""]


# @deprecated
def deconstruct_filename(filename):
    """
    Function for backward compatibility.
    Deprecated
    """
    return FilenameObject(filename=filename)


def construct_filename(filename, frame=None):
    "Try to construct the filename for a given frame"
    fobj = FilenameObject(filename=filename)
    if frame is not None:
        fobj.num = frame
    return fobj.tostring()


def next_filename(name, padding=True):
    """ increment number """
    fobj = FilenameObject(filename=name)
    fobj.num += 1
    if not padding:
        fobj.digits = 0
    return fobj.tostring()


def previous_filename(name, padding=True):
    """ decrement number """
    fobj = FilenameObject(filename=name)
    fobj.num -= 1
    if not padding:
        fobj.digits = 0
    return fobj.tostring()


def jump_filename(name, num, padding=True):
    """ jump to number """
    fobj = FilenameObject(filename=name)
    fobj.num = num
    if not padding:
        fobj.digits = 0
    return fobj.tostring()


def extract_filenumber(name):
    """ extract file number """
    fobj = FilenameObject(filename=name)
    return fobj.num


def isAscii(name, listExcluded=None):
    """
    :param name: string to check
    :param listExcluded: list of char or string excluded.
    :return: True of False whether  name is pure ascii or not
    """
    isascii = None
    try:
        name.encode("ASCII")
    except UnicodeDecodeError:
        isascii = False
    else:
        if listExcluded:
            isascii = not(any(bad in name for bad in listExcluded))
        else:
            isascii = True
    return isascii


def toAscii(name, excluded=None):
    """
    :param name: string to check
    :param excluded: tuple of char or string excluded (not list: they are mutable).
    :return: the name with all non valid char removed
    """
    if excluded not in dictAscii:
        ascii = dictAscii[None][:]
        for i in excluded:
            if i in ascii:
                ascii.remove(i)
            else:
                logger.error("toAscii: %s not in ascii table" % i)
        dictAscii[excluded] = ascii
    else:
        ascii = dictAscii[excluded]
    out = [i for i in str(name) if i in ascii]
    return "".join(out)


def nice_int(s):
    """
    Workaround that int('1.0') raises an exception

    :param s: string to be converted to integer
    """
    try:
        return int(s)
    except ValueError:
        return int(float(s))


class BytesIO(_BytesIO):
    """
    just an interface providing the name and mode property to a BytesIO

    BugFix for MacOSX mainly
    """

    def __init__(self, data, fname=None, mode="r"):
        _BytesIO.__init__(self, data)
        if "closed" not in dir(self):
            self.closed = False
        if fname is None:
            self.name = "fabioStream"
        else:
            self.name = fname
        self.mode = mode
        self.lock = threading.Semaphore()
        self.__size = None

    def getSize(self):
        if self.__size is None:
            logger.debug("Measuring size of %s" % self.name)
            with self.lock:
                pos = self.tell()
                self.seek(0, os.SEEK_END)
                self.__size = self.tell()
                self.seek(pos)
        return self.__size

    def setSize(self, size):
        self.__size = size

    size = property(getSize, setSize)


class File(FileIO):
    """
    wrapper for "file" with locking
    """

    def __init__(self, name, mode="rb", temporary=False):
        """file(name[, mode[, buffering]]) -> file object

        Open a file.  The mode can be 'r', 'w' or 'a' for reading (default),
        writing or appending.  The file will be created if it doesn't exist
        when opened for writing or appending; it will be truncated when
        opened for writing.  Add a 'b' to the mode for binary files.
        Add a '+' to the mode to allow simultaneous reading and writing.
        If the buffering argument is given, 0 means unbuffered, 1 means line
        buffered, and larger numbers specify the buffer size.  The preferred way
        to open a file is with the builtin open() function.
        Add a 'U' to mode to open the file for input with universal newline
        support.  Any line ending in the input file will be seen as a '\n'
        in Python.  Also, a file so opened gains the attribute 'newlines';
        the value for this attribute is one of None (no newline read yet),
        '\r', '\n', '\r\n' or a tuple containing all the newline types seen.

        'U' cannot be combined with 'w' or '+' mode.

        :param temporary: if True, destroy file at close.
        """
        FileIO.__init__(self, name, mode)
        self.lock = threading.Semaphore()
        self.__size = None
        self.__temporary = temporary

    def __del__(self):
        """Explicit close at deletion
        """
        if hasattr(self, "closed") and not self.closed:
            self.close()

    def close(self):
        name = self.name
        FileIO.close(self)
        if self.__temporary:
            try:
                os.unlink(name)
            except Exception as err:
                logger.error("Unable to remove %s: %s" % (name, err))
                raise(err)

    def getSize(self):
        if self.__size is None:
            logger.debug("Measuring size of %s" % self.name)
            with self.lock:
                pos = self.tell()
                self.seek(0, os.SEEK_END)
                self.__size = self.tell()
                self.seek(pos)
        return self.__size

    def setSize(self, size):
        self.__size = size

    size = property(getSize, setSize)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        """
        Close the file.
        """
        return FileIO.close(self)

    def write(self, readablebuffer):
        nbytes = len(readablebuffer)
        nwritten = super().write(readablebuffer)
        while nwritten < nbytes:
            # One write operation is limited to e.g. 2 GB
            nextra = super().write(readablebuffer[nwritten:])
            if nextra:
                nwritten += nextra
            else:
                break
        return nwritten

    def read(self, size = -1):
        buffer = super().read(size)
        size -= len(buffer)
        while size > 0:
            # One read operation is limited to e.g. 2 GB
            extra = super().read(size)
            nextra = len(extra)
            if nextra:
                size -= nextra
                buffer += extra
            else:
                break
        return buffer


class UnknownCompressedFile(File):
    """
    wrapper for "File" with locking
    """

    def __init__(self, name, mode="rb", buffering=0):
        logger.warning("No decompressor found for this type of file (are gzip anf bz2 installed ???")
        File.__init__(self, name, mode, buffering)

    def __del__(self):
        """Explicit close at deletion
        """
        if hasattr(self, "closed") and not self.closed:
            self.close()


if gzip is None:
    GzipFile = UnknownCompressedFile
else:

    class GzipFile(gzip.GzipFile):
        """
        Just a wrapper for gzip.GzipFile providing the correct seek capabilities for python 2.5
        """

        def __init__(self, filename=None, mode=None, compresslevel=9, fileobj=None):
            """
            Wrapper with locking for constructor for the GzipFile class.

            At least one of fileobj and filename must be given a
            non-trivial value.

            The new class instance is based on fileobj, which can be a regular
            file, a StringIO object, or any other object which simulates a file.
            It defaults to None, in which case filename is opened to provide
            a file object.

            When fileobj is not None, the filename argument is only used to be
            included in the gzip file header, which may includes the original
            filename of the uncompressed file.  It defaults to the filename of
            fileobj, if discernible; otherwise, it defaults to the empty string,
            and in this case the original filename is not included in the header.

            The mode argument can be any of 'r', 'rb', 'a', 'ab', 'w', or 'wb',
            depending on whether the file will be read or written.  The default
            is the mode of fileobj if discernible; otherwise, the default is 'rb'.
            Be aware that only the 'rb', 'ab', and 'wb' values should be used
            for cross-platform portability.

            The compresslevel argument is an integer from 1 to 9 controlling the
            level of compression; 1 is fastest and produces the least compression,
            and 9 is slowest and produces the most compression.  The default is 9.
            """
            gzip.GzipFile.__init__(self, filename, mode, compresslevel, fileobj)
            self.lock = threading.Semaphore()
            self.__size = None

        def __del__(self):
            """Explicit close at deletion
            """
            if hasattr(self, "closed") and not self.closed:
                self.close()

        def __repr__(self):
            return "fabio." + gzip.GzipFile.__repr__(self)

        def measure_size(self):
            if self.mode == gzip.WRITE:
                return self.size
            if self.__size is None:
                with self.lock:
                    if self.__size is None:
                        if "offset" in dir(self):
                            pos = self.offset
                        elif "tell" in dir(self):
                            pos = self.tell()
                        end_pos = len(gzip.GzipFile.read(self)) + pos
                        self.seek(pos)
                        logger.debug("Measuring size of %s: %s @ %s == %s" % (self.name, end_pos, pos, pos))
                        self.__size = end_pos
            return self.__size

    def __enter__(self):
        return self

    def __exit__(self, *args):
        """
        Close the file.
        """
        gzip.GzipFile.close(self)

if bz2 is None:
    BZ2File = UnknownCompressedFile
else:

    class BZ2File(bz2.BZ2File):
        "Wrapper with lock"

        def __init__(self, name, mode='r', compresslevel=9):
            """
            BZ2File(name [, mode='r', compresslevel=9]) -> file object

            Open a bz2 file. The mode can be 'r' or 'w', for reading (default) or
            writing. When opened for writing, the file will be created if it doesn't
            exist, and truncated otherwise.

            If compresslevel is given, must be a number between 1 and 9.

            Add a 'U' to mode to open the file for input with universal newline
            support. Any line ending in the input file will be seen as a '\n' in
            Python. Also, a file so opened gains the attribute 'newlines'; the value
            for this attribute is one of None (no newline read yet), '\r', '\n',
            '\r\n' or a tuple containing all the newline types seen. Universal
            newlines are available only when reading.
            """
            bz2.BZ2File.__init__(self, name, mode, compresslevel=compresslevel)
            self.lock = threading.Semaphore()
            self.__size = None

        def __del__(self):
            """Explicit close at deletion
            """
            if hasattr(self, "closed") and not self.closed:
                self.close()

        def getSize(self):
            if self.__size is None:
                logger.debug("Measuring size of %s" % self.name)
                with self.lock:
                    pos = self.tell()
                    _ = self.read()
                    self.__size = self.tell()
                    self.seek(pos)
            return self.__size

        def setSize(self, value):
            self.__size = value

        size = property(getSize, setSize)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            """
            Close the file at exit
            """
            bz2.BZ2File.close(self)


class NotGoodReader(RuntimeError):
    """The reader used is probably not the good one
    """
    pass


class DebugSemaphore(threading.Semaphore):
    """
    threading.Semaphore like class with helper for fighting dead-locks
    """
    write_lock = threading.Semaphore()
    blocked = []

    def __init__(self, *arg, **kwarg):
        threading.Semaphore.__init__(self, *arg, **kwarg)

    def acquire(self, *arg, **kwarg):
        if self._Semaphore__value == 0:
            with self.write_lock:
                self.blocked.append(id(self))
                sys.stderr.write(os.linesep.join(["Blocking sem %s" % id(self)] +
                                 traceback.format_stack()[:-1] + [""]))

        return threading.Semaphore.acquire(self, *arg, **kwarg)

    def release(self, *arg, **kwarg):
        with self.write_lock:
            uid = id(self)
            if uid in self.blocked:
                self.blocked.remove(uid)
                sys.stderr.write("Released sem %s %s" % (uid, os.linesep))
        threading.Semaphore.release(self, *arg, **kwarg)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *arg, **kwarg):
        self.release()


def exists(path):
    """Test whether a path exists.

    Replaces os.path.exists and handles in addition "::" based URI as defined in
    http://odo.pydata.org/en/latest/uri.html#separating-parts-with

    :param path: string
    :return: boolean
    """
    return os.path.exists(path.split("::")[0])


class OrderedDict(_OrderedDict):
    """Ordered dictionary with pretty print"""

    def __repr__(self):
        try:
            res = json.dumps(self, indent=2)
        except Exception as err:
            logger.warning("Header is not JSON-serializable: %s", err)
            tmp = _OrderedDict()
            for key, value in self.items():
                tmp[str(key)] = str(value)
            res = json.dumps(tmp, indent=2)
        return res


AVAILABLE_COMPRESSED_EXTENSIONS = set([])
"""Set of available compressed file extensions. Do not contains extensions for
uninstalled optional dependancies."""
if GzipFile != UnknownCompressedFile:
    AVAILABLE_COMPRESSED_EXTENSIONS.add("gz")
if BZ2File != UnknownCompressedFile:
    AVAILABLE_COMPRESSED_EXTENSIONS.add("bz2")
