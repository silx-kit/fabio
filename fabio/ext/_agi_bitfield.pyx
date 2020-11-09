# -*- coding: utf-8 -*-
#cython: embedsignature=True, language_level=3
## This is for optimisation
#cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False,
## This is for developping:
##cython: profile=True, warn.undeclared=True, warn.unused=True, warn.unused_result=False, warn.unused_arg=True
#
#    Project: Fable Input/Output
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) 2020-2020 European Synchrotron Radiation Facility, Grenoble, France
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Compression and decompression extension for Esperanto format
"""
__author__ = "Jérôme Kieffer"
__date__ = "09/11/2020"
__contact__ = "Jerome.kieffer@esrf.fr"
__license__ = "MIT"


from libc.stdint cimport int32_t


cpdef int32_t fieldsize(int32_t nbvalue):
    "Direct translation of Fortran"
    cdef int getfieldsize
    if(nbvalue < -63):
        getfieldsize = 8
    elif(nbvalue < -31):
        getfieldsize = 7
    elif(nbvalue < -15):
        getfieldsize = 6
    elif(nbvalue < -7):
        getfieldsize = 5
    elif(nbvalue < -3):
        getfieldsize = 4
    elif(nbvalue < -1):
        getfieldsize = 3
    elif(nbvalue < 0):
        getfieldsize = 2
    elif(nbvalue < 2):
        getfieldsize = 1
    elif(nbvalue < 3):
        getfieldsize = 2
    elif(nbvalue < 5):
        getfieldsize = 3
    elif(nbvalue < 9):
        getfieldsize = 4
    elif(nbvalue < 17):
        getfieldsize = 5
    elif(nbvalue < 33):
        getfieldsize = 6
    elif(nbvalue < 65):
        getfieldsize = 7
    else:
        getfieldsize = 8
    return getfieldsize


cpdef int32_t get_fieldsize(int32_t[::1] array):
    """determine the fieldsize to store the given values
    
    :param array numpy.array
    :returns int
    """
    cdef:
        int32_t size, idx, maxi, mini, value
    maxi = mini = 0
    size = array.shape[0]
    for idx in range(size):
        value = array[idx]
        maxi = max(maxi, value)
        mini = min(mini, value)
    
    return max(fieldsize(maxi), fieldsize(mini))