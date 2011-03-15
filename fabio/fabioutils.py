import re, os

def construct_filename(*args, **kwds):
    raise Exception("You probably want fabio.jump_filename")



FILETYPES = {
    # extension NNNimage fabioclass
    # type consistency - always use a list if one case is
    'edf'    : ['edf'],
    'cor'    : ['edf'],
    'pnm'    : ['pnm'],
    'pgm'    : ['pnm'],
    'pbm'    : ['pnm'],
    'tif'    : ['tif'],
    'tiff'   : ['tif'],
    'img'    : ['adsc', 'OXD', 'HiPiC'],
    'mccd'   : ['marccd'],
    'mar2300': ['mar345'],
    'sfrm'   : ['bruker100'],
    'msk'    : ['fit2dmask'],
    'spr'    : ['fit2dspreadsheet'],
    'dm3'    : ['dm3'],
    'kcd'    : ['kcd'],
    'cbf'    : ['cbf'],
    'xml'    : ["xsd"],
    'xsd'    : ["xsd"],
             }

# Add bzipped and gzipped
for key in FILETYPES.keys():
    FILETYPES[key + ".bz2"] = FILETYPES[key]
    FILETYPES[key + ".gz"] = FILETYPES[key]


# Compressors

COMPRESSORS = {}

try:
    lines = os.popen("gzip -h 2>&1").read()
    # Looking for "usage"
    if "sage" in lines:
        COMPRESSORS['.gz'] = 'gzip -dc '
    else:
        COMPRESSORS['.gz'] = None
except:
    COMPRESSORS['.gz'] = None

try:
    lines = os.popen("bzip2 -h 2>&1").read()
    # Looking for "usage" 
    if "sage" in lines:
        COMPRESSORS['.bz2'] = 'bzip2 -dc '
    else:
        COMPRESSORS['.bz2'] = None
except:
    COMPRESSORS['.bz2'] = None

# print COMPRESSORS

def getnum(name):
    """
    # try to figure out a file number
    # guess it starts at the back
    """
    stem , num, post_num = numstem(name)
    try:
        return int(num)
    except ValueError:
        return None

class filename_object:
    """
    The 'meaning' of a filename
    """
    def __init__(self, stem,
            num=None,
            directory=None,
            format=None,
            extension=None,
            postnum=None,
            digits=4):
        self.stem = stem
        self.num = num
        self.format = format
        self.extension = extension
        self.digits = digits
        self.postnum = postnum
        self.directory = directory
        #print self.str()

    def str(self):
        """ Return a string representation """
        fmt = "stem %s, num %s format %s extension %s " + \
                "postnum = %s digits %s dir %s"
        return fmt % tuple([str(x) for x in [
                    self.stem ,
                    self.num ,
                    self.format ,
                    self.extension ,
                    self.postnum ,
                    self.digits ,
                    self.directory ] ])


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


def numstem(name):
    """ cant see how to do without reversing strings
    Match 1 or more digits going backwards from the end of the string
    """
    reg = re.compile(r"^(.*?)(-?[0-9]{0,9})(\D*)$")
    #reg = re.compile("""(\D*)(\d\d*)(\w*)""")
    try:
        res = reg.match(name).groups()
        #res = reg.match(name[::-1]).groups()
        #return [ r[::-1] for r in res[::-1]]
        if len(res[0]) == len(res[1]) == 0: # Hack for file without number 
            return [res[2], '', '']
        return [ r for r in res]
    except AttributeError: # no digits found
        return [name, "", ""]

def deconstruct_filename(filename):
    """
    Break up a filename to get image type and number
    """
    direc , name = os.path.split(filename)
    if len(direc) == 0:
        direc = None
    parts = os.path.split(name)[-1].split(".")
    # loop back from end
    compressed = False
    extn = ""
    postnum = ""
    ndigit = 4
    if parts[-1] in ["gz", "bz2"]:
        extn = "." + parts[-1]
        parts = parts[:-1]
        compressed = True
    if parts[-1] in FILETYPES.keys():
        typ = FILETYPES[parts[-1]]
        extn = "." + parts[-1] + extn
        try:
            stem , numstring, postnum = numstem(".".join(parts[:-1]))
            num = int(numstring)
            ndigit = len(numstring)
        except:
            # There is no number - hence make num be None, not 0
            num = None
            stem = "".join(parts[:-1])
    else:
        # Probably two type left
        if len(parts) == 1:
            # Probably GE format stem_numb
            parts2 = parts[0].split("_")
            try:
                num = int(parts2[-1])
                ndigit = len(parts2[-1])
                typ = ['GE']
                stem = "_".join(parts2[:-1]) + "_"
            except:
                pass
        else:
            try:
                num = int(parts[-1])
                ndigit = len(parts[-1])
                typ = ['bruker']
                stem = ".".join(parts[:-1]) + "."
            except:
                typ = None
                extn = "." + parts[-1] + extn
                try:
                    stem , numstring, postnum = numstem(".".join(parts[:-1]))
                    num = int(numstring)
                    ndigit = len(numstring)
                except:
                    raise
            #            raise Exception("Cannot decode "+filename)
    obj = filename_object(stem,
            num=num,
            directory=direc,
            format=typ,
            extension=extn,
            postnum=postnum,
            digits=ndigit)

    return obj


def next_filename(name, padding=True):
    """ increment number """
    obj = deconstruct_filename(name)
    obj.num += 1
    if not padding:
        obj.digits = 0
    return obj.tostring()

def previous_filename(name, padding=True):
    """ decrement number """
    obj = deconstruct_filename(name)
    obj.num -= 1
    if not padding:
        obj.digits = 0
    return obj.tostring()

def jump_filename(name, num, padding=True):
    """ jump to number """
    obj = deconstruct_filename(name)
    obj.num = num
    if not padding:
        obj.digits = 0
    return obj.tostring()


def extract_filenumber(name):
    """ extract file number """
    obj = deconstruct_filename(name)
    return obj.num
