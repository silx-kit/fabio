#!/usr/bin/env python

"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

         and Jon Wright, Jerome Kieffer: ESRF

"""
from __future__ import with_statement
import os, types, logging, sys, tempfile
logger = logging.getLogger("fabioimage")
import numpy
try:
    import Image
except ImportError:
    logger.warning("PIL is not installed ... trying to do without")
    Image = None
import fabioutils, converters


class fabioimage(object):
    """
    A common object for images in fable
    Contains a numpy array (.data) and dict of meta data (.header)
    """

    _need_a_seek_to_read = False
    _need_a_real_file = False

    def __init__(self, data=None , header=None):
        """
        Set up initial values
        """
        self._classname = None
        if type(data) in types.StringTypes:
            raise Exception("fabioimage.__init__ bad argument - " + \
                            "data should be numpy array")
        self.data = self.checkData(data)
        self.pilimage = None
        if header is None:
            self.header = {}
        else:
            self.header = self.checkHeader(header)
        self.header_keys = self.header.keys() # holds key ordering
        if self.data is not None:
            self.dim2, self.dim1 = self.data.shape
        else:
            self.dim1 = self.dim2 = 0
        self.bytecode = None     # numpy typecode
        self.bpp = 2             # bytes per pixel
        # cache for image statistics
        self.mean = self.maxval = self.stddev = self.minval = None
        # Cache roi
        self.roi = None
        self.area_sum = None
        self.slice = None
        # New for multiframe files
        self.nframes = 1
        self.currentframe = 0
        self.filename = None
        self.filenumber = None

    @staticmethod
    def checkHeader(header=None):
        """
        Empty for fabioimage but may be populated by others classes
        """
        if header is None:
            return {}
        else:
            return header

    @staticmethod
    def checkData(data=None):
        """
        Empty for fabioimage but may be populated by others classes, especially for format accepting only integers
        """
        return data

    def getclassname(self):
        """
        Retrieves the name of the class
        @return: the name of the class
        """
        if self._classname is None:
            self._classname = str(self.__class__).replace("<class '", "").replace("'>", "").split(".")[-1]
        return self._classname
    classname = property(getclassname)

    def getframe(self, num):
        """ returns the file numbered 'num' in the series as a fabioimage """
        if self.nframes == 1:
            # single image per file
            import openimage
            return openimage.openimage(
                fabioutils.jump_filename(self.filename, num))
        raise Exception("getframe out of range")

    def previous(self):
        """ returns the previous file in the series as a fabioimage """
        import openimage
        return openimage.openimage(
            fabioutils.previous_filename(self.filename))

    def next(self):
        """ returns the next file in the series as a fabioimage """
        import openimage
        return openimage.openimage(
            fabioutils.next_filename(self.filename))

    def toPIL16(self, filename=None):
        """
        Convert to Python Imaging Library 16 bit greyscale image

        FIXME - this should be handled by the libraries now
        """
        if not Image:
            raise RuntimeError("PIL is not installed !!! ")
        if filename:
            self.read(filename)
        if self.pilimage is not None:
            return self.pilimage
        # mode map
        size = self.data.shape[:2][::-1]
        typmap = {
            'float32' : "F"     ,
            'int32'   : "F;32S" ,
            'uint32'  : "F;32"  ,
            'int16'   : "F;16S" ,
            'uint16'  : "F;16"  ,
            'int8'    : "F;8S"  ,
            'uint8'   : "F;8"  }
        if typmap.has_key(self.data.dtype.name):
            mode2 = typmap[ self.data.dtype.name ]
            mode1 = mode2[0]
        else:
            raise Exception("Unknown numpy type " + str(self.data.dtype.type))
        #
        # hack for byteswapping for PIL in MacOS
        testval = numpy.array((1, 0), numpy.uint8).view(numpy.uint16)[0]
        if  testval == 1:
            dats = self.data.tostring()
        elif testval == 256:
            dats = self.data.byteswap().tostring()
        else:
            raise Exception("Endian unknown in fabioimage.toPIL16")

        self.pilimage = Image.frombuffer(mode1,
                                         size,
                                         dats,
                                         "raw",
                                         mode2,
                                         0,
                                         1)

        return self.pilimage

    def getheader(self):
        """ returns self.header """
        return self.header

    def getmax(self):
        """ Find max value in self.data, caching for the future """
        if self.maxval is None:
            self.maxval = self.data.max()
        return self.maxval

    def getmin(self):
        """ Find min value in self.data, caching for the future """
        if self.minval is None:
            self.minval = self.data.min()
        return self.minval

    def make_slice(self, coords):
        """
        Convert a len(4) set of coords into a len(2)
        tuple (pair) of slice objects
        the latter are immutable, meaning the roi can be cached
        """
        assert len(coords) == 4
        if len(coords) == 4:
            # fabian edfimage preference
            if coords[0] > coords[2]:
                coords[0:3:2] = [coords[2], coords[0]]
            if coords[1] > coords[3]:
                coords[1:4:2] = [coords[3], coords[1]]
            #in fabian: normally coordinates are given as (x,y) whereas
            # a matrix is given as row,col
            # also the (for whichever reason) the image is flipped upside
            # down wrt to the matrix hence these tranformations
            fixme = (self.dim2 - coords[3] - 1,
                     coords[0] ,
                     self.dim2 - coords[1] - 1,
                     coords[2])
        return (slice(int(fixme[0]), int(fixme[2]) + 1) ,
                 slice(int(fixme[1]), int(fixme[3]) + 1))


    def integrate_area(self, coords):
        """
        Sums up a region of interest
        if len(coords) == 4 -> convert coords to slices
        if len(coords) == 2 -> use as slices
        floor -> ? removed as unused in the function.
        """
        if self.data == None:
            # This should return NAN, not zero ?
            return 0
        if len(coords) == 4:
            sli = self.make_slice(coords)
        elif len(coords) == 2 and isinstance(coords[0], slice) and \
                                  isinstance(coords[1], slice):
            sli = coords

        if sli == self.slice and self.area_sum is not None:
            pass
        elif sli == self.slice and self.roi is not None:
            self.area_sum = self.roi.sum(dtype=numpy.float)
        else:
            self.slice = sli
            self.roi = self.data[ self.slice ]
            self.area_sum = self.roi.sum(dtype=numpy.float)
        return self.area_sum

    def getmean(self):
        """ return the mean """
        if self.mean is None:
            self.mean = self.data.mean(dtype=numpy.double)
        return self.mean

    def getstddev(self):
        """ return the standard deviation """
        if self.stddev == None:
            self.stddev = self.data.std(dtype=numpy.double)
        return self.stddev

    def add(self, other):
        """
        Add another Image - warning, does not clip to 16 bit images by default
        """
        if not hasattr(other, 'data'):
            logger.warning('edfimage.add() called with something that ' + \
                'does not have a data field')
        assert self.data.shape == other.data.shape , \
                  'incompatible images - Do they have the same size?'
        self.data = self.data + other.data
        self.resetvals()


    def resetvals(self):
        """ Reset cache - call on changing data """
        self.mean = self.stddev = self.maxval = self.minval = None
        self.roi = self.slice = self.area_sum = None

    def rebin(self, x_rebin_fact, y_rebin_fact, keep_I=True):
        """
        Rebin the data and adjust dims
        @param x_rebin_fact: x binning factor
        @param y_rebin_fact: y binning factor
        @param keep_I: shall the signal increase ?
        @type x_rebin_fact: int
        @type y_rebin_fact: int
        @type keep_I: boolean


        """
        if self.data == None:
            raise Exception('Please read in the file you wish to rebin first')

        if (self.dim1 % x_rebin_fact != 0) or (self.dim2 % y_rebin_fact != 0):
            raise RuntimeError('image size is not divisible by rebin factor - ' + \
                  'skipping rebin')
        else:
            dataIn = self.data.astype("float64")
            shapeIn = self.data.shape
            shapeOut = (shapeIn[0] / y_rebin_fact, shapeIn[1] / x_rebin_fact)
            binsize = y_rebin_fact * x_rebin_fact
            if binsize < 50: #method faster for small binning (4x4)
                out = numpy.zeros(shapeOut, dtype="float64")
                for j in range(x_rebin_fact):
                    for i in range(y_rebin_fact):
                        out += dataIn[i::y_rebin_fact, j::x_rebin_fact]
            else: #method faster for large binning (8x8)
                temp = self.data.astype("float64")
                temp.shape = (shapeOut[0], y_rebin_fact, shapeOut[1], x_rebin_fact)
                out = temp.sum(axis=3).sum(axis=1)
        self.resetvals()
        if keep_I:
            self.data = (out / (y_rebin_fact * x_rebin_fact)).astype(self.data.dtype)
        else:
            self.data = out.astype(self.data.dtype)

        self.dim1 = self.dim1 / x_rebin_fact
        self.dim2 = self.dim2 / y_rebin_fact

        #update header
        self.update_header()

    def write(self, fname):
        """
        To be overwritten - write the file
        """
        raise Exception("Class has not implemented readheader method yet")

    def save(self, fname):
        'wrapper for write'
        self.write(fname)

    def readheader(self, filename):
        """
        Call the _readheader function...
        """
        # Override the needs asserting that all headers can be read via python modules
        save_state = self._need_a_real_file , self._need_a_seek_to_read
        self._need_a_real_file , self._need_a_seek_to_read = False, False
        fin = self._open(filename)
        self._readheader(fin)
        fin.close()
        self._need_a_real_file , self._need_a_seek_to_read = save_state

    def _readheader(self, fik_obj):
        """
        Must be overridden in classes
        """
        raise Exception("Class has not implemented _readheader method yet")

    def update_header(self , **kwds):
        """
        update the header entries
        by default pass in a dict of key, values.
        """
        self.header.update(kwds)

    def read(self, filename, frame=None):
        """
        To be overridden - fill in self.header and self.data
        """
        raise Exception("Class has not implemented read method yet")
#        return self

    def load(self, *arg, **kwarg):
        "Wrapper for read"
        return self.read(*arg, **kwarg)

    def readROI(self, filename, frame=None, coords=None):
        """
        Method reading Region of Interest.
        This implementation is the trivial one, just doing read and crop
        """
        self.read(filename, frame)
        if len(coords) == 4:
            self.slice = self.make_slice(coords)
        elif len(coords) == 2 and isinstance(coords[0], slice) and \
                                  isinstance(coords[1], slice):
            self.slice = coords
        else:
            logger.warning('readROI: Unable to understand Region Of Interest: got %s', coords)
        self.roi = self.data[ self.slice ]
        return self.roi


    def _open(self, fname, mode="rb"):
        """
        Try to handle compressed files, streams, shared memory etc
        Return an object which can be used for "read" and "write"
        ... FIXME - what about seek ?
        """
        fileObject = None
        self.filename = fname
        self.filenumber = fabioutils.extract_filenumber(fname)
        if hasattr(fname, "read") and hasattr(fname, "write"):
            # It is already something we can use
            return fname
        if isinstance(fname, (str, unicode)):
            self.header["filename"] = fname
            if os.path.splitext(fname)[1] == ".gz":
                fileObject = self._compressed_stream(fname,
                                       fabioutils.COMPRESSORS['.gz'],
                                       fabioutils.GzipFile,
                                       mode)
            elif os.path.splitext(fname)[1] == '.bz2':
                fileObject = self._compressed_stream(fname,
                                       fabioutils.COMPRESSORS['.bz2'],
                                       fabioutils.BZ2File,
                                       mode)
            #
            # Here we return the file even though it may be bzipped or gzipped
            # but named incorrectly...
            #
            # FIXME - should we fix that or complain about the daft naming?
            else:
                fileObject = fabioutils.File(fname, mode)
            if "name" not in dir(fileObject):
                fileObject.name = fname

        return fileObject

    def _compressed_stream(self,
                           fname,
                           system_uncompress,
                           python_uncompress,
                           mode='rb'):
        """
        Try to transparently handle gzip / bzip without always getting python
        performance
        """
        # assert that python modules are always OK based on performance benchmark
        # Try to fix the way we are using them?
        fobj = None
        if self._need_a_real_file and mode[0] == "r":
            fo = python_uncompress(fname, mode)
#            fobj = os.tmpfile()
            #problem when not administrator under certain flavors of windows
            tmpfd, tmpfn = tempfile.mkstemp()
            os.close(tmpfd)
            fobj = fabioutils.File(tmpfn, "w+b")
            fobj.write(fo.read())
            fo.close()
            fobj.seek(0)
        elif self._need_a_seek_to_read and mode[0] == "r":
            fo = python_uncompress(fname, mode)
            fobj = fabioutils.StringIO(fo.read(), fname, mode)
        else:
            fobj = python_uncompress(fname, mode)
        return fobj

    def convert(self, dest):
        """
        Convert a fabioimage object into another fabioimage object (with possible conversions)
        @param dest: destination type "EDF", "edfimage" or the class itself
        """
        if type(dest) in types.StringTypes:
            dest = dest.lower()
            modules = []
            for val  in fabioutils.FILETYPES.values():
                modules += [i + "image" for i in val if i not in modules]
            klass = None
            module = None
            klass_name = None
            for klass_name in modules:
                if  klass_name.startswith(dest):
                    try:
                        module = sys.modules["fabio." + klass_name]
                    except KeyError:
                        try:
                            module = __import__(klass_name)
                        except:
                            logger.error("Failed to import %s", klass_name)
                        else:
                            logger.debug("imported %simage", klass_name)
                    if module is not None:
                        break
            if module is not None:
                if hasattr(module, klass_name):
                    klass = getattr(module, klass_name)
                else:
                    logger.error("Module %s has no image class" % module)
        elif isinstance(dest, self.__class__):
            klass = dest.__class__
        elif ("__new__" in dir(dest)) and isinstance(dest(), fabioimage):
            klass = dest
        else:
            logger.warning("Unrecognized destination format: %s " % dest)
            return self
        if klass is None:
            logger.warning("Unrecognized destination format: %s " % dest)
            return self
        other = klass() #temporary instance (to be overwritten)
        other = klass(data=converters.convert_data(self.classname, other.classname, self.data),
                    header=converters.convert_header(self.classname, other.classname, self.header))
        return other

def test():
    """
    check some basic fabioimage functionality
    """
    import time
    start = time.time()

    dat = numpy.ones((1024, 1024), numpy.uint16)
    dat = (dat * 50000).astype(numpy.uint16)
    assert dat.dtype.char == numpy.ones((1), numpy.uint16).dtype.char
    hed = {"Title":"50000 everywhere"}
    obj = fabioimage(dat, hed)

    assert obj.getmax() == 50000
    assert obj.getmin() == 50000
    assert obj.getmean() == 50000 , obj.getmean()
    assert obj.getstddev() == 0.

    dat2 = numpy.zeros((1024, 1024), numpy.uint16, savespace=1)
    cord = [ 256, 256, 790, 768 ]
    slic = obj.make_slice(cord)
    dat2[slic] = dat2[slic] + 100

    obj = fabioimage(dat2, hed)

    # New object, so...
    assert obj.maxval is None
    assert obj.minval is None

    assert obj.getmax() == 100, obj.getmax()
    assert obj.getmin() == 0 , obj.getmin()
    npix = (slic[0].stop - slic[0].start) * (slic[1].stop - slic[1].start)
    obj.resetvals()
    area1 = obj.integrate_area(cord)
    obj.resetvals()
    area2 = obj.integrate_area(slic)
    assert area1 == area2
    assert obj.integrate_area(cord) == obj.integrate_area(slic)
    assert obj.integrate_area(cord) == npix * 100, obj.integrate_area(cord)


    def clean():
        """ clean up the created testfiles"""
        for name in ["testfile", "testfile.gz", "testfile.bz2"]:
            try:
                os.remove(name)
            except:
                continue


    clean()
    import gzip, bz2
    gzip.open("testfile.gz", "wb").write("{ hello }")
    fout = obj._open("testfile.gz")
    readin = fout.read()
    assert readin == "{ hello }", readin + " gzipped file"


    bz2.BZ2File("testfilebz", "wb").write("{ hello }")
    fout = obj._open("testfile.bz2")
    readin = fout.read()
    assert readin == "{ hello }", readin + " bzipped file"

    ftest = open("testfile", "wb")
    ftest.write("{ hello }")
    assert ftest == obj._open(ftest)
    ftest.close()
    fout = obj._open("testfile")
    readin = fout.read()
    assert readin == "{ hello }", readin + "plain file"
    fout.close()
    ftest.close()
    clean()

    print "Passed in", time.time() - start, "s"

if __name__ == '__main__':
    test()
