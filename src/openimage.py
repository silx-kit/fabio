

"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:henning.sorensen@risoe.dk

mods for fabio by JPW

"""

import fabio
from fabio import deconstruct_filename, getnum
from fabio.fabioimage import fabioimage


from fabio import edfimage
from fabio import adscimage
from fabio import tifimage
from fabio import marccdimage
from fabio import mar345image
from fabio import fit2dmaskimage
from fabio import brukerimage
from fabio import bruker100image
from fabio import pnmimage
from fabio import GEimage


MAGIC_NUMBERS = {
    # "\42\5a" : 'bzipped'
    # "\1f\8b" : 'gzipped'
    "\x4d\x4d\x00\x2a"   : 'tif' ,
    "\x49\x49\x2a\x00"   : 'tif' ,
    "{"                  : 'edf',
    "\r{"                : 'edf',
    "FORMAT :        86" : 'bruker', 
    "ADEPT"         : 'GE',
    # hint : MASK in 32 bit
    'M\x00\x00\x00A\x00\x00\x00S\x00\x00\x00K\x00\x00\x00' : 'fit2dmask' ,
    }

def do_magic(byts):
    """ Try to interpret the bytes starting the file as a magic number """
    for magic, format in MAGIC_NUMBERS.iteritems():
        if byts.find(magic) == 0:
            return format
    raise Exception("Could not interpret magic string")

def openimage(filename):
    """ Try to open an image """
    try:
        file_obj = deconstruct_filename(filename)
        filetype = file_obj.format
        filenumber = file_obj.num
    except:
        imo = fabioimage()
        byts = imo._open(filename).read(16)
        filetype = do_magic(byts)
        filenumber = getnum(filename)

    klass_name = filetype + 'image' 
    #print "looking for",klass_name
    if hasattr(fabio, klass_name):
        module = getattr(fabio, klass_name)
        if hasattr(module, klass_name):
            klass  = getattr(module, klass_name)
        else:
            raise Exception("Module " + module + "has no image class")
    else:
        raise Exception("Filetype not known " + filename + " " +
                        klass_name)
    obj = klass()
    obj.read(filename)
    return obj

        



