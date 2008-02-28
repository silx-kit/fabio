

"""
Read the fit2d ascii image output
        + Jon Wright, ESRF
"""

import numpy.oldnumeric as Numeric, logging

from fabio.fabioimage import fabioimage




class fit2dspreadsheetimage(fabioimage):
    """
    Read a fit2d ascii format
    """
    
    def _readheader(self, infile):
        """

        TODO : test for minimal attributes?
        """
        line = infile.readline()
        try:
            items = line.split()
            xd = int(items[0])
            yd = int(items[1])
        except:
            raise
        self.header['title'] = line
        self.header['Dim_1'] = xd
        self.header['Dim_2'] = yd
        
    def read(self, fname):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = {}
        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)
        # Compute image size
        try:
            self.dim1 = int(self.header['Dim_1'])
            self.dim2 = int(self.header['Dim_2'])
        except:
            raise Exception("file", str(fname) + \
                                "is corrupt, cannot read it")
        bytecode = Numeric.Float32

        self.bpp = len(Numeric.array(0, bytecode).tostring())

        #now read the data into the array
        if 1:
#            import time
#            start = time.time()
            try:
                vals = []
                for line in infile.readlines():
                    try:
                        vals.append([float(x) for x in line.split()])
                    except:
                        pass
                self.data = Numeric.array(vals)
                assert self.data.shape ==( self.dim2, self.dim1)

            except:
                raise IOError, "Error reading ascii"
#            print time.time()-start
        if 0:
            # numpy version - it is slower(!)
            infile.seek(0)
            infile.readline()
            from numpy import loadtxt
            import time
            start = time.time()
            self.data = loadtxt( infile )
            assert self.data.shape ==( self.dim2, self.dim1)
            print time.time()-start
        self.resetvals()
        # ensure the PIL image is reset
        self.pilimage = None
        return self


if __name__=="__main__":
    import sys, time
    start = time.time()
    im = fit2dspreadsheetimage()
    im.read(sys.argv[1])
    print time.time()-start
    print im.dim1, im.dim2, im.data.shape
    from matplotlib.pylab import imshow, show
    imshow(im.data.T)
    show()
