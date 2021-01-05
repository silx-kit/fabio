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

"""Densification of sparse frame format
"""
__author__ = "Jérôme Kieffer"
__date__ = "18/12/2020"  
__contact__ = "Jerome.kieffer@esrf.fr"
__license__ = "MIT"

import time
import numpy

from libc.stdint cimport int8_t, uint8_t, \
                         uint16_t, int16_t,\
                         int32_t, uint32_t,\
                         int64_t, uint64_t
from libc.math cimport isfinite, log, sqrt, cos, M_PI                         
from libc.stdlib cimport rand, RAND_MAX, srand
               
ctypedef fused any_t:
    double
    float
    int8_t
    uint8_t
    uint16_t
    int16_t
    int32_t
    uint32_t
    int64_t
    uint64_t

cdef:
    double EPS64 = numpy.finfo(numpy.float64).eps
    double two_pi = 2.0*M_PI


cdef double random_normal(double mu, double sigma) nogil:
    """
    Calculate the gaussian distribution using the Box–Muller algorithm
    
    Credits:
    https://en.wikipedia.org/wiki/Box%E2%80%93Muller_transform
    
    :param mu: the center of the distribution
    :param sigma: the width of the distribution
    """    
    cdef:
        double u1, u2, mag
    
    u1 = u2 = 0.0
    
    while (u1 < EPS64):
        u1 = <double> rand() / RAND_MAX 
        u2 = <double> rand() / RAND_MAX
    
    mag = sigma * sqrt(-2.0 * log(u1));
    return mag * cos(two_pi * u2) + mu;
    

def densify(float[:,::1] mask,
            float[::1] radius,
            uint32_t[::1] index,
            any_t[::1] intensity,
            any_t dummy,
            dtype,
            float[::1] background,
            float[::1] background_std=None):
    """
    Densify a sparse representation to generate a normal frame 
    
    :param mask: 2D array with NaNs for mask and pixel radius for the valid pixels
    :param radius: 1D array with the radial distance
    :param background: 1D array with the background values at given distance from the center
    :param index: position of non-background pixels
    :param intensity: intensities of non background pixels (at index position)
    :param dummy: numerical value for masked-out pixels in dense image
    :param dtype: dtype of intensity.
    :param background_std: 1D array with the background std at given distance from the center --> activates the noisy mode.
    :return: dense frame as 2D array
    """
    cdef:
        Py_ssize_t i, j, size, pos, size_over, width, height
        double value, fres, fpos, idelta, start, std
        bint integral, noisy
        any_t[:, ::1] dense
        
    size = radius.shape[0]
    assert background.shape[0] == size
    size_over = index.shape[0]
    assert intensity.shape[0] == size_over
    integral = numpy.issubdtype(dtype, numpy.integer)
    height =mask.shape[0] 
    width = mask.shape[1]
    dense = numpy.zeros((height, width), dtype=dtype)
    
    noisy = background_std is not None
    if noisy:
        try:
            value = time.time_ns()
        except Exception:
            value = int(time.time()/EPS64)
        srand(<unsigned int> (value%RAND_MAX))
                
    with nogil:
        start = radius[0]
        idelta = (size - 1)/(radius[size-1] - start)  
        
        #Linear interpolation
        for i in range(height):
            for j in range(width):
                fpos = (mask[i,j] - start)*idelta
                if (fpos<0) or (fpos>=size) or (not isfinite(fpos)):
                    dense[i,j] = dummy 
                else:
                    pos = <uint32_t> fpos
                    if pos+1 == size:
                        value = background[pos]
                        fres = 0.0
                    else:
                        fres = fpos - pos
                        value = (1.0 - fres)*background[pos] + fres*background[pos+1]
                    if noisy:
                        std = (1.0 - fres)*background_std[pos] + fres*background_std[pos+1]
                        value = max(0.0, random_normal(value, std))
                        
                    if integral:
                        dense[i,j] =  <any_t>(value + 0.5) #this is rounding
                    else:
                        dense[i,j] =  <any_t>(value) 
        # Assignment of outliers
        for i in range(size_over):
            j = index[i]
            dense[j//width, j%width] = intensity[i]
    return numpy.asarray(dense) 

                
