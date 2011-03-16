"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:henning.sorensen@risoe.dk

mods for fabio by JPW

"""
import sys, logging
from fabioutils  import deconstruct_filename, getnum, filename_object
from fabioimage import fabioimage
import edfimage
import adscimage
import tifimage
import marccdimage
import mar345image
import fit2dmaskimage
import brukerimage
import bruker100image
import pnmimage
import GEimage
import OXDimage
import dm3image
import HiPiCimage
import pilatusimage
import fit2dspreadsheetimage
import kcdimage
import cbfimage
import xsdimage

MAGIC_NUMBERS = [
    # "\42\5a" : 'bzipped'
    # "\1f\8b" : 'gzipped'
    ("FORMAT :        86" , 'bruker'),
    ("\x4d\x4d\x00\x2a"   , 'tif') ,
    # The marCCD and Pilatus formats are both standard tif with a header
    # hopefully these byte patterns are unique for the formats
    # If not the image will be read, but the is missing 
    ("\x49\x49\x2a\x00\x08\x00"   , 'marccd') ,
    ("\x49\x49\x2a\x00\x82\x00"   , 'pilatus') ,
    ("\x49\x49\x2a\x00"   , 'tif') ,
    # ADSC must come before edf
    ("{\nHEA"             , 'adsc'),
    ("{"                  , 'edf'),
    ("\r{"                , 'edf'),
    ("\n{"                , 'edf'),
    ("ADEPT"              , 'GE'),
    ("OD"                 , 'OXD'),
    ("IM"                 , 'HiPiC'),
    ('\x2d\x04'           , 'mar345'),
    ('\x04\x2d'           , 'mar345'), #some machines may need byteswapping
    # hint : MASK in 32 bit
    ('M\x00\x00\x00A\x00\x00\x00S\x00\x00\x00K\x00\x00\x00' , 'fit2dmask') ,
    ('\x00\x00\x00\x03'   , 'dm3'),
    ("No"                 , "kcd"),
    ("<"                  , "xsd")
    ]

def do_magic(byts):
    """ Try to interpret the bytes starting the file as a magic number """
    for magic, format in MAGIC_NUMBERS:
        if byts.find(magic) == 0:
            return format
        if 0: # debugging - bruker needed 18 bytes below
            print "m:", magic, "f:", format,
            print "bytes:", magic, "len(bytes)", len(magic),
            print "found:", byts.find(magic)
            for i in range(len(magic)):
                print ord(magic[i]), ord(byts[i]), magic[i], byts[i]
    raise Exception("Could not interpret magic string")


def openimage(filename):
    """ Try to open an image """
    if isinstance(filename, filename_object):
        try:
            obj = _openimage(filename.tostring())
            obj.read(filename.tostring())
        except:
            # multiframe file
            #print "DEBUG: multiframe file, start # %d"%(
            #    filename.num)
            obj = _openimage(filename.stem)
            obj.read(filename.stem, frame=filename.num)
    else:
        obj = _openimage(filename)
        obj.read(filename)
    return obj


def openheader(filename):
    """ return only the header"""
    obj = _openimage(filename)
    obj.readheader(filename)
    return obj


def _openimage(filename):
    """ 
    determine which format for a filename
    and return appropriate class which can be used for opening the image
    """
    try:
        imo = fabioimage()
        byts = imo._open(filename).read(18)
        filetype = do_magic(byts)
	# print filetype
        if filetype == "marccd" and filename.find("mccd") == -1:
            # Cannot see a way around this. Need to find something
            # to distinguish mccd from regular tif...
            filetype = "tif"
        #UNUSED filenumber = getnum(filename)
    except IOError:
        # File probably does not exist
        raise
    except:
        try:
            file_obj = deconstruct_filename(filename)
            if file_obj == None:
                raise Exception
            if len(file_obj.format) != 1 and \
                    type(file_obj.format) != type(["list"]):
                # one of OXD/ ADSC - should have got in previous
                raise Exception("openimage failed on magic bytes & name guess")
            filetype = file_obj.format
            #UNUSED filenumber = file_obj.num
        except:
            #import traceback
            #traceback.print_exc()
            raise Exception("Fabio could not identify " + filename)
    klass_name = "".join(filetype) + 'image'
#    print "looking for %s in" % klass_name
#    for i in sys.modules:
#        if klass_name in i:
#            print "%s\t%s" % (i, sys.modules[i])
    module = sys.modules.get("fabio." + klass_name, None)
#    if hasattr(__init__, klass_name):
#        module = getattr(__init__, klass_name)
    if module is not None:
        if hasattr(module, klass_name):
            klass = getattr(module, klass_name)
                # print klass
        else:
            raise Exception("Module %s has no image class" % module)
    else:
        raise Exception("Filetype not known %s %s" % (filename, klass_name))
    obj = klass()
    # skip the read for read header
    return obj





