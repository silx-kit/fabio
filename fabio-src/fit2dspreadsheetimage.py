

"""
Read the fit2d ascii image output
        + Jon Wright, ESRF
"""

import numpy

from fabioimage import fabioimage




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
            xdim = int(items[0])
            ydim = int(items[1])
        except:
            raise
        self.header['title'] = line
        self.header['Dim_1'] = xdim
        self.header['Dim_2'] = ydim

    def read(self, fname, frame=None):
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
        bytecode = numpy.float32

        self.bpp = len(numpy.array(0, bytecode).tostring())

        #now read the data into the array
        try:
            vals = []
            for line in infile.readlines():
                try:
                    vals.append([float(x) for x in line.split()])
                except:
                    pass
            self.data = numpy.array(vals).astype(bytecode)
            assert self.data.shape == (self.dim2, self.dim1)

        except:
            raise IOError, "Error reading ascii"

        self.resetvals()
        # ensure the PIL image is reset
        self.pilimage = None
        return self


if __name__ == "__main__":
    import sys, time
    start = time.time()
    img = fit2dspreadsheetimage()
    img.read(sys.argv[1])
    print time.time() - start
    print img.dim1, img.dim2, img.data.shape
    from matplotlib.pylab import imshow, show
    imshow(img.data.T)
    show()
