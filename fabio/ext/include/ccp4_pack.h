/* Fabio Mar345 ccp4_pack decompressor
   Copyright (C) 2007-2009 Henning O. Sorensen & Erik Knudsen

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 3 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General
   Public License along with this library; if not, write to the
   Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301 USA */

#ifndef CPP4_PACK_H
#define CPP4_PACK_H

#ifndef _MSC_VER
#include <stdint.h>
#else
#include "msvc\\stdint.h"
#endif

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>


#define CCP4_PCK_BLOCK_HEADER_LENGTH 6
#define CCP4_PCK_BLOCK_HEADER_LENGTH_V2 8


#define PACKIDENTIFIER "\nCCP4 packed image, X: %04d, Y: %04d\n"
// This string defines the start of a packed image. An image file is scanned
//   until this string is encountered, the size of the unpacked image is
//   determined from the values of X and Y (which are written out as formatted
//   ascii numbers), and the packed image is expected to start immediately after
//   the null-character ending the string.

#define V2IDENTIFIER "\nCCP4 packed image V2, X: %04d, Y: %04d\n"
// This string defines the start of a packed image. An image file is scanned
//   until this string is encountered, the size of the unpacked image is
//   determined from the values of X and Y (which are written out as formatted
//   ascii numbers), and the packed image is expected to start immediately after
//   the null-character ending the string.

#define PACKBUFSIZ BUFSIZ
// Size of internal buffer in which the packed array is stored during transit
//   form an unpacked image to a packed image on disk. It is set to the size
//   used by the buffered io-routines given in <stdio.h>, but it could be
//   anything.

#define DIFFBUFSIZ 16384L
// Size of the internal buffer in which the differences between neighbouring
//   pixels are stored prior to compression. The image is therefore compressed
//   in DIFFBUFSIZ chunks. Decompression does not need to know what DIFFBUFSIZ
//   was when the image was compressed. By increasing this value, the image
//   can be compressed into a packed image which is a few bytes smaller. Do
//   not decrease the value of DIFFBUFSIZ below 128L.


#define pfail_nonzero(a) if ((a)) return NULL;
#define max(x, y) (((x) > (y)) ? (x) : (y))
#define min(x, y) (((x) < (y)) ? (x) : (y))

#define shift_left(x, n)  (((x) & CCP4_PCK_MASK_32[32 - (n)]) << (n))
#define shift_right(x, n) (((x) >> (n)) & CCP4_PCK_MASK_32[32 - (n)])
// This macro is included because the C standard does not properly define a
//   left shift: on some machines the bits which are pushed out at the left are
//   popped back in at the right. By masking, the macro prevents this behaviour.
//   If you are sure that your machine does not pops bits back in, you can speed
//   up the code insignificantly by taking out the masking.

// read data from a file
void* mar345_read_data(FILE *file, int ocount, int dim1, int dim2);
// read data from a stream
void* mar345_read_data_string(char *instring, int ocount, int dim1, int dim2);

// unpack the given data
void* ccp4_unpack(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);
// unpack the given data
void* ccp4_unpack_v2(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);
// unpack the given data
void* ccp4_unpack_string(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);
// unpack the given data
void* ccp4_unpack_v2_string(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);

void pack_wordimage_c(short int *img, int x, int y, char *filename);

#endif // CPP4_PACK_H
