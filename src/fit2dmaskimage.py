## Automatically adapted for numpy.oldnumeric Oct 05, 2007 by alter_code1.py

#!/usr/bin/env python
"""

Author: Andy Hammersley, ESRF
Translation into python/fabio: Jon Wright, ESRF
"""

import numpy as N

from fabio.fabioimage import fabioimage


class fit2dmaskimage(fabioimage):
    """ Read and try to write Andy Hammersleys mask format """


    def _readheader(self, infile):
        """
        Read in a header from an already open file
        """
        # 1024 bytes gives 256x32 bit integers
        header = infile.read(1024)
        for i, j in [ ("M",  0),
                      ("A",  4),
                      ("S",  8),
                      ("K", 12)  ]:
            if header[j] != i:
                raise Exception("Not a fit2d mask file")
        fit2dhdr = N.fromstring(header, N.int32)
        self.dim1 = fit2dhdr[4] # 1 less than Andy's fortran
        self.dim2 = fit2dhdr[5]


    def read(self, fname ):
        """
        Read in header into self.header and
            the data   into self.data
        """
        fin = self._open(fname)
        self._readheader(fin)
        # Compute image size
        self.bytecode = N.uint8
        self.bpp = len(N.array(0, self.bytecode).tostring())

        # integer division
        num_ints = (self.dim1 + 31)//32
        total = self.dim2 * num_ints * 4
        data = fin.read(total)
        assert len(data) == total
        fin.close()

        # Now to unpack it
        data = N.fromstring(data, N.uint8)
        data = N.reshape(data, (self.dim2, num_ints*4))

        result = N.zeros((self.dim2, num_ints*4*8), N.uint8)

        # Unpack using bitwise comparisons to 2**n
        bits = N.ones((1), N.uint8)
        for i in range(8):
            temp =  N.bitwise_and( bits, data)
            result[:, i::8] = temp.astype(N.uint8)
            bits = bits * 2
        # Extra rows needed for packing odd dimensions
        spares = num_ints*4*8 - self.dim1
        if spares == 0:
            self.data = N.where(result == 0, 0, 1)
        else:
            self.data = N.where(result[:,:-spares] == 0, 0, 1)
        # Transpose appears to be needed to match edf reader (scary??)
#        self.data = N.transpose(self.data)
        self.data = N.reshape(self.data.astype(N.uint16),
                                    (self.dim2, self.dim1))
        self.pilimage = None



    def write(self, fname ):
        """
        Try to write a file
        check we can write zipped also
        mimics that fabian was writing uint16 (we sometimes want floats)
        """
        raise Exception("Not implemented yet")
