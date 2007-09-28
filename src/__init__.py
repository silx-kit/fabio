



import re, os # -> move elsewhere?


def construct_filename(oldfilename, newfilenumber, padding=True):
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
    num_list = []
    first = False
    for byt in name[::-1]: # this means iterate backwards through the string
        if byt.isdigit():
            first = True
            num_list.append(byt)
            continue
        if first: 
            break
    num = "".join(num_list[::-1])
    try:
        return int(num)
    except ValueError:
        return 0
        


def deconstruct_filename(filename):
    """
    Break up a filename to get image type and number
    """
    parts = os.path.split(filename)[-1].split(".")
    # loop back from end
    compressed = False
    if parts[-1] in ["gz","bz2"]:
        parts = parts[:-1]
        compressed=True
    if parts[-1] in FILETYPES.keys():
        typ = FILETYPES[parts[-1]]
        try:
            num = getnum("".join(parts[:-1]))
        except:
            num = 0
    else:
        try:
            num = int(parts[-1])
            typ = 'bruker'
        except:
            # unregistered type??
            raise Exception("Cannot decode "+filename)
    return num, typ



def extract_filenumber(filename):
    return deconstruct_filename(filename)[0]

