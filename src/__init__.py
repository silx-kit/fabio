



import re, os # -> move elsewhere?


def construct_filename_old(oldfilename, newfilenumber, padding=True):
    #some code to replace the filenumber in oldfilename with newfilenumber
    #by figuring out how the files are named
    import string
    p=re.compile(r"^(.*?)(-?[0-9]{0,4})(\D*)$")
    m=re.match(p,oldfilename)
    if padding==False:
        return m.group(1) + str(newfilenumber) + m.group(3)
    if m.group(2)!='':
        return m.group(1) + string.zfill(newfilenumber,len(m.group(2))) + \
            m.group(3)
    else:
        return oldfilename

def construct_filename_erik(oldfilename, newfilenumber, padding=True):
    #some code to replace the filenumber in oldfilename with newfilenumber
    #by figuring out how the files are named
    #mask the mar2300 construction
    name=oldfilename.replace("mar2300","mar----")
    
    rev_oldnum=str(getnum(name))[::-1]
    if padding:
        rev_newnum=str(newfilenumber).zfill(len(rev_oldnum))[::-1]
    else:
        rev_newnum=str(newfilenumber)[::-1]
    
    rev_newname=name[::-1].replace(rev_oldnum,rev_newnum,1)
    if padding and len(rev_oldnum)<len(rev_newnum):
        #catch case when f.i. going from 9 to 10 with zero padding
        #the result is that there is an extra 0 in front that needs to be removed
        first=rev_newname.find(rev_newnum+"0")
        if first>=0:
            rev_newname=rev_newname[:first+len(rev_newnum)]+rev_newname[first+1+len(rev_newnum):]
    return rev_newname[::-1].replace("mar----","mar2300")

def construct_filename(*args, **kwds):
    raise Exception("You probably want fabio.jump_filename")

def deconstruct_filename_old(filename):
    p=re.compile(r"^(.*?)(-?[0-9]{0,4})(\D*)$")
    # misses when data9999.edf -> data10000.edf
    m=re.match(p,filename)
    if m==None or m.group(2)=='':
        number=0;
    else:
        number=int(m.group(2))
    ext=os.path.splitext(filename)
    filetype={'edf' : 'edf',
              'gz'  : 'edf',
              'bz2' : 'edf',
              'pnm' : 'pnm',
              'pgm' : 'pnm',
              'pbm' : 'pnm',
              'tif' : 'tif',
              'tiff': 'tif',
              'img' : 'adsc',
              'mccd': 'marccd',
              'sfrm': 'bruker100',
              m.group(2): 'bruker'
              }[ext[1][1:]]
    return (number,filetype)


FILETYPES = {
    # extension XXXimage fabioclass
    'edf'    : 'edf',
    'cor'    : 'edf',
    'pnm'    : 'pnm',
    'pgm'    : 'pnm',
    'pbm'    : 'pnm',
    'tif'    : 'tif',
    'tiff'   : 'tif',
    'img'    : 'adsc',
    'mccd'   : 'marccd',
    'mar2300': 'mar345',
    'sfrm'   : 'bruker100',
    'msk'    : 'fit2dmask',
             }

# Add bzipped and gzipped
for key in FILETYPES.keys():
    FILETYPES[key+".bz2"] = FILETYPES[key]
    FILETYPES[key+".gz"]  = FILETYPES[key]

    
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
            num = None,
            directory = None, 
            format = None, 
            extension = None, 
            postnum = None,
            digits = 4): 
        self.stem = stem
        self.num = num
        self.format = format
        self.extension = extension
        self.digits = digits
        self.postnum = postnum
        self.directory = directory
        #print self.str()

    def str(self):
        return "stem %s, num %s format %s extension %s postnum = %s digits %s dir %s"%tuple([
            str(x) for x in [self.stem , 
                self.num , 
                self.format , 
                self.extension , 
                self.postnum ,
                self.digits , 
                self.directory ] ] )

        
    def tostring(self):
        """
        convert yourself to a string
        """
        name = self.stem
        if self.digits is not None and self.num is not None:
            fmt = "%0"+str(self.digits)+"d"
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
    import re
    reg = re.compile("""(\D*)(\d\d*)(\w*)""")
    try:
        res = reg.match(name[::-1]).groups()
        return [ r[::-1] for r in res[::-1]]
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
    if parts[-1] in ["gz","bz2"]:
        extn = "."+parts[-1]
        parts = parts[:-1]
        compressed=True
    if parts[-1] in FILETYPES.keys():
        typ = FILETYPES[parts[-1]]
        extn = "." + parts[-1] + extn
        try:
            stem , numstring, postnum = numstem("".join(parts[:-1]))
            num = int(numstring)
            ndigit = len(numstring)
        except:
            # There is no number - hence make num be None, not 0
            num = None
            stem = "".join(parts[:-1])
    else:
        try:
            num = int(parts[-1])
            ndigit = len(parts[-1])
            typ = 'bruker'
            stem = ".".join(parts[:-1])+"."
        except:
            # unregistered type??
            raise
#            raise Exception("Cannot decode "+filename)

    obj = filename_object( stem,  
            num = num,
            directory = direc, 
            format = typ, 
            extension = extn, 
            postnum = postnum,
            digits = ndigit ) 
     
    return obj


def next_filename(name, padding=True):
    """ increment number """
    obj = deconstruct_filename(name)
    obj.num += 1
    if not padding:
        obj.ndigits = 0
    return obj.tostring()

def previous_filename(name, padding=True):
    """ decrement number """
    obj = deconstruct_filename(name)
    obj.num -= 1
    if not padding:
        obj.ndigits = 0
    return obj.tostring()

def jump_filename(name, num, padding=True):
    """ jump to number """
    obj = deconstruct_filename(name)
    obj.num = num
    if not padding:
        obj.ndigits = 0
    return obj.tostring()


def extract_filenumber(filename):
    return deconstruct_filename(filename)[0]

