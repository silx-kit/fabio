# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
#
#    Copyright (C) 2015 European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
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
"""
New Cython version of mar345_IO for preparing the migration to Python3

Compressor & decompressor for "pack" algorithm by JPA, binding to CCP4 libraries
those libraries are re-implemented in Cython

"""

__authors__ = ["Jerome Kieffer", "Gael Goret"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "2012-2015, European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "14/09/2016" 

import cython
cimport numpy as cnp

import numpy
import os
import tempfile
import logging
logger = logging.getLogger("mar345_IO")

ctypedef fused any_int_t:
    cnp.int8_t
    cnp.int16_t
    cnp.int32_t
    cnp.int64_t

# Few constants:
cdef:
    cnp.uint8_t *CCP4_PCK_BIT_COUNT = [0, 4, 5, 6, 7, 8, 16, 32]
    cnp.uint8_t *CCP4_BITSIZE = [0, 0, 0, 0, 1, 2, 3, 4, 5, 0, 0, 0, 0, 0, 0, 0, 
                                 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7]
    int CCP4_PCK_BLOCK_HEADER_LENGTH = 6

    list bad_pixels = [1498519, 1498520, 1500817, 1500818, 1500819, 1500820, 1503117,
        1503118, 1503119, 1516878, 1519176, 1519177, 1519178, 1546882,
        1549180, 1549181, 1549182, 1549183, 1551479, 1551480, 1551481,
        1551482, 1551483, 1553780, 1553781, 1553782, 1604169, 1606467,
        1606468, 1606469, 1608767, 1608768, 1608769, 1673191, 1675489,
        1675490, 1675491, 1677789, 1677790, 1677791, 1719436, 1719437,
        1721734, 1721735, 1721736, 1721737, 1724034, 1724035, 1724036,
        1724037, 1726063, 1728361, 1728362, 1728363, 1740095, 1740096,
        1742393, 1742394, 1742395, 1742396, 1790573, 1790574, 1790575,
        1792872, 1792873, 1792874, 1792875, 1795171, 1795172, 1795173,
        1795174, 1795175, 1797472, 1797473, 1797474, 1797475, 1806816,
        1806817, 1809114, 1809115, 1809116, 1809117, 1903449, 1903450,
        1905747, 1905748, 1905749, 1905750, 1905751, 1908047, 1908048,
        1908049, 1908050, 1908051, 1910347, 1910348, 1910349, 1910350,
        1910351, 1912648, 1912649, 1912650, 1940168, 1940169, 1942466,
        1942467, 1942468, 1942469, 1944766, 1944767, 1944768, 1944769,
        1979011, 1979012, 1981309, 1981310, 1981311, 1981312, 2004683,
        2004684, 2006981, 2006982, 2006983, 2006984, 2009281, 2009282,
        2009283, 2009284, 2013250, 2015548, 2015549, 2015550, 2015551,
        2017848, 2017849, 2017850, 2017851, 2020934, 2020935, 2023232,
        2023233, 2023234, 2023235, 2105916, 2105917, 2108214, 2108215,
        2108216, 2108217, 2130545, 2130546, 2132843, 2132844, 2132845,
        2132846, 2132847, 2135143, 2135144, 2135145, 2135146, 2135147,
        2137443, 2137444, 2137445, 2137446, 2137447, 2199569, 2199570,
        2201867, 2201868, 2201869, 2201870, 2252848, 2252849, 2255146,
        2255147, 2255148, 2255149, 2257446, 2257447, 2257448, 2257449,
        2259573, 2259747, 2259748, 2259749, 2261871, 2261872, 2261873,
        2263992, 2263993, 2263994, 2266290, 2266291, 2266293, 2266294,
        2268590, 2268591, 2268592, 2268593, 2268594, 2330716, 2330717,
        2333014, 2333015, 2333016, 2333017, 2349755, 2352053, 2352054,
        2352055, 2352056, 2354352, 2354353, 2354354, 2354355, 2354356,
        2356117, 2356118, 2358415, 2358416, 2358417, 2358418, 2360715,
        2360716, 2360717, 2360718, 2365455, 2367753, 2367754, 2367755,
        2367756, 2370052, 2370053, 2370054, 2370055, 2370056, 2370057,
        2370510, 2372352, 2372353, 2372354, 2372356, 2372357, 2372808,
        2372809, 2372810, 2374653, 2374654, 2374655, 2374656, 2416115,
        2418413, 2418414, 2418415, 2439635, 2439636, 2439637, 2441933,
        2441934, 2441935, 2441936, 2441937, 2444232, 2444233, 2444234,
        2444235, 2444236, 2444237, 2446533, 2446534, 2446535, 2446536,
        2446537, 2466600, 2466601, 2468898, 2468899, 2468900, 2468901,
        2468902, 2471198, 2471199, 2471200, 2471201, 2471202, 2480807,
        2482281, 2483105, 2483106, 2483107, 2484579, 2484580, 2484581,
        2486879, 2486880, 2486881, 2517173, 2517174, 2517175, 2519471,
        2519472, 2519473, 2519474, 2519475, 2521772, 2521773, 2521774,
        2540044, 2540045, 2540046, 2540047, 2542343, 2542344, 2542345,
        2542346, 2542347, 2544643, 2544644, 2544645, 2544646, 2544647,
        2546943, 2546944, 2546945, 2546946, 2546947, 2549006, 2551304,
        2551305, 2551306, 2553896, 2556194, 2556195, 2556196, 2568537,
        2570835, 2570836, 2570837, 2628255, 2628256, 2628257, 2630553,
        2630554, 2630555, 2630556, 2630557, 2632854, 2632855, 2632856,
        2632857, 2664920, 2664921, 2667218, 2667219, 2667220, 2667221,
        2667222, 2669517, 2669518, 2669519, 2669520, 2669521, 2669522,
        2671590, 2671591, 2671592, 2671593, 2671594, 2671818, 2671819,
        2671820, 2671821, 2671822, 2673889, 2673890, 2673891, 2673892,
        2673893, 2673894, 2676189, 2676190, 2676191, 2676192, 2676193,
        2676194, 2678489, 2678490, 2678491, 2678492, 2678493, 2678494,
        2687250, 2687251, 2687252, 2687253, 2687254, 2689549, 2689550,
        2689551, 2689552, 2689553, 2689554, 2691848, 2691849, 2691850,
        2691851, 2691852, 2691853, 2691854, 2694149, 2694150, 2694151,
        2694153, 2694154, 2696450, 2696451, 2696452, 2700811, 2700812,
        2700813, 2700814, 2703110, 2703111, 2703113, 2703114, 2705410,
        2705411, 2705412, 2705413, 2705414, 2707710, 2707711, 2707712,
        2707713, 2707714, 2722490, 2722491, 2724788, 2724789, 2724790,
        2724791, 2727088, 2727089, 2727090, 2727091, 2735926, 2735927,
        2738224, 2738225, 2738226, 2738227, 2740524, 2740525, 2740526,
        2740527, 2751531, 2751532, 2751533, 2751534, 2753830, 2753831,
        2753833, 2753834, 2756130, 2756131, 2756132, 2756133, 2756134,
        2802472, 2802473, 2802474, 2804771, 2804772, 2804773, 2804774,
        2807070, 2807071, 2807073, 2807074, 2809370, 2809371, 2809372,
        2809373, 2809374, 2839551, 2841849, 2841850, 2841851, 2853309,
        2853310, 2853311, 2853312, 2855608, 2855609, 2855610, 2855611,
        2855612, 2857909, 2857910, 2857911, 2857912, 2915342, 2915343,
        2915344, 2915345, 2915346, 2917641, 2917642, 2917643, 2917645,
        2917646, 2919941, 2919942, 2919943, 2919944, 2919945, 2919946,
        2922241, 2922242, 2922243, 2922244, 2922245, 2922246, 2922568,
        2924866, 2924867, 2924868, 2924869, 2924870, 2927165, 2927166,
        2927167, 2927168, 2927169, 2927170, 2929466, 2929467, 2929468,
        2929469, 2929470, 2935918, 2938216, 2938217, 2938218, 2965916,
        2965917, 2965918, 2968214, 2968215, 2968216, 2968217, 2968218,
        2970515, 2970516, 2970517, 2970518, 2972157, 2972158, 2974455,
        2974456, 2974457, 2974458, 2981889, 2981890, 2981891, 2981892,
        2984188, 2984189, 2984190, 2984191, 2984192, 2986487, 2986488,
        2986489, 2986490, 2986491, 2986492, 2988787, 2988788, 2988789,
        2988790, 2988791, 2988792, 2991087, 2991088, 2991089, 2991090,
        2991091, 2991092, 2999973, 2999974, 3002271, 3002272, 3002273,
        3002274, 3009224, 3009225, 3009226, 3011522, 3011523, 3011524,
        3011525, 3011526, 3013822, 3013823, 3013824, 3013825, 3013826,
        3014190, 3015980, 3016488, 3016489, 3016490, 3016491, 3018278,
        3018279, 3018280, 3018281, 3018787, 3018788, 3018789, 3018790,
        3018791, 3020577, 3020578, 3020579, 3020580, 3020581, 3020776,
        3021088, 3021089, 3021090, 3021091, 3023074, 3023075, 3023076,
        3055781, 3055782, 3055783, 3058080, 3058081, 3058082, 3058083,
        3060380, 3060381, 3060382, 3060383, 3078834, 3078835, 3078836,
        3078837, 3078838, 3081133, 3081134, 3081135, 3081136, 3081137,
        3081138, 3083434, 3083435, 3083436, 3083437, 3083438, 3092594,
        3092595, 3092596, 3094893, 3094894, 3094895, 3094896, 3096607,
        3096608, 3096609, 3097193, 3097194, 3097195, 3097196, 3098906,
        3098907, 3098908, 3098909, 3101205, 3101206, 3101207, 3101208,
        3101209, 3105858, 3105859, 3105860, 3108157, 3108158, 3108159,
        3108160, 3110456, 3110457, 3110458, 3110459, 3110460, 3117216,
        3119514, 3119515, 3119516, 3121814, 3121815, 3121816, 3135518,
        3135519, 3135520, 3137817, 3137818, 3137819, 3137820, 3140117,
        3140118, 3140119, 3152147, 3152148, 3154445, 3154446, 3154447,
        3154448, 3156746, 3156747, 3156748, 3163471, 3165375, 3165376,
        3165377, 3165769, 3165770, 3165771, 3167673, 3167674, 3167676,
        3167677, 3169973, 3169974, 3169975, 3169976, 3169977, 3175516,
        3175517, 3175518, 3175519, 3177815, 3177816, 3177818, 3177819,
        3177820, 3180115, 3180116, 3180117, 3180118, 3180119, 3180120,
        3182416, 3182417, 3182418, 3182419, 3214631, 3214632, 3214633,
        3216929, 3216930, 3216931, 3216932, 3216933, 3219230, 3219231,
        3219232, 3219233, 3239304, 3239305, 3239306, 3241603, 3241604,
        3241605, 3241606, 3241607, 3243902, 3243903, 3243904, 3243906,
        3243907, 3246202, 3246203, 3246204, 3246205, 3246206, 3248554,
        3248555, 3248556, 3250853, 3250854, 3250855, 3250856, 3253152,
        3253153, 3253154, 3253155, 3253156, 3276803, 3279101, 3279102,
        3279103, 3290560, 3292858, 3292859, 3292860, 3305832, 3305833,
        3305834, 3308130, 3308131, 3308132, 3308133, 3308134, 3310430,
        3310431, 3310432, 3310433, 3328989, 3331287, 3331288, 3331289,
        3333586, 3333587, 3333588, 3333589, 3375050, 3375051, 3375052,
        3377348, 3377349, 3377350, 3377351, 3377352, 3379648, 3379649,
        3379650, 3379651, 3379652, 3381949, 3381950, 3381951, 3398331,
        3400629, 3400630, 3400631, 3414020, 3416318, 3416319, 3416320,
        3416602, 3418900, 3418901, 3418902, 3443879, 3443880, 3443881,
        3446178, 3446179, 3446180, 3446181, 3448478, 3448479, 3448480,
        3448903, 3450833, 3451201, 3451202, 3451203, 3453131, 3453132,
        3453133, 3457782, 3457783, 3457784, 3457785, 3460081, 3460082,
        3460083, 3460084, 3460085, 3462381, 3462382, 3462383, 3462384,
        3462385, 3543099, 3545397, 3545398, 3545399, 3575399, 3575400,
        3575401, 3577698, 3577699, 3577700, 3577701, 3577702, 3579998,
        3579999, 3580000, 3580001, 3580002, 3582299, 3582300, 3582301,
        3595828, 3595829, 3595830, 3598127, 3598128, 3598129, 3598130,
        3600427, 3600428, 3600429, 3600430, 3635083, 3637381, 3637382,
        3637383, 3653626, 3655924, 3655925, 3655926, 3658224, 3658225,
        3658226, 3708798, 3708799, 3711096, 3711097, 3711098, 3711099,
        3722272, 3722273, 3724570, 3724571, 3724572, 3724573, 3761385,
        3763683, 3763684, 3763685, 3807591, 3807592, 3809889, 3809890,
        3809891, 3809892]
#cdef cnp.uint8_t[:]  CCP4_PCK_MASK = numpy.array([0, 1, 3, 7, 15, 31, 63, 127, 255], dtype=numpy.uint8)

cdef extern from "ccp4_pack.h":
    void* mar345_read_data_string(char *instream, int ocount, int dim1, int dim2) nogil
    void pack_wordimage_c(short int*, int , int , char*) nogil
    void* ccp4_unpack_string   (void *, void *, size_t, size_t, size_t) nogil
    void* ccp4_unpack_v2_string(void *, void *, size_t, size_t, size_t) nogil
cdef int PACK_SIZE_HIGH = 8


@cython.boundscheck(False)
def compress_pck(image not None, bint use_CCP4=True):
    """
    :param image: numpy array as input
    :param use_CCP4: use the former LGPL implementation provided by CCP4
    :return: binary stream
    """
    cdef:
        cnp.uint32_t  size, dim0, dim1, i, j, 
        int fd, ret
        char* name
        cnp.int16_t[::1] data, raw
        
    assert image.ndim == 2, "Input image shape is 2D"
    size = image.size
    dim0 = image.shape[0]
    dim1 = image.shape[1]
    data = numpy.ascontiguousarray(image.ravel(), dtype=numpy.int16)
    if use_CCP4:
        (fd, fname) = tempfile.mkstemp()
        fname = fname.encode("ASCII")
        name = <char*> fname
        with nogil:
            pack_wordimage_c(<short int *> &data[0], dim1, dim0, name)
        with open(name, "rb") as f:
            f.seek(0)
            output = f.read()
        os.close(fd)
        os.unlink(fname)
    else:
        output = b"\nCCP4 packed image, X: %04d, Y: %04d\n" % (dim1, dim0)
        raw = precomp(data, dim1)
        cont = pack_image(raw, False)
#         print("position: %s offset: %s, allocate: %s" % (cont.position, cont.offset, cont.allocated))
        output += cont.get().tostring()
    return output


@cython.boundscheck(False)
@cython.cdivision(True)
def uncompress_pck(bytes raw not None, dim1=None, dim2=None, overflowPix=None, version=None, normal_start=None, swap_needed=None, bint use_CCP4=False):
    """
    Unpack a mar345 compressed image

    :param raw: input string (bytes in python3)
    :param dim1,dim2: optional parameters size
    :param overflowPix: optional parameters: number of overflowed pixels
    :param version: PCK version 1 or 2
    :param normal_start: position of the normal value section (can be auto-guessed)
    :param swap_needed: set to True when reading data from a foreign endianness (little on big or big on little)
    @return : ndarray of 2D with the right size
    """
    cdef:
        int cdimx, cdimy, chigh, cversion, records, normal_offset, lenkey, i, stop, idx, value
        cnp.uint32_t[:, ::1] data
        cnp.uint8_t[::1] instream
        cnp.int32_t[::1] unpacked
        cnp.int32_t[:, ::1] overflow_data  # handles overflows
        void* out
    end = None
    key1 = b"CCP4 packed image, X: "
    key2 = b"CCP4 packed image V2, X: "

    if (dim1 is None) or (dim2 is None) or \
       (version not in [1, 2]) or \
       (version is None) or \
       (normal_start is None):
        start = raw.find(key2)
        key = key2
        cversion = 2
        if start == -1:
            start = raw.find(key1)
            key = key1
            cversion = 1
        lenkey = len(key)
        start = raw.index(key) + lenkey
        sizes = raw[start:start + 13]
        cdimx = < int > int(sizes[:4])
        cdimy = < int > int(sizes[-4:])
        normal_offset = start + 13
    else:
        cdimx = < int > dim1
        cdimy = < int > dim2
        cversion = <int> version
        normal_offset = <int> normal_start
        if cversion == 1:
            lenkey = len(key1)
        else:
            lenkey = len(key2)
    if cversion not in [1, 2]:
        raise RuntimeError("Cannot determine the compression scheme for PCK compression (either version 1 or 2)")
    if (overflowPix is None) and (overflowPix is not False):
        end = raw.find("END OF HEADER")
        start = raw[:end].find("HIGH")
        hiLine = raw[start:end]
        hiLine = hiLine.split("\n")[0]
        word = hiLine.split()
        if len(word) > 1:
            chigh = int(word[1])
        else:
            logger.warning("Error while looking for overflowed pixels in line %s", hiLine.strip())
            chigh = 0
    else:
        chigh = < int > overflowPix

    instream = numpy.fromstring(raw[normal_offset:].lstrip(), dtype=numpy.uint8)

    if use_CCP4:
        data = numpy.empty((cdimy, cdimx), dtype=numpy.uint32)   
        with nogil:
            ################################################################################
            #      rely to whichever version of ccp4_unpack is appropriate
            ################################################################################
            if cversion == 1:
                ccp4_unpack_string(&data[0,0], &instream[0], cdimx, cdimy, 0)
            else:
                # cversion == 2:
                ccp4_unpack_v2_string(&data[0,0], &instream[0], cdimx, cdimy, 0)
    else:
        unpacked = postdec(unpack_pck(instream, cdimx, cdimy).get1d(), cdimx)
        data = numpy.ascontiguousarray(unpacked, numpy.uint32).reshape((cdimy, cdimx))
#         data = numpy.ascontiguousarray(unpack_pck(instream, cdimx, cdimy).get(), numpy.uint32)

    if chigh > 0:
        ################################################################################
        # handle overflows: Each record is 8 overflow of 2x32bits integers
        ################################################################################
        records = (chigh + PACK_SIZE_HIGH - 1) // PACK_SIZE_HIGH
        stop = normal_offset - lenkey - 14
        odata = numpy.fromstring(raw[stop - 64 * records: stop], dtype=numpy.int32)
        if swap_needed:
            odata.byteswap(True)
        overflow_data = odata.reshape((-1, 2))
        for i in range(overflow_data.shape[0]): 
            idx = overflow_data[i, 0] - 1     # indexes are even values (-1 because 1 based counting)
            value = overflow_data[i, 1]  # values are odd values
            if (idx >= 0) and (idx < cdimx * cdimy):
                data[idx // cdimx, idx % cdimx] = <cnp.uint32_t> value
    return numpy.asarray(data)


################################################################################
# Re-Implementation of the pck compression/decompression 
################################################################################

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
cpdef inline any_int_t[::1] precomp(any_int_t[::1] img, int width):
    """Pre-compression by subtracting the average value of the four neighbours
    
    Actually it looks a bit more complicated:
    
    * there comes the +2 from ?
    * the first element remains untouched
    * elements of the first line (+ fist of second) use only former element  

    
    JPA, the original author wrote:
    Compression is achieved by first calculating the differences between every
    pixel and the truncated value of four of its neighbours. For example:
    the difference for a pixel at img[x, y] is:

    comp[y, x] =  img[y, x] - (img[y-1, x-1] + img[y-1, x] + img[y-1, x+1] + img[y, x-1]) / 4
    """
    cdef: 
        cnp.uint32_t size, i
        any_int_t[::1] comp
        any_int_t last, cur, im0, im1, im2
    size = img.size
    comp = numpy.zeros_like(img)
    
    # First pixel
    comp[0] = last = im0 = img[0]
    im1 = img[1]
    im2 = img[2]
    # First line (+ 1 pixel)
    for i in range(1, width + 1):
        cur = img[i]
        comp[i] = cur - last
        last = cur
    
    # Rest of the image
    
    for i in range(width + 1, size):
        cur = img[i]
        comp[i] = cur - (last + im0 + im1 + im2 + 2) // 4
        last = cur
        im0 = im1
        im1 = im2
        im2 = img[i - width + 2]

    return comp


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
cpdef inline any_int_t[::1] postdec(any_int_t[::1] comp, int width):
    """Post decompression by adding the average value of the four neighbours
    
    Actually it looks a bit more complicated:
    
    * there comes the +2 from ?
    * the first element remains untouched
    * elements of the first line (+ fist of second) use only former element  
    
    JPA , the original author wrote:
    Compression is achieved by first calculating the differences between every
    pixel and the truncated value of four of its neighbours. For example:
    the difference for a pixel at img[x, y] is:

    comp[y, x] =  img[y, x] - (img[y-1, x-1] + img[y-1, x] + img[y-1, x+1] + img[y, x-1]) / 4
    """
    cdef: 
        cnp.uint32_t size, i
        any_int_t[::1] img
        any_int_t last, cur, fl0, fl1, fl2
    size = comp.size
    img = numpy.zeros_like(comp)
    
    # First pixel
    img[0] = last = comp[0] 
    
    # First line (+ 1 pixel)
    for i in range(1, width + 1):
        img[i] = cur = comp[i] + last  
        last = cur
    
    # Rest of the image: not parallel in this case
    fl0 = img[0]
    fl1 = img[1]
    fl2 = img[2]
    for i in range(width + 1, size):
        img[i] = cur = comp[i] + (last + fl0 + fl1 + fl2 + 2) // 4
        last = cur
        fl0 = fl1
        fl1 = fl2
        fl2 = img[i - width + 2]

    return img
 

################################################################################
# Re-Implementation of the pck compression stuff 
################################################################################

    
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
cpdef inline int calc_nb_bits(any_int_t[::1] data, cnp.uint32_t start, cnp.uint32_t stop):
    """Calculate the number of bits needed to encode the data
    
    :param data: input data, probably slices of a larger array
    :param start: start position
    :param stop: stop position
    :return: the needed number of bits to store the values
    
    Comment from JPA:
    .................
    
    Returns the number of bits necessary to encode the longword-array 'chunk'
    of size 'n' The size in bits of one encoded element can be 0, 4, 5, 6, 7,
    8, 16 or 32.
     """ 
    cdef:
        cnp.uint32_t size, maxsize, i, abs_data
        any_int_t read_data
    
    size = stop - start
    maxsize = 0
    for i in range(start, stop):
        read_data = data[i]
        abs_data = - read_data if read_data < 0 else read_data
#         abs_data = abs(read_data) 
        if abs_data > maxsize:
            maxsize = abs_data        
    if maxsize == 0:
        return 0
    elif maxsize < 8:
        return size * 4
    elif maxsize < 16:
        return size * 5
    elif maxsize < 32:
        return size * 6
    elif maxsize < 64:
        return size * 7
    elif maxsize < 128:
        return size * 8
    elif maxsize < 32768:
        return size * 16
    else:
        return size * 32


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
def pack_image(img, bint do_precomp=True):
    """Pack an image into a binary compressed block
    
    :param img: input image as numpy.int16
    :param do_precomp: perform the subtraction to the 4 neighbours's average. False is for testing the packing only 
    :return: 1D array of numpy.int8  
    
    JPA wrote:
    ..........
    Pack image 'img', containing 'x * y' WORD-sized pixels into byte-stream
    """
    cdef:
        cnp.uint32_t nrow, ncol, size, stream_size
        cnp.int16_t[::1] input_image, raw 
        PackContainer container
        cnp.uint32_t i, position
        cnp.uint32_t nb_val_packed
        cnp.uint32_t current_block_size, next_bock_size
    
    if do_precomp:
        assert len(img.shape) == 2
        nrow = img.shape[0]
        ncol = img.shape[1]
        input_image = numpy.ascontiguousarray(img, dtype=numpy.int16).ravel()
        # pre compression: subtract the average of the 4 neighbours
        raw = precomp(input_image, ncol)
        size = nrow * ncol
    else:
        raw = numpy.ascontiguousarray(img, dtype=numpy.int16).ravel()
        size = raw.size

    # allocation of the output buffer
    container = PackContainer(size)
    position = 0
    while position < size:
        nb_val_packed = 1
        current_block_size = calc_nb_bits(raw, position, position + nb_val_packed)
        while ((position + nb_val_packed) < size) and (nb_val_packed < 128):
            if (position + 2 * nb_val_packed) < size:
                next_bock_size = calc_nb_bits(raw, position + nb_val_packed, position + 2 * nb_val_packed)
            else:
                break
            if 2 * max(current_block_size, next_bock_size) < (current_block_size + next_bock_size + CCP4_PCK_BLOCK_HEADER_LENGTH):
                nb_val_packed *= 2
                current_block_size = 2 * max(current_block_size, next_bock_size)
            else:
                break
        container.append(raw, position, nb_val_packed, current_block_size)
        position += nb_val_packed
                         
    return container


cdef class PackContainer:
    cdef: 
        readonly cnp.uint32_t position, offset, allocated
        cnp.uint8_t[::1] data 
        
    def __cinit__(self, cnp.uint32_t size=4096):
        """Constructor of the class
        
        :param size: start size of the array
        """
        self.position = 0
        self.offset = 0
        self.allocated = size
        self.data = numpy.zeros(self.allocated, dtype=numpy.uint8)
    
    def __dealloc__(self):
        self.data = None
        
    def get(self):
        """retrieve the populated array"""
        if self.offset:
            end = self.position + 1
        else:
            end = self.position
        return numpy.asarray(self.data[:end])
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    @cython.initializedcheck(False)
    cpdef append(self, cnp.int16_t[::1] data, cnp.uint32_t position, cnp.uint32_t nb_val, cnp.uint32_t block_size): 
        """Append a block of data[position: position+nb_val] to the compressed
        stream. Only the most significant bits are takes.
        
        :param data: input uncompressed image as 1D array
        :param position: start position of reading of the image
        :param nb_val: number of value from data to pack in the block
        :param block_size: number of bits for the whole block
        
        The 6 bits header is managed here as well as the stream resizing.
        """
        cdef:
            cnp.uint32_t offset, index, i, bit_per_val, nb_bytes
            cnp.uint64_t tmp, tostore, mask
            cnp.int64_t topack
            
        bit_per_val = block_size // nb_val
        
        # realloc memory if needed
        nb_bytes = (CCP4_PCK_BLOCK_HEADER_LENGTH + block_size + 7) // 8
        if self.position + nb_bytes >= self.allocated:
            self.allocated *= 2
            new_stream = numpy.zeros(self.allocated, dtype=numpy.uint8)
            if self.offset:
                new_stream[:self.position + 1] = self.data[:self.position + 1]
            else:
                new_stream[:self.position] = self.data[:self.position]
            self.data = new_stream
        
        if self.offset == 0:
            tmp = 0
        else:
            tmp = self.data[self.position]
        
        # append 6 bits of header
        tmp |= pack_nb_val(nb_val, bit_per_val) << self.offset
        self.offset += CCP4_PCK_BLOCK_HEADER_LENGTH
        self.data[self.position] = tmp & (255)
        if self.offset >= 8:
            self.position += 1
            self.offset -= 8 
            self.data[self.position] = (tmp >> 8) & (255)

        if bit_per_val == 0:
            return
        # now pack every value in input stream" 
        for i in range(nb_val):
            topack = data[position + i]

            mask = ((1 << (bit_per_val - 1)) - 1)
            tmp = (topack & mask)
            if topack < 0: 
                # handle the sign
                tmp |= 1 << (bit_per_val - 1)
             
            # read last position
            if self.offset == 0:
                tostore = 0
            else:
                tostore = self.data[self.position]     
            
            tostore |= tmp << self.offset
            self.offset += bit_per_val

            # Update the array
            self.data[self.position] = tostore & (255)
            while self.offset >= 8:
                tostore = tostore >> 8
                self.offset -= 8
                self.position += 1
                self.data[self.position] = tostore & (255)
            

cpdef inline cnp.uint8_t pack_nb_val(cnp.uint8_t nb_val, cnp.uint8_t value_size):
    """Calculate the header to be stored in 6 bits
    
    :param nb_val: number of values to be stored: must be a power of 2 <=128
    :param value_size: can be 0, 4, 5, 6, 7, 8, 16 or 32, the number of bits per value
    :return: the header as an unsigned char 
    """
    cdef:
        cnp.uint32_t value, i
        
    value = 0 
    for i in range(8):
        if (nb_val >> i) == 1:
            value |= i
            break
    value |= (CCP4_BITSIZE[value_size]) << (CCP4_PCK_BLOCK_HEADER_LENGTH >> 1) 
    # should be 6/2 = 3
    return value


################################################################################
# Re-Implementation of the pck uncompression stuff 
################################################################################
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
cpdef UnpackContainer unpack_pck(cnp.uint8_t[::1] stream, int ncol, int nrow):
    """Unpack the raw stream and return the image
    V1 only for now, V2 may be added later
    
    :param stream: raw input stream
    :param ncol: number of columns in the image (i.e width)
    :param nrow: number if rows in the image (i.e. height)
    :return: Container with decompressed image
    """
    cdef: 
        cnp.uint32_t offset       # Number of bit to offset in the current byte
        cnp.uint32_t pos, end_pos # current position and last position of block  in byte stream
        cnp.uint32_t size         # size of the input stream
        int value, next           # integer values 
        cnp.uint32_t nb_val_packed, nb_bit_per_val, nb_bit_in_block
        UnpackContainer cont      # Container with unpacked data 

    cont = UnpackContainer(ncol, nrow)
    size = stream.size
    
    # Luckily we start at byte boundary
    offset = 0
    pos = 0
    
    while pos < (size) and cont.position < (cont.size):
        value = stream[pos]
        if offset > (8 - CCP4_PCK_BLOCK_HEADER_LENGTH):
            # wrap around
            pos += 1
            next = stream[pos]
            value |= next << 8
            value = value >> offset
            offset += CCP4_PCK_BLOCK_HEADER_LENGTH - 8
        elif offset == (8 - CCP4_PCK_BLOCK_HEADER_LENGTH):
            # Exactly on the boundary
            value = value >> offset
            pos += 1
            offset = 0
        else:
            # stay in same byte
            value = value >> offset
            offset += CCP4_PCK_BLOCK_HEADER_LENGTH
        
        # we use 7 as mask: decimal value of 111 
        nb_val_packed = 1 << (value & 7)   # move from offset, read 3 lsb, take the power of 2
        nb_bit_per_val = CCP4_PCK_BIT_COUNT[(value >> 3) & 7] # read 3 next bits, search in LUT for the size of each element in block

        if nb_bit_per_val == 0:
            cont.set_zero(nb_val_packed)
        else:
            nb_bit_in_block = nb_bit_per_val * nb_val_packed
            cont.unpack(stream, pos, offset, nb_val_packed, nb_bit_per_val)
            offset += nb_bit_in_block
            pos += offset // 8
            offset %= 8
    return cont


cdef class UnpackContainer:
    cdef:
        readonly cnp.uint32_t nrow, ncol, position, size
        cnp.int32_t[::1] data 
    
    def __cinit__(self, int ncol, int nrow):
        self.nrow = nrow
        self.ncol = ncol
        self.size = nrow * ncol
        self.data = numpy.zeros(self.size, dtype=numpy.int32)
        self.position = 0
    
    def __dealloc__(self):
        self.data = None
        
    def get(self):
        """retrieve the populated array"""
        return numpy.asarray(self.data).reshape((self.nrow, self.ncol))

    cpdef cnp.int32_t[::1] get1d(self):
        """retrieve the populated array"""
        return self.data

    cpdef set_zero(self, int number):
        "set so many zeros"
        self.position += number

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    @cython.initializedcheck(False)
    cpdef unpack(self, cnp.uint8_t[::1] stream, cnp.uint32_t pos, cnp.uint32_t offset, cnp.uint32_t nb_value, cnp.uint32_t value_size):
        """unpack a block on data, all the same size
        
        :param stream: input stream, already sliced
        :param offset: number of bits of offset, at the begining of the stream 
        :param nb_value: number of values to unpack
        :param value_size: number of bits of each value
        """
        cdef:
            cnp.uint32_t i, j        # simple counters
            cnp.uint32_t new_offset  # position after read
            cnp.int64_t cur, tmp2    # value to be stored
            cnp.uint64_t tmp         # under contruction: needs to be unsigned
            int to_read              # number of bytes to read

        cur = 0
        for i in range(nb_value):

            # read as many bytes as needed and unpack them to tmp variable
            
            tmp = stream[pos] >> offset
            
            new_offset = value_size + offset 
            to_read = (new_offset + 7) // 8
            
            for j in range(1, to_read + 1):
                tmp |= (stream[pos + j]) << (8 * j - offset)
                
            # Remove the lsb of tmp up to offset and apply the mask
             
            cur = tmp & ((1 << (value_size - 0)) - 1)
            
            # change sign if most significant bit is 1
#             if tmp & (1 << (value_size - 1)): # retreive the bit of sign
#                 tmp2 = cur ^ (1 << value_size - 1) +1  # xor with 1111 to get the positive value
#                 cur = -tmp2  
            if tmp & (1 << (value_size - 1)):
                cur |= (<cnp.int64_t> -1) << (value_size - 1)
#                 cur = (cur) 

            if self.position in bad_pixels:
                print("P: %s p: %s o: %s, nv: %s, vs: %s  tmp: %s, %s cur %s, raw: %s"%(self.position, pos, offset, nb_value, value_size,  bin(tmp), tmp, cur,  " ".join([bin(ii) for ii in stream[pos:pos+to_read + 1]])))

            # Update the storage
            self.data[self.position] = cur
            self.position += 1
            
            
            # Update the position in the array
            pos = pos + new_offset // 8
            offset = new_offset % 8    
