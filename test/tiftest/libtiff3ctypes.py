"""libtiff3 interface using ctypes.

from
http://starship.python.net/crew/theller/wiki/TiffWrapping
"""

import os
import sys
import ctypes
import logging     # Logging module
import platform    # Platform discovery



class Tiff3Error(Exception):
    pass

def InitUNIX(libpath="libtiff.so"):
    log=logging.getLogger("LibTiff3.Init")
    tlib=None
    if tlib==None:
        tlib=ctypes.cdll.LoadLibrary(libpath)
    return tlib

def InitWindows(libpath="libtiff3.dll"):
    log=logging.getLogger("LibTiff3.Init")
    tlib=None

    if tlib==None and libpath != None:
        try:
            tlib = ctypes.cdll.LoadLibrary(libpath)
            log.debug("loading libtiff from %s"%libpath)
        except:
            log.warning("failed to load libtiff from %s"%libpath)
            tlib=None

    if tlib == None:
        tlib=ctypes.cdll.libtiff3
        log.debug("loading system libtiff")

    return tlib


def Init():
    log=logging.getLogger("LibTiff3.Init")
    log.debug("got platform '%s'"%platform.system())
    if platform.system() == "Windows":
        return InitWindows()
    else:
        return InitUNIX()


def OpenTiff(fname, mode, tlib=None):
    """OpenTiff(fname, mode, tlib=None) -> (tiff handler, tlib handler)
    Opens up a tiff file in <mode> using a tlib library handler.
    """
    log=logging.getLogger("LibTiff3.OpenTiff")
    if tlib==None: tlib=Init()
    tif=tlib.TIFFOpen(fname,mode)
    if (tif):
       return tif, tlib
    else:
       return None, 0
    # if the tiff is bad, you won't always get the error from LibTiff, 
    # so check that the pointer to the TIFF struc isn't 0, otherwise, 
    # you'll segfault on an empty file or bad tiff on subsequent 
    # operations on the TIFF ptr




def GetTiffTags(tif, tlib):
    log=logging.getLogger("LibTiff3.GetTiffTags")
    result={}

    width = ctypes.c_int()
    tlib.TIFFGetField(tif, 256 ,ctypes.byref(width))
    width=width.value
    result["ImageWidth"]=width

    height = ctypes.c_int()
    tlib.TIFFGetField(tif, 257 ,ctypes.byref(height))
    height=height.value
    result["ImageLength"]=height

    bps= ctypes.c_short()
    tlib.TIFFGetField(tif, 258 ,ctypes.byref(bps))
    result["BitsPerSample"]=bps.value

    spp= ctypes.c_short()
    tlib.TIFFGetField(tif, 277,ctypes.byref(spp))
    result["SamplesPerPixel"]=spp.value

    comp=ctypes.c_short()
    tlib.TIFFGetField(tif, 259 ,ctypes.byref(comp))
    result["Compression"]=comp.value

    x=ctypes.c_short()
    tlib.TIFFGetField(tif, 262 ,ctypes.byref(x))
    result["PhotometricInterpretation"]=x.value

    x=ctypes.c_short()
    tlib.TIFFGetField(tif, 278  ,ctypes.byref(x))
    result["RowsPerStrip"]=x.value

    x=ctypes.c_short()
    tlib.TIFFGetField(tif, 284 ,ctypes.byref(x))
    result["PlanarConfiguration"]=x.value

    x=ctypes.c_char_p()
    tlib.TIFFGetField(tif, 315 ,ctypes.byref(x))
    result["Artist"]=x.value

    x=ctypes.c_char_p()
    tlib.TIFFGetField(tif, 33432 ,ctypes.byref(x))
    result["Copyright"]=x.value

    return result


def test_read_tags(filename):
    tif, tlib = OpenTiff(filename,"r")
    tags=GetTiffTags(tif, tlib)
    for k,v in tags.items():
        print k, ":", v
    tlib.TIFFClose(tif)



def GetTiffData(tif, tlib, tags=None):

    if tags==None:
        tags=GetTiffTags(tif, tlib)


        
    data=[]
    # TODO: We should try to put this into a numpy or PIL
    #       style buffer directly
    if tlib.TIFFIsTiled(tif):
        return _readtiled( tags, tif, tlib )
    else:
        return _readstrips( tags, tif ,tlib )

def _readtiled(tags, til, tlib):
    return []

def _readstrips(tags, tif, tlib):
    log = logging.getLogger("_readstrips")
    w,h = tags["ImageWidth"], tags["ImageLength"]
    data = []
    # print "strip size",tlib.TIFFStripSize(tif) 
    buffer=(ctypes.c_ubyte * tlib.TIFFStripSize(tif) )()
    pbuffer=ctypes.pointer(buffer)
    if tlib.TIFFSetDirectory(tif,0) == 0:
        raise Tiff3Error("unable to set directory")
    for strip in range(tlib.TIFFNumberOfStrips(tif)):
        cc=tlib.TIFFReadEncodedStrip(tif, strip, pbuffer, -1)
        if cc == -1:
            print "there was an error"
        data+=list(pbuffer.contents)[:cc]
    if len(data) != w*h:
        log.warning("short read %d bytes out of %d expected"%(
                len(data), w*h))
    return data


def test_read_data(filename):
    tif, tlib = OpenTiff(filename,"r")
    tags=GetTiffTags(tif, tlib)
    data=GetTiffData(tif, tlib, tags)
    w=tags["ImageWidth"]
    h=tags["ImageLength"]
    
    M=max(data)
    m=min(data)
    tlib.TIFFClose(tif)
    
    fp=open("o.pgm", "w")
    fp.write("P2\n%d %d\n%d\n"%(w,h,M))
    N=12
    for i in range(0, len(data), N):
        for j in range(N):
            k=i+j
            if k > w*h: continue
            fp.write("%d "%(data[k]))
        fp.write("\n")
    fp.close()



# These bits added by JPW for convenient checking
def GetTiffTagsAndData( filename ):
    """ Returns the tags and data """
    tif, tlib = OpenTiff( filename, "r" )
    tags = GetTiffTags(tif, tlib)
    data = GetTiffData(tif, tlib, tags)
    tlib.TIFFClose(tif)
    return tags, data


if __name__=="__main__":
    import os, glob, traceback
    testfiles = glob.glob(os.path.join("libtiffpic",
                                       "*.tif"))
    passed = 0
    failed = 0
    for filename in testfiles:
        try:
            tags, data = GetTiffTagsAndData( filename )
            print "passed", filename
            passed += 1
        except:
            traceback.print_exc()
            print "failed", filename
            failed += 1
    print passed, failed, passed + failed
