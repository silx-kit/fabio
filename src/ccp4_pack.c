#include <stdint.h>
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
void *ccp4_unpack(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);
void *ccp4_unpack_v2(void *unpacked_array, void *packed, size_t dim1, size_t dim2, size_t max_num_int);

/**unpack a new style mar345 image a'la what is done in CBFlib
 * assumes the file is already positioned after the ascii header
 * Perhaps the positioning should be done here as well.
 */
void * mar345_read_data(FILE *file, int ocount, int dim1, int dim2){
  /* first process overflow bytes - for now we just ignore them
   * these are stored in 64 byte records*/
  int orecords=(int)(ocount/8.0+0.875);
  int *odata,x,y,version=0;
  char *c,cbuffer[64]="";
  unsigned int *unpacked_array;
  
  odata=malloc(64*8*orecords);
  if (!odata)
    return NULL;
  pfail_nonzero (orecords-fread(odata,64,orecords,file));
  printf("have %d overflows in %d recs\n",ocount,orecords);
  
  /* now after they have been read find the CCP4.....string and compare to dim1*/
  c=cbuffer;
  while((*c)!=EOF){
    
    if (c==cbuffer+63){
     c=cbuffer;
    } 
    
    *c=(char)getc(file);
    /*set the next character to a \0 so the string is always terminated*/
    *(c+1)='\0';
    
    if (*c=='\n'){
      /*check for the CCP- string*/
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
  /* allocate memory for the arrays*/
  unpacked_array=malloc(sizeof(unsigned int)*dim1*dim2);
  if (!unpacked_array)
    return NULL;
  /*relay to whichever version of ccp4_unpack is appropriate*/
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
  
  /*handle overflows*/
  while (ocount>0){
    unsigned int adress,value;
    adress=odata[2*ocount-2];
    if (adress){
      value=odata[2*ocount-1];
      /*adresses start at 1*/
      unpacked_array[adress-1]=value;
    }
    ocount--;
  }
  return unpacked_array;
}

/**unpack a ccp4-style packed array into the memory location pointed to by unpacked_array
 * if this is null alloocate memory and return a pointer to it
 * \return NULL if unsuccesful
 * TODO change this to read directly from the FILE to not waste memory*/ 
void * ccp4_unpack(
    void *unpacked_array,
    void *packed,
    size_t dim1,size_t dim2,
    size_t max_num_int){

  uint8_t t_,t2,_conv;
  int err_val,bit_offset,num_error=0,num_bits=0,read_bits;
  int i;
  int x4,x3,x2,x1;
  unsigned int *int_arr=(unsigned int *) unpacked_array;
  FILE *instream=(FILE *)packed;
  
  /*if no maximum integers are give read the whole nine yards*/
  if (max_num_int==0){
    max_num_int=dim1*dim2;
  }
  /*if a NULL pointer is passed allocate some new memory*/
  if (unpacked_array==NULL){
    if ( (unpacked_array=malloc(sizeof(unsigned int)*max_num_int))==NULL){
      errno=ENOMEM;
      return NULL;
    }
  }
  /*packed bits always start at byte boundary after header*/
  bit_offset=0;
  /*read the first byte of the current_block*/
  t_=(unsigned char)fgetc(instream);
  /*while less than num ints have been unpacked*/
  i=0;  
  while(i<max_num_int){
    if (num_error==0){
      /* at the beginning of block - read the 6 block header bits*/
      if (bit_offset>=(8-CCP4_PCK_BLOCK_HEADER_LENGTH)){
        /*we'll be reading past the next byte boundary*/
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
      /*reading the data in the block*/
      while(num_error>0){
        err_val=0;
        read_bits=0;
        while(read_bits<num_bits){
          if (bit_offset+(num_bits-read_bits)>=8) {
            /*read to next full byte boundary and convert*/
            _conv= (t_>>bit_offset) & CCP4_PCK_MASK[8-bit_offset];
            err_val|= (unsigned int) _conv << read_bits;
            read_bits+=(8-bit_offset);
            /*have read to byte boundary - set offset to 0 and read next byte*/
            bit_offset=0;
            t_=(unsigned char) fgetc(instream);
          }
          else {
            /*must stop before next byte boundary - also this means that these are the last bits in the error*/
            _conv= (t_ >>bit_offset) & CCP4_PCK_MASK[num_bits-read_bits];
            err_val|= _conv<<read_bits;
            bit_offset+= (num_bits-read_bits);
            read_bits=num_bits;
          }
          
        }
        /*if the msb is set, the error is negative -
         * fill up with 1s to get a 2's compl representation*/
        if (err_val & (1 << (num_bits-1)) )
        {
          err_val|= -1<<(num_bits-1);
        }
        /*store the current value in the unpacked array*/ 
        if (i>dim1){
          /*the current pixel is not in the first row - averaging is possible
           *n.b. the averaging calculation is performed in the 2's complement domain*/
          x4=(int16_t) int_arr[i-1];
          x3=(int16_t) int_arr[i-dim1+1];
          x2=(int16_t) int_arr[i-dim1];
          x1=(int16_t) int_arr[i-dim1-1];
          int_arr[i]=(uint16_t) (err_val + (x4 + x3 + x2 + x1 +2) /4 );
          i=i;
        } else if (i!=0){
          /*current pixel is in the 1st row but is not first pixel*/
          int_arr[i]=(uint16_t) (err_val + int_arr[i-1]);
        } else {
          int_arr[i]=(uint16_t) err_val;
        }
        i++;
        num_error--;
      } 
    }/*else*/
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
  
  /*if no maximum integers are give read the whole nine yards*/
  if (max_num_int==0){
    max_num_int=dim1*dim2;
  }
  /*if a NULL pointer is passed allocate some new memory*/
  if (unpacked_array==NULL){
    if ( (unpacked_array=malloc(sizeof(unsigned int)*max_num_int))==NULL){
      errno=ENOMEM;
      return NULL;
    }
  }
  /*packed bits always start at byte boundary after header*/
  bit_offset=0;
  /*read the first byte of the current_block*/
  t_=(unsigned char)fgetc(instream);
  /*while less than num ints have been unpacked*/
  i=0;  
  while(i<max_num_int){
    if (num_error==0){
      /* at the beginning of block - read the 6 block header bits*/
      if (bit_offset>=(8-CCP4_PCK_BLOCK_HEADER_LENGTH_V2)){
        /*we'll be reading past the next byte boundary*/
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
      /*reading the data in the block*/
      while(num_error>0){
        err_val=0;
        read_bits=0;
        while(read_bits<num_bits){
          if (bit_offset+(num_bits-read_bits)>=8) {
            /*read to next full byte boundary and convert*/
            _conv= (t_>>bit_offset) & CCP4_PCK_MASK[8-bit_offset];
            err_val|= (unsigned int) _conv << read_bits;
            read_bits+=(8-bit_offset);
            /*have read to byte boundary - set offset to 0 and read next byte*/
            bit_offset=0;
            t_=(unsigned char) fgetc(instream);
          }
          else {
            /*must stop before next byte boundary - also this means that these are the last bits in the error*/
            _conv= (t_ >>bit_offset) & CCP4_PCK_MASK[num_bits-read_bits];
            err_val|= _conv<<read_bits;
            bit_offset+= (num_bits-read_bits);
            read_bits=num_bits;
          }
          
        }
        /*if the msb is set, the error is negative -
         * fill up with 1s to get a 2's compl representation*/
        if (err_val & (1 << (num_bits-1)) )
        {
          err_val|= -1<<(num_bits-1);
        }
        /*store the current value in the unpacked array*/ 
        if (i>dim1){
          /*the current pixel is not in the first row - averaging is possible
           *n.b. the averaging calculation is performed in the 2's complement domain*/
          x4=(int16_t) int_arr[i-1];
          x3=(int16_t) int_arr[i-dim1+1];
          x2=(int16_t) int_arr[i-dim1];
          x1=(int16_t) int_arr[i-dim1-1];
          int_arr[i]=(uint16_t) (err_val + (x4 + x3 + x2 + x1 +2) /4 );
          i=i;
        } else if (i!=0){
          /*current pixel is in the 1st row but is not first pixel*/
          int_arr[i]=(uint16_t) (err_val + int_arr[i-1]);
        } else {
          int_arr[i]=(uint16_t) err_val;
        }
        i++;
        num_error--;
      } 
    }/*else*/
  }
  return (void *) unpacked_array;
}
