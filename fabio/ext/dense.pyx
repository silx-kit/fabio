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
__date__ = "02/06/2022"  
__contact__ = "Jerome.kieffer@esrf.fr"
__license__ = "MIT"

import time
import numpy
# from cython.parallel import prange
from libc.stdint cimport int8_t, uint8_t, \
                         uint16_t, int16_t,\
                         int32_t, uint32_t,\
                         int64_t, uint64_t
from libc.math cimport isfinite, log, sqrt, cos, M_PI                         
from libc.stdlib cimport RAND_MAX
cimport cython
               
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

#Few constants for 64-bit Mersenne Twisters
cdef:
    uint32_t NN = 312
    uint32_t MM = 156
    uint64_t MATRIX_A = 0xB5026F5AA96619E9ULL
    uint64_t UM = 0xFFFFFFFF80000000ULL # Most significant 33 bits
    uint64_t LM = 0x7FFFFFFFULL #Least significant 31 bits
    double NRM53 = 1.0 / ((1<<53)-1) #Normalisation for 53 bit integer
    double EPS64 = numpy.finfo(numpy.float64).eps
    double TWO_PI = 2.0 * M_PI
    

cdef class MT:
    """
    This class implements 64-bit Mersenne Twisters
    
    http://www.math.sci.hiroshima-u.ac.jp/m-mat/MT/VERSIONS/C-LANG/mt19937-64.c
    
    Inspired from:
    https://github.com/ananswam/cython_random
    with minor clean-ups
    
    Licence: MIT
    """
    cdef:
        uint64_t mt[312]
        uint32_t mti
        uint64_t mag01[2]
        bint has_spare
        double spare

    
    def __init__(self, seed):
        self.mti = NN + 1
        self._seed(<uint64_t> seed)
    
    cdef inline void _seed(self, uint64_t seed) nogil:
        self.mt[0] = seed
        for self.mti in range(1, NN):
            self.mt[self.mti] = (6364136223846793005ULL * (self.mt[self.mti-1] ^ (self.mt[self.mti-1] >> 62)) + self.mti)
        self.mag01[0] = 0ULL
        self.mag01[1] = MATRIX_A
        self.mti = NN
        self.has_spare = False
        
    cdef inline uint64_t genrand64(self) nogil:
        cdef: 
            uint32_t i
            uint64_t x
        if self.mti >= NN:
            for i in range(NN - MM):
                x = (self.mt[i]&UM) | (self.mt[i+1]&LM)
                self.mt[i] = self.mt[i+MM] ^ (x>>1) ^ self.mag01[int(x&1ULL)]

            for i in range(NN-MM, NN-1):
                x = (self.mt[i]&UM)|(self.mt[i+1]&LM)
                self.mt[i] = self.mt[i+(MM-NN)] ^ (x>>1) ^ self.mag01[int(x&1ULL)]

            x = (self.mt[NN-1]&UM)|(self.mt[0]&LM)
            self.mt[NN-1] = self.mt[MM-1] ^ (x>>1) ^ self.mag01[int(x&1ULL)]
            self.mti = 0

        x = self.mt[self.mti]
        self.mti += 1
        x ^= (x >> 29) & 0x5555555555555555ULL
        x ^= (x << 17) & 0x71D67FFFEDA60000ULL
        x ^= (x << 37) & 0xFFF7EEE000000000ULL
        x ^= (x >> 43);
        return x
    
    def rand(self):
        return self.genrand64()%(<uint64_t>RAND_MAX+1)
    
    @cython.cdivision(True)
    cdef inline double _uniform(self) nogil:
        return (self.genrand64() >> 11) * NRM53
    
    def uniform(self):
        "Return a random value between [0:1["
        return self._uniform()
    
    cdef inline double _normal_bm(self, double mu, double sigma) nogil:
        "Box-Muller implementation of the normal distribution"
        cdef:
            double u1=0.0, u2=0.0
    
        while (u1 == 0.0):
            u1 = self._uniform()
            u2 = self._uniform()

        return sigma * sqrt(-2.0 * log(u1)) * cos(TWO_PI * u2) + mu;

    cdef inline double _normal_m(self, double mu, double sigma) nogil:
        "Marsaglia implementation of the normal distribution, 2xfaster than Box-Muller"
        cdef: 
            double u1=0.0, u2=0.0, s=0.0
        if self.has_spare:
            self.has_spare = False
            return mu + self.spare * sigma 
        else:
            while (s>=1 or s==0.0):
                u1 = 2.0 * self._uniform() - 1.0
                u2 = 2.0 * self._uniform() - 1.0
                s = u1 * u1 + u2 * u2;
            s = sqrt(-2.0*log(s)/s)
            self.spare = u2 * s
            self.has_spare = True
        return mu + sigma * u1 * s;

    def normal(self, mu, sigma): 
        """
        Calculate the gaussian distribution using the Marsaglia algorithm

        Credits:
        https://en.wikipedia.org/wiki/Marsaglia_polar_method
        https://en.wikipedia.org/wiki/Box%E2%80%93Muller_transform

        :param mu: the center of the distribution
        :param sigma: the width of the distribution
        :return: random value
        """       
        return self._normal_m(mu, sigma)



def distribution_uniform_mtc(shape, seed=None):
    "Function to test uniform distribution"
    if seed is None:  
        try:
            seed = time.time_ns()
        except:
            seed = int(time.time()*1e9)
    cdef: 
        uint64_t size = numpy.prod(shape), idx
        double[::1] ary = numpy.empty(size)
        MT mt = MT(seed)
    with nogil:
        for idx in range(size):
            ary[idx] = mt._uniform()
    return numpy.asarray(ary).reshape(shape)      


def distribution_normal_mtc(mu, sigma, seed=None):
    "Function to test normal distribution"
    shape = mu.shape
    assert mu.shape == sigma.shape
    if seed is None:  
        try:
            seed = time.time_ns()
        except:
            seed = int(time.time()*1e9)
    cdef: 
        uint64_t size = numpy.prod(shape), idx
        double[::1] ary = numpy.empty(size)
        double[::1] cmu = numpy.ascontiguousarray(mu, dtype=numpy.float64).ravel()
        double[::1] csigma = numpy.ascontiguousarray(sigma, dtype=numpy.float64).ravel()
        MT mt = MT(seed)
    with nogil:
        for idx in range(size):
            ary[idx] = mt._normal_m(cmu[idx], csigma[idx])
    return numpy.asarray(ary).reshape(shape)        


def densify(cython.floating[:,::1] mask,
            cython.floating[::1] radius,
            uint32_t[::1] index,
            any_t[::1] intensity,
            any_t dummy,
            dtype,
            float[::1] background,
            float[::1] background_std=None,
            normalization=None,
            seed = None):
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
    :param normalization: normalization array: renormalize all data with this factor (pixel-wise)
    :param seed: seed for the random number-generator, used only when regenerating noisy background
    :return: dense frame as 2D array
    """
    cdef:
        Py_ssize_t i, j, size, pos, size_over, width, height
        double value, fres, fpos, idelta, start, std
        bint integral, noisy, do_normalization=False
        any_t[:, ::1] dense
        float[:,::1] c_normalization
        MT mt
    size = radius.shape[0]
    assert background.shape[0] == size
    size_over = index.shape[0]
    assert intensity.shape[0] == size_over
    integral = numpy.issubdtype(dtype, numpy.integer)
    height =mask.shape[0] 
    width = mask.shape[1]
    dense = numpy.zeros((height, width), dtype=dtype)
    if normalization is not None:
        do_normalization = True
        c_normalization = numpy.ascontiguousarray(normalization, dtype=numpy.float32)
    
    if background_std is None:
        noisy = False
    else:
        noisy=True
        if seed is None:
            try:
                seed = time.time_ns()
            except Exception:
                seed = int(time.time()*1e9)
        mt = MT(seed)
                
    with nogil:
        start = radius[0]
        idelta = <double>(size - 1)/(radius[size-1] - start)  
        
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
                        if pos+1 == size:
                            std = background_std[pos]
                            fres = 0.0
                        else:
                            std = (1.0 - fres)*background_std[pos] + fres*background_std[pos+1]
                        value = max(0.0, mt._normal_m(value, std))
                    if do_normalization:
                        value *= c_normalization[i, j]
                    if integral:
                        dense[i,j] =  <any_t>(value + 0.5) #this is rounding
                    else:
                        dense[i,j] =  <any_t>(value) 
        # Assignment of outliers
        for i in range(size_over):
            j = index[i]
            dense[j//width, j%width] = intensity[i]
    return numpy.asarray(dense) 