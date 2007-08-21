
import tifimage, adscimage, brukerimage
import marccdimage, bruker100image, pnmimage


from fabioimage import fabioimage
from edfimage import edfimage
from marccdimage import marccdimage

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
        return m.group(1) + string.zfill(newfilenumber,len(m.group(2))) + m.group(3)
    else:
        return oldfilename

def deconstruct_filename(filename):
    p=re.compile(r"^(.*?)(-?[0-9]{0,4})(\D*)$")
    m=re.match(p,filename)
    if m==None or m.group(2)=='':
        number=0;
    else:
        number=int(m.group(2))
    ext=os.path.splitext(filename)
    filetype={'edf': 'edf',
              'gz': 'edf',
              'bz2': 'edf',
              'pnm' : 'pnm',
              'pgm' : 'pnm',
              'pbm' : 'pnm',
              'tif': 'tif',
              'tiff': 'tif',
              'img': 'adsc',
              'mccd': 'marccd',
              'sfrm': 'bruker100',
              m.group(2): 'bruker'
              }[ext[1][1:]]
    return (number,filetype)

def extract_filenumber(filename):
    return deconstruct_filename(filename)[0]

class fabio:
    def __init__(self):
        self.filenumber = None
        self.filetype = None
    
    def openimage(self,filename=None):
        #if a filename is supplied use that - otherwise get it from the GUI
        if filename==None:
            filename=self.filename.get()

        (self.filenumber,self.filetype)=deconstruct_filename(filename)

        img=eval( self.filetype+'image.'+self.filetype+'image()')
        try:
            self.im=img.read(filename).toPIL16()
            (self.im.minval,self.im.maxval,self.im.meanval)=(img.getmin(),img.getmax(\
                ),img.getmean())
            self.im.header=img.getheader()
            (self.xsize, self.ysize)=(img.dim1, img.dim2)
        except IOError:
            raise
 



