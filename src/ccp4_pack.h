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
#ifndef _MSC_VER
#include <stdint.h> 
#else
#include "stdint.h" 
#endif
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>


#define CCP4_PCK_BLOCK_HEADER_LENGTH 6
#define CCP4_PCK_BLOCK_HEADER_LENGTH_V2 8
/*array translating the number of errors per block*/
static unsigned int CCP4_PCK_ERR_COUNT[] = {1,2,4,8,16,32,64,128};
/*array translating the number of bits per error*/
static unsigned int CCP4_PCK_BIT_COUNT[]= {0,4,5,6,7,8,16,32};
/*array translating the number of errors per block - can use shifts as well actually*/
static unsigned int CCP4_PCK_ERR_COUNT_V2[] = {1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768};
/*array translating the number of bits per error*/
static unsigned int CCP4_PCK_BIT_COUNT_V2[]= {0,4,5,6,7,8,9,10,11,12,13,14,15,16,32};

static const unsigned char CCP4_PCK_MASK[]={0x00,
  0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF};

static const unsigned int CCP4_PCK_MASK_16[]={0x00,
  0x01,  0x03,  0x07,  0x0F,  0x1F,   0x3F,   0x7F,   0xFF,
  0x1FF, 0x3FF, 0x7FF, 0xFFF, 0x1FFF, 0x3FFF, 0x7FFF, 0xFFFF};

static const unsigned long CCP4_PCK_MASK_32[]={0x00,
  0x01,      0x03,      0x07,      0x0F,      0x1F,       0x3F,       0x7F,       0xFF,
  0x1FF,     0x3FF,     0x7FF,     0xFFF,     0x1FFF,     0x3FFF,     0x7FFF,     0xFFFF,
  0x1FFFF,   0x3FFFF,   0x7FFFF,   0xFFFFF,   0x1FFFFF,   0x3FFFFF,   0x7FFFFF,   0xFFFFFF,
  0x1FFFFFF, 0x3FFFFFF, 0x7FFFFFF, 0xFFFFFFF, 0x1FFFFFFF, 0x3FFFFFFF, 0x7FFFFFFF, 0xFFFFFFFF};

#define pfail_nonzero(a) if ((a)) return NULL;

void *mar345_read_data(FILE *file, int ocount, int dim1, int dim2);
void *mar345_read_data_string(char *instring, int ocount, int dim1, int dim2);
void *ccp4_unpack(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);
void *ccp4_unpack_v2(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);
void *ccp4_unpack_string(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);
void *ccp4_unpack_v2_string(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);

void pack_wordimage_c(short int *img, int x, int y, char *filename);
