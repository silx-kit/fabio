import numpy
from fabio import compression
test = numpy.array([0, 1, 2, 127, 0, 1, 2, 128, 0, 1, 2, 32767, 0, 1, 2, 32768, 0, 1, 2, 2147483647, 0, 1, 2, 2147483648, 0, 1, 2, 128, 129, 130, 32767, 32768, 128, 129, 130, 32768, 2147483647, 2147483648])
b = compression.compByteOffset_numpy(test)
print(compression.decByteOffset_cython(b) - test)
print(compression.decByteOffset_numpy(b) - test)