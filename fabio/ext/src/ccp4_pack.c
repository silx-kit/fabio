/* Fabio Mar345 ccp4_pack decompressor
   Copyright (C) 2007-2009 Henning O. Sorensen & Erik Knudsen
                 2012 ESRF

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

/* part of this code is freely adaped from pack_c.c from CCP4 distribution
 * (which is also LGPL). The original author is Jan Pieter Abrahams
 *
						    jpa@mrc-lmb.cam.ac.uk

   This file contains functions capable of compressing and decompressing
   images. It is especially suited for X-ray diffraction patterns, or other
   image formats in which orthogonal pixels contain "grey-levels" and
   vary smoothly accross the image. Clean images measured by a MAR-research
   image plate scanner containing two bytes per pixel can be compressed by
   a factor of 3.5 to 4.5 .

   Since the images are encoded in a byte-stream, there should be no problem
   concerning big- or little ended machines: both will produce an identical
   packed image.

   Compression is achieved by first calculating the differences between every
   pixel and the truncated value of four of its neighbours. For example:
   the difference for a pixel at img[x, y] is:

     img[x, y] - (int) (img[x-1, y-1] +
                        img[x-1, y] +
			img[x-1, y+1] +
			img[x, y-1]) / 4

   After calculating the differences, they are encoded in a packed array. A
   packed array consists of consequitive chunks which have the following format:
   - Three bits containing the logarithm base 2 of the number of pixels encoded
     in the chunk.
   - Three bits defining the number of bits used to encode one element of the
     chunk. The value of these three bits is used as index in a lookup table
     to get the actual number of bits of the elements of the chunk.
        Note: in version 2, there are four bits in this position!! This allows
              more efficient packing of synchrotron data! The routines in this
	      sourcefile are backwards compatible.
	                                             JPA, 26 June 1995
   - The truncated pixel differences.

   To compress an image, call pack_wordimage_c() or pack_longimage_c(). These
   will append the packed image to any header information already written to
   disk (take care that the file containing this information is closed before
   calling). To decompress an image, call readpack_word_c() or
   readpack_long_c(). These functions will find the start of the packed image
   themselves, irrespective of the header format.

                                            Jan Pieter Abrahams, 6 Jan 1993   */

#include <ccp4_pack.h>
#include "string.h"
#include "assert.h"

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



void *mar345_read_data_string(char *instring, int ocount, int dim1, int dim2){
	// first process overflow bytes - for now we just ignore them
	// * these are stored in 64 byte records
	int orecords=(int)(ocount/8.0+0.875);
	int *odata,x,y,version=0;
	char *c,cbuffer[64]="";
	char *t_;
	unsigned int *unpacked_array;

	odata=(int*)malloc(64*8*orecords);
	if (!odata)
	  return NULL;
	memcpy(odata, instring, 64*orecords);
	t_ = instring + (64*orecords);
	// there is no stdout in a gui, sorry

	// now after they have been read find the CCP4.....string and compare to dim1
	c=cbuffer;
	while((*c)!=EOF){

	  if (c==cbuffer+63){
	   c=cbuffer;
	  }

	  *c = (char) *t_;
	  t_++;

	  // set the next character to a \0 so the string is always terminated
	  *(c+1)='\0';

	  if (*c=='\n'){
		// check for the CCP- string
		x=y=0;
		sscanf(cbuffer,"CCP4 packed image, X: %04d, Y: %04d", &x,&y);
		if (x==dim1 || y ==dim2){
		  version=1;
		  break;
		}
		x=y=0;
		sscanf(cbuffer,"CCP4 packed image V2, X: %04d, Y: %04d", &x,&y);
		if (x==dim1 || y ==dim2){
		  version=2;
		  break;
		}
		c=cbuffer;
	  } else
		c++;
	}
	// allocate memory for the arrays
	unpacked_array=(unsigned int*) malloc(sizeof(unsigned int)*dim1*dim2);
	if (!unpacked_array)
	  return NULL;
	// relay to whichever version of ccp4_unpack is appropriate

	switch(version){
	  case 1:
		ccp4_unpack_string(unpacked_array,(void*)t_,dim1,dim2,0);
		break;
	  case 2:
		ccp4_unpack_v2_string(unpacked_array,(void*)t_,dim1,dim2,0);
		break;
	  default:
		return NULL;
	}

	// handle overflows
	while (ocount>0){
	  unsigned int adress,value;
	  adress=odata[2*ocount-2];
	  if (adress){
		value=odata[2*ocount-1];
		// adresses start at 1
		unpacked_array[adress-1]=value;
	  }
	  ocount--;
	}
	return unpacked_array;
}

// Henri start modif
// void* mar345_read_data_2(const char* pFilePath, int ocount, int dim1, int dim2){
//   FILE* f = fopen(pFilePath, "r");
//   assert(f);
//   if(!f){
//     printf("can't find file %s. Unable to read mar345 data\n", pFilePath);
//     return NULL;
//   }

//   void* res = mar345_read_data(f, ocount, dim1, dim2);
//   fclose(f);
//   return res;
// }
// Henri end modif

// *unpack a new style mar345 image a'la what is done in CBFlib
// * assumes the file is already positioned after the ascii header
// * Perhaps the positioning should be done here as well.
 
void * mar345_read_data(FILE *file, int ocount, int dim1, int dim2){
  // first process overflow bytes - for now we just ignore them
  // these are stored in 64 byte records
  int orecords=(int)(ocount/8.0+0.875);
  int *odata,x,y,version=0;
  char *c,cbuffer[64]="";
  unsigned int *unpacked_array;
  
  odata=(int*)malloc(64*8*orecords);
  if (!odata)
    return NULL;
  pfail_nonzero (orecords-fread(odata,64,orecords,file));
  //  there is no stdout in a gui, sorry
   
  // now after they have been read find the CCP4.....string and compare to dim1
  c=cbuffer;
  while((*c)!=EOF){
    
    if (c==cbuffer+63){
     c=cbuffer;
    } 
    
    *c=(char)getc(file);
    // set the next character to a \0 so the string is always terminated
    *(c+1)='\0';
    
    if (*c=='\n'){
      // check for the CCP- string
      x=y=0;
      sscanf(cbuffer,"CCP4 packed image, X: %04d, Y: %04d", &x,&y);
      if (x==dim1 || y ==dim2){
        version=1;
        break;
      }
      x=y=0;
      sscanf(cbuffer,"CCP4 packed image V2, X: %04d, Y: %04d", &x,&y);
      if (x==dim1 || y ==dim2){
        version=2;
        break;
      }
      c=cbuffer;
    } else
      c++;
  }
   // allocate memory for the arrays
  unpacked_array=(unsigned int*) malloc(sizeof(unsigned int)*dim1*dim2);
  if (!unpacked_array)
    return NULL;
  // relay to whichever version of ccp4_unpack is appropriate
  switch(version){
    case 1:
      ccp4_unpack(unpacked_array,(void*)file,dim1,dim2,0);
      break;
    case 2:
      ccp4_unpack_v2(unpacked_array,(void*)file,dim1,dim2,0);
      break;
    default:
      return NULL;
  }
  
  // handle overflows
  while (ocount>0){
    unsigned int adress,value;
    adress=odata[2*ocount-2];
    if (adress){
      value=odata[2*ocount-1];
      // adresses start at 1
      unpacked_array[adress-1]=value;
    }
    ocount--;
  }
  return unpacked_array;
}

// *unpack a ccp4-style packed array into the memory location pointed to by unpacked_array
// * if this is null allocate memory and return a pointer to it
// * \return NULL if unsuccessful
// * TODO change this to read directly from the FILE to not waste memory 
void * ccp4_unpack(
    void *unpacked_array,
    void *packed,
    size_t dim1,size_t dim2,
    size_t max_num_int
    ){

  uint8_t t_,t2,_conv;
  int err_val,bit_offset,num_error=0,num_bits=0,read_bits;
  int i;
  int x4,x3,x2,x1;
  unsigned int *int_arr=(unsigned int *) unpacked_array;
  FILE *instream=(FILE *)packed;
  // if no maximum integers are give read the whole nine yards
  if (max_num_int==0){
    max_num_int=dim1*dim2;
  }
  // if a NULL pointer is passed allocate some new memory
  if (unpacked_array==NULL){
    if ( (unpacked_array=malloc(sizeof(unsigned int)*max_num_int))==NULL){
      errno=ENOMEM;
      return NULL;
    }
  }
  // packed bits always start at byte boundary after header
  bit_offset=0;
  // read the first byte of the current_block
  t_=(unsigned char)fgetc(instream);

  // while less than num ints have been unpacked
  i=0;  
  while(i<max_num_int){
    if (num_error==0){
       // at the beginning of block - read the 6 block header bits
      if (bit_offset>=(8-CCP4_PCK_BLOCK_HEADER_LENGTH)){
        // we'll be reading past the next byte boundary
        t2=(unsigned char ) fgetc(instream);
        t_=(t_>>bit_offset) + ((unsigned char)t2 <<(8-bit_offset) );
        num_error=CCP4_PCK_ERR_COUNT[t_ & CCP4_PCK_MASK[3]];
        num_bits=CCP4_PCK_BIT_COUNT[(t_>>3) & CCP4_PCK_MASK[3]];
        bit_offset=CCP4_PCK_BLOCK_HEADER_LENGTH+bit_offset-8;
        t_=t2;
      }else{
        num_error=CCP4_PCK_ERR_COUNT[(t_>>bit_offset) & CCP4_PCK_MASK[3]];
        num_bits=CCP4_PCK_BIT_COUNT[(t_>>(3+bit_offset)) & CCP4_PCK_MASK[3]];
        bit_offset+=CCP4_PCK_BLOCK_HEADER_LENGTH;
      } 
    } else {
      // reading the data in the block
      while(num_error>0){
        err_val=0;
        read_bits=0;
        while(read_bits<num_bits){
          if (bit_offset+(num_bits-read_bits)>=8) {
            // read to next full byte boundary and convert
            _conv= (t_>>bit_offset) & CCP4_PCK_MASK[8-bit_offset];
            err_val|= (unsigned int) _conv << read_bits;
            read_bits+=(8-bit_offset);
            // have read to byte boundary - set offset to 0 and read next byte
            bit_offset=0;
            t_=(unsigned char) fgetc(instream);
          }
          else {
            // must stop before next byte boundary - also this means that these are the last bits in the error
            _conv= (t_ >>bit_offset) & CCP4_PCK_MASK[num_bits-read_bits];
            err_val|= _conv<<read_bits;
            bit_offset+= (num_bits-read_bits);
            read_bits=num_bits;
          }
          
        }
        // if the msb is set, the error is negative -
        // * fill up with 1s to get a 2's compl representation
        if (err_val & (1 << (num_bits-1)) )
        {
          err_val|= -1<<(num_bits-1);
        }
        // store the current value in the unpacked array 
        if (i>dim1){
          // the current pixel is not in the first row - averaging is possible
          //  n.b. the averaging calculation is performed in the 2's complement domain
          x4=(int16_t) int_arr[i-1];
          x3=(int16_t) int_arr[i-dim1+1];
          x2=(int16_t) int_arr[i-dim1];
          x1=(int16_t) int_arr[i-dim1-1];
          int_arr[i]=(uint16_t) (err_val + (x4 + x3 + x2 + x1 +2) /4 );
          i=i;
        } else if (i!=0){
          // current pixel is in the 1st row but is not first pixel
          int_arr[i]=(uint16_t) (err_val + int_arr[i-1]);
        } else {
          int_arr[i]=(uint16_t) err_val;
        }
        i++;
        num_error--;
      } 
    }// else
  }
  return (void *) unpacked_array;
}


void * ccp4_unpack_string(
    void *unpacked_array,
    void *packed,
    size_t dim1,size_t dim2,
    size_t max_num_int
    ){

  uint8_t t_,t2,_conv;
  int err_val,bit_offset,num_error=0,num_bits=0,read_bits;
  int i;
  int x4,x3,x2,x1;
  unsigned int *int_arr;
  char *instream = (char *)packed;

  // if no maximum integers are give read the whole nine yards
  if (max_num_int==0){
    max_num_int=dim1*dim2;
  }
  // if a NULL pointer is passed allocate some new memory
  if (unpacked_array==NULL){
    if ( (unpacked_array=malloc(sizeof(unsigned int)*max_num_int))==NULL){
      errno=ENOMEM;
      return NULL;
    }
  }
  int_arr = (unsigned int *) unpacked_array;

  // packed bits always start at byte boundary after header
  bit_offset=0;
  // read the first byte of the current_block
  t_=(unsigned char)*instream;
  instream++;
  // printf("%02X \n",t_);
  // while less than num ints have been unpacked
  i=0;
  while(i<max_num_int){
    if (num_error==0){
      // at the beginning of block - read the 6 block header bits
      if (bit_offset>=(8-CCP4_PCK_BLOCK_HEADER_LENGTH)){
        // we'll be reading past the next byte boundary
        t2=(unsigned char ) *instream;
        instream++;
        t_=(t_>>bit_offset) + ((unsigned char)t2 <<(8-bit_offset) );
        num_error=CCP4_PCK_ERR_COUNT[t_ & CCP4_PCK_MASK[3]];
        num_bits=CCP4_PCK_BIT_COUNT[(t_>>3) & CCP4_PCK_MASK[3]];
        bit_offset=CCP4_PCK_BLOCK_HEADER_LENGTH+bit_offset-8;
        t_=t2;
      }else{
        num_error=CCP4_PCK_ERR_COUNT[(t_>>bit_offset) & CCP4_PCK_MASK[3]];
        num_bits=CCP4_PCK_BIT_COUNT[(t_>>(3+bit_offset)) & CCP4_PCK_MASK[3]];
        bit_offset+=CCP4_PCK_BLOCK_HEADER_LENGTH;
      }
    } else {
      // reading the data in the block
      while(num_error>0){
        err_val=0;
        read_bits=0;
        while(read_bits<num_bits){
          if (bit_offset+(num_bits-read_bits)>=8) {
            // read to next full byte boundary and convert
            _conv= (t_>>bit_offset) & CCP4_PCK_MASK[8-bit_offset];
            err_val|= (unsigned int) _conv << read_bits;
            read_bits+=(8-bit_offset);
            // have read to byte boundary - set offset to 0 and read next byte
            bit_offset=0;
            t_=(unsigned char) *instream;
            instream++;
          }
          else {
            // must stop before next byte boundary - also this means that these are the last bits in the error
            _conv= (t_ >>bit_offset) & CCP4_PCK_MASK[num_bits-read_bits];
            err_val|= _conv<<read_bits;
            bit_offset+= (num_bits-read_bits);
            read_bits=num_bits;
          }

        }
        // if the msb is set, the error is negative -
        // fill up with 1s to get a 2's compl representation
        if (err_val & (1 << (num_bits-1)) )
        {
          err_val|= -1<<(num_bits-1);
        }
        // store the current value in the unpacked array
        if (i>dim1){
          // the current pixel is not in the first row - averaging is possible
          //  n.b. the averaging calculation is performed in the 2's complement domain
          x4=(int16_t) int_arr[i-1];
          x3=(int16_t) int_arr[i-dim1+1];
          x2=(int16_t) int_arr[i-dim1];
          x1=(int16_t) int_arr[i-dim1-1];
          int_arr[i]=(uint16_t) (err_val + (x4 + x3 + x2 + x1 +2) /4 );
          i=i;
        } else if (i!=0){
          // current pixel is in the 1st row but is not first pixel
          int_arr[i]=(uint16_t) (err_val + int_arr[i-1]);
        } else {
          int_arr[i]=(uint16_t) err_val;
        }
        i++;
        num_error--;
      }
    } //else
  }
  return (void *) unpacked_array;
}


void * ccp4_unpack_v2(
    void *unpacked_array,
    void *packed,
    size_t dim1,size_t dim2,
    size_t max_num_int){

  uint8_t t_,t2,_conv;
  int err_val,bit_offset,num_error=0,num_bits=0,read_bits;
  int i;
  unsigned int x4=0,x3=0,x2=0,x1=0;
  unsigned int *int_arr=(unsigned int *) unpacked_array;
  FILE *instream=(FILE *)packed;
  
  // if no maximum integers are give read the whole nine yards
  if (max_num_int==0){
    max_num_int=dim1*dim2;
  }
  // if a NULL pointer is passed allocate some new memory
  if (unpacked_array==NULL){
    if ( (unpacked_array=malloc(sizeof(unsigned int)*max_num_int))==NULL){
      errno=ENOMEM;
      return NULL;
    }
  }
  // packed bits always start at byte boundary after header
  bit_offset=0;
  // read the first byte of the current_block
  t_=(unsigned char)fgetc(instream);
  // while less than num ints have been unpacked
  i=0;  
  while(i<max_num_int){
    if (num_error==0){
       // at the beginning of block - read the 6 block header bits
      if (bit_offset>=(8-CCP4_PCK_BLOCK_HEADER_LENGTH_V2)){
        // we'll be reading past the next byte boundary
        t2=(unsigned char ) fgetc(instream);
        t_=(t_>>bit_offset) + ((unsigned char)t2 <<(8-bit_offset) );
        num_error=CCP4_PCK_ERR_COUNT_V2[t_ & CCP4_PCK_MASK[4]];
        num_bits=CCP4_PCK_BIT_COUNT_V2[(t_>>4) & CCP4_PCK_MASK[4]];
        bit_offset=CCP4_PCK_BLOCK_HEADER_LENGTH_V2+bit_offset-8;
        t_=t2;
      }else{
        num_error=CCP4_PCK_ERR_COUNT_V2[ (t_>>bit_offset) & CCP4_PCK_MASK[4] ];
        num_bits=CCP4_PCK_BIT_COUNT_V2[ (t_>>(4+bit_offset)) & CCP4_PCK_MASK[4] ];
        bit_offset+=CCP4_PCK_BLOCK_HEADER_LENGTH_V2;
      } 
    } else {
      // reading the data in the block
      while(num_error>0){
        err_val=0;
        read_bits=0;
        while(read_bits<num_bits){
          if (bit_offset+(num_bits-read_bits)>=8) {
            // read to next full byte boundary and convert
            _conv= (t_>>bit_offset) & CCP4_PCK_MASK[8-bit_offset];
            err_val|= (unsigned int) _conv << read_bits;
            read_bits+=(8-bit_offset);
            // have read to byte boundary - set offset to 0 and read next byte
            bit_offset=0;
            t_=(unsigned char) fgetc(instream);
          }
          else {
            // must stop before next byte boundary - also this means that these are the last bits in the error
            _conv= (t_ >>bit_offset) & CCP4_PCK_MASK[num_bits-read_bits];
            err_val|= _conv<<read_bits;
            bit_offset+= (num_bits-read_bits);
            read_bits=num_bits;
          }
          
        }
        // if the msb is set, the error is negative -
          // fill up with 1s to get a 2's compl representation
        if (err_val & (1 << (num_bits-1)) )
        {
          err_val|= -1<<(num_bits-1);
        }
        // store the current value in the unpacked array 
        if (i>dim1){
          // the current pixel is not in the first row - averaging is possible
          // n.b. the averaging calculation is performed in the 2's complement domain
          x4=(int16_t) int_arr[i-1];
          x3=(int16_t) int_arr[i-dim1+1];
          x2=(int16_t) int_arr[i-dim1];
          x1=(int16_t) int_arr[i-dim1-1];
          int_arr[i]=(uint16_t) (err_val + (x4 + x3 + x2 + x1 +2) /4 );
          i=i;
        } else if (i!=0){
          // current pixel is in the 1st row but is not first pixel
          int_arr[i]=(uint16_t) (err_val + int_arr[i-1]);
        } else {
          int_arr[i]=(uint16_t) err_val;
        }
        i++;
        num_error--;
      } 
    } // else
  }
  return (void *) unpacked_array;
}
void * ccp4_unpack_v2_string(
    void *unpacked_array,
    void *packed,
    size_t dim1,size_t dim2,
    size_t max_num_int){

  uint8_t t_,t2,_conv;
  int err_val,bit_offset,num_error=0,num_bits=0,read_bits;
  int i;
  unsigned int x4=0,x3=0,x2=0,x1=0;
  unsigned int *int_arr=(unsigned int *) unpacked_array;
  char *instream=(char *)packed;

  // if no maximum integers are give read the whole nine yards
  if (max_num_int==0){
    max_num_int=dim1*dim2;
  }
  // if a NULL pointer is passed allocate some new memory
  if (unpacked_array==NULL){
    if ( (unpacked_array=malloc(sizeof(unsigned int)*max_num_int))==NULL){
      errno=ENOMEM;
      return NULL;
    }
  }
  // packed bits always start at byte boundary after header
  bit_offset=0;
  // read the first byte of the current_block
  t_=(unsigned char)*instream;
  instream++;
  // while less than num ints have been unpacked
  i=0;
  while(i<max_num_int){
    if (num_error==0){
       // at the beginning of block - read the 6 block header bits
      if (bit_offset>=(8-CCP4_PCK_BLOCK_HEADER_LENGTH_V2)){
        // we'll be reading past the next byte boundary
        t2=(unsigned char ) *instream;
        instream++;
        t_=(t_>>bit_offset) + ((unsigned char)t2 <<(8-bit_offset) );
        num_error=CCP4_PCK_ERR_COUNT_V2[t_ & CCP4_PCK_MASK[4]];
        num_bits=CCP4_PCK_BIT_COUNT_V2[(t_>>4) & CCP4_PCK_MASK[4]];
        bit_offset=CCP4_PCK_BLOCK_HEADER_LENGTH_V2+bit_offset-8;
        t_=t2;
      }else{
        num_error=CCP4_PCK_ERR_COUNT_V2[ (t_>>bit_offset) & CCP4_PCK_MASK[4] ];
        num_bits=CCP4_PCK_BIT_COUNT_V2[ (t_>>(4+bit_offset)) & CCP4_PCK_MASK[4] ];
        bit_offset+=CCP4_PCK_BLOCK_HEADER_LENGTH_V2;
      }
    } else {
      // reading the data in the block
      while(num_error>0){
        err_val=0;
        read_bits=0;
        while(read_bits<num_bits){
          if (bit_offset+(num_bits-read_bits)>=8) {
            // read to next full byte boundary and convert
            _conv= (t_>>bit_offset) & CCP4_PCK_MASK[8-bit_offset];
            err_val|= (unsigned int) _conv << read_bits;
            read_bits+=(8-bit_offset);
            // have read to byte boundary - set offset to 0 and read next byte
            bit_offset=0;
            t_=(unsigned char) *instream;
            instream++;
          }
          else {
            // must stop before next byte boundary - also this means that these are the last bits in the error
            _conv= (t_ >>bit_offset) & CCP4_PCK_MASK[num_bits-read_bits];
            err_val|= _conv<<read_bits;
            bit_offset+= (num_bits-read_bits);
            read_bits=num_bits;
          }

        }
        // if the msb is set, the error is negative -
        // fill up with 1s to get a 2's compl representation
        if (err_val & (1 << (num_bits-1)) )
        {
          err_val|= -1<<(num_bits-1);
        }
        // store the current value in the unpacked array
        if (i>dim1){
          // the current pixel is not in the first row - averaging is possible
          // n.b. the averaging calculation is performed in the 2's complement domain
          x4=(int16_t) int_arr[i-1];
          x3=(int16_t) int_arr[i-dim1+1];
          x2=(int16_t) int_arr[i-dim1];
          x1=(int16_t) int_arr[i-dim1-1];
          int_arr[i]=(uint16_t) (err_val + (x4 + x3 + x2 + x1 +2) /4 );
          i=i;
        } else if (i!=0){
          // current pixel is in the 1st row but is not first pixel
          int_arr[i]=(uint16_t) (err_val + int_arr[i-1]);
        } else {
          int_arr[i]=(uint16_t) err_val;
        }
        i++;
        num_error--;
      }
    } // else
  }
  return (void *) unpacked_array;
}


// #############################################################################
// ################### Everything to write Mar345 ##############################
// #############################################################################


// Returns the number of bits neccesary to encode the longword-array 'chunk'
//   of size 'n' The size in bits of one encoded element can be 0, 4, 5, 6, 7,
//   8, 16 or 32. 
int bits(		int32_t *chunk,		int n){
  int size, maxsize, i;

  for (i = 1, maxsize = abs(chunk[0]); i < n; ++i)
    maxsize = max(maxsize, abs(chunk[i]));
  if (maxsize == 0)
    size = 0;
  else if (maxsize < 8)
    size = 4 * n;
  else if (maxsize < 16)
    size = 5 * n;
  else if (maxsize < 32)
    size = 6 * n;
  else if (maxsize < 64)
    size = 7 * n;
  else if (maxsize < 128)
    size = 8 * n;
  else if (maxsize < 32768)
    size = 16 * n;
  else
    size = 32 * n;
  return(size);
}

// Calculates the difference of WORD-sized pixels of an image with the
//   truncated mean value of four of its neighbours. 'x' is the number of fast
//   coordinates of the image 'img', 'y' is the number of slow coordinates,
//   'diffs' will contain the differences, 'done' defines the index of the pixel
//   where calculating the differences should start. A pointer to the last
//   difference is returned. Maximally DIFFBUFSIZ differences are returned in
//   'diffs'.
int *diff_words(
		short int *word,
		int x,
		int y,
		int *diffs,
		int done){
  int i = 0;
  int tot = x * y;

  if (done == 0)
  { *diffs = word[0];
    ++diffs;
    ++done;
    ++i;}
  while ((done <= x) && (i < DIFFBUFSIZ))
  { *diffs = word[done] - word[done - 1];
    ++diffs;
    ++done;
    ++i;}
  while ((done < tot) && (i < DIFFBUFSIZ))
  { *diffs = word[done] - (word[done - 1] + word[done - x + 1] +
                           word[done - x] + word[done - x - 1] + 2) / 4;
    ++diffs;
    ++done;
    ++i;}
  return(--diffs);
}

// Pack 'n' WORDS, starting with 'lng[0]' into the packed array 'target'. The
//   elements of such a packed array do not obey BYTE-boundaries, but are put one
//   behind the other without any spacing. Only the 'bitsiz' number of least
//   significant bits are used. The starting bit of 'target' is 'bit' (bits range
//   from 0 to 7). After completion of 'pack_words()', both '**target' and '*bit'
//   are updated and define the next position in 'target' from which packing
//   could continue. 
void pack_longs(int32_t *lng,
		int n,
		char **target,
		int *bit,
		int size){
  int32_t mask, window;
  int valids, i, temp;
  int temp_bit = *bit;
  char *temp_target = *target;

  if (size > 0)
  { mask = CCP4_PCK_MASK_32[size];
    for (i = 0; i < n; ++i)
    { window = lng[i] & mask;
      valids = size;
      if (temp_bit == 0)
        *temp_target = (char) window;
      else
      { temp = shift_left(window, temp_bit);
        *temp_target |= temp;}
      window = shift_right(window, 8 - temp_bit);
      valids = valids - (8 - temp_bit);
      if (valids < 0)
        temp_bit += size;
      else
      { while (valids > 0)
        { *++temp_target = (char) window;
          window = shift_right(window, 8);
          valids -= 8;}
        temp_bit = 8 + valids;}
      if (valids == 0)
      { temp_bit = 0;
        ++temp_target;}}
  *target = temp_target;
  *bit = (*bit + (size * n)) % 8;}
}


// Packs 'nmbr' LONGs starting at 'lng[0]' into a packed array of 'bitsize'
//   sized elements. If the internal buffer in which the array is packed is full,
//   it is flushed to 'file', making room for more of the packed array. If
//   ('lng == NULL'), the buffer is flushed a swell. 
void pack_chunk(int32_t *lng,
		int nmbr,
		int bitsize,
		FILE *packfile){
  static int32_t bitsize_encode[33] = {0, 0, 0, 0, 1, 2, 3, 4, 5, 0, 0,
                                    0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0,
                                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7};
  int32_t descriptor[2], i, j;
  static char *buffer = NULL;
  static char *buffree = NULL;
  static int bitmark;

  if (buffer == NULL)
  { buffree = buffer = (char *) malloc(PACKBUFSIZ);
    bitmark = 0;}
  if (lng != NULL)
  { for (i = nmbr, j = 0; i > 1; i /= 2, ++j);
    descriptor[0] = j;
    descriptor[1] = bitsize_encode[bitsize];
    if ((buffree - buffer) > (PACKBUFSIZ - (130 * 4)))
    { fwrite(buffer, sizeof(char), buffree - buffer, packfile);
      buffer[0] = buffree[0];
      buffree = buffer;}
    pack_longs(descriptor, 2, &buffree, &bitmark, 3);
    pack_longs(lng, nmbr, &buffree, &bitmark, bitsize);}
  else
  { int len=buffree-buffer;
    if (bitmark!=0) len++;
    fwrite(buffer, sizeof(char), len, packfile);
    free((void *) buffer);
    buffer = NULL;}}


// Pack image 'img', containing 'x * y' WORD-sized pixels into 'filename'. 
void pack_wordimage_copen(short int *img,
		int x,
		int y,
		FILE *packfile){
	int chunksiz, packsiz, nbits, next_nbits, tot_nbits;
	  int32_t buffer[DIFFBUFSIZ];
	  int32_t *diffs = buffer;
	  int32_t *end = diffs - 1;
	  int32_t done = 0;

	  fprintf(packfile, PACKIDENTIFIER, x, y);
	  while (done < (x * y))
	  { end = diff_words(img, x, y, buffer, done);
		done += (end - buffer) + 1;
		diffs = buffer;
		while (diffs <= end)
		{ packsiz = 0;
		  chunksiz = 1;
		  nbits = bits(diffs, 1);
		  while (packsiz == 0)
		  { if (end <= (diffs + chunksiz * 2))
			  packsiz = chunksiz;
			else
			{ next_nbits = bits(diffs + chunksiz, chunksiz);
			  tot_nbits = 2 * max(nbits, next_nbits);
			  if (tot_nbits >= (nbits + next_nbits + 6))
				packsiz = chunksiz;
			  else
			  { nbits = tot_nbits;
				if (chunksiz == 64)
				  packsiz = 128;
				else
				  chunksiz *= 2;}}}
		   pack_chunk(diffs, packsiz, nbits / packsiz, packfile);
		   diffs += packsiz;}}
		pack_chunk(NULL, 0, 0, packfile);
}



void pack_wordimage_c(
		short int *img,
		int x, int y,
		char *filename){
  FILE *packfile = fopen(filename, "ab");
  if (packfile == NULL) {
    fprintf(stderr,"The file %s cannot be created!\n   ...giving up...\n",
          filename);
    exit(1);
  } else {
    pack_wordimage_copen(img, x, y, packfile);
    fclose(packfile);
  }
}

