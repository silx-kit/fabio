#ifndef CF_H
#define CF_H 1

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define CF_INIT_ROWS 8192
#define CF_INIT_COLS 32
#define CF_HEADER_ITEM 128


#define CF_GZ_COMP 1
#define CF_BIN 2


#define repeat16_inc(name,offset) \
  *((name)+(offset)),*((name)+(offset)+1),*((name)+(offset)+2),*((name)+(offset)+3),*((name)+(offset)+4), \
  *((name)+(offset)+5),*((name)+(offset)+6),*((name)+(offset)+7),*((name)+(offset)+8),*((name)+(offset)+9), \
  *((name)+(offset)+10),*((name)+(offset)+11),*((name)+(offset)+12),*((name)+(offset)+13),*((name)+(offset)+14),*((name)+(offset)+15)

#define cf_check_realloc(p,i,chunk_size,item_size) \
  do {\
    if((i)%(chunk_size)==0){\
  } while (0);

#define cf_sscan_column(source,conversion,dest,prefix) \
    do {\
      int tmpi=0;\
      if ((prefix)!=NULL) sscanf(source,prefix);\
      while (sscanf( (source) , (conversion) , ((dest) +tmpi))){\
        tmpi++;\
      }\
    } while (0);

#define is_ws(character) \
    ( (character==' ') || ((character)=='\t') || ((character)=='\v') || ((character) =='\r') || ((character) =='\n') )

typedef struct cf_data{
  int ncols,nrows;
  unsigned int nralloc;
  double **data;
  char **clabels;
} cf_data;

void * cf_read_ascii(void *fp, void *dest, unsigned int FLAGS);
void * cf_read_bin(void *fp, void *dest, unsigned int FLAGS);
int cf_write(char *fname, void *cf_handle, unsigned int FLAGS);
int cf_write_bin(void *fp, void *cf_handle);
int cf_write_ascii(void *fp, void *cf_handle,unsigned int FLAGS);
void cf_free( cf_data *cf_handle);



#endif
