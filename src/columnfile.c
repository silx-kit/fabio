#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef HAVE_ZLIB_H
#define HAVE_ZLIB_H 0
#else
#include <zlib.h>
#endif

#include "columnfile.h"

static char hdr_ctl[]="# %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s";

int compression_yes(char *fname){
  /*should we use compression*/
  char *p;
  if ( HAVE_ZLIB_H && (p=strstr(fname,".gz"))!=NULL && p<fname+strlen(fname) ){
    return 1;
  }
  return 0;
}

void inline cf_free( cf_data *p){
  int i;
  if (p!=NULL){
    for (i=0;i<p->nralloc;i++){
      if (p->data[i]!=NULL) free(p->data[i]);
    }
    if( p->data!=NULL){free(p->data);}
    for (i=0;i<p->ncols;i++){
      if(p->clabels[i]!=NULL) free(p->clabels[i]);
    }
    if(p->clabels!=NULL){free(p->clabels);}
    free(p);
  }
}

int cf_write(char *fname,void *cf_handle, unsigned int FLAGS){
#if HAVE_ZLIB_H
  if (FLAGS && CF_COMPRESSION){
    gzFile gzfp=gzopen(fname,"wbh");
    if (gzfp==NULL) return -1;
    int status=-1;
    if (FLAGS && CF_BINARY){
      status=cf_write_bin_gz(gzfp,cf_handle);
    }else{
      status=cf_write_ascii_gz(gzfp,cf_handle);
    }
    gzclose(gzfp);
    return status;
  }else{
#else 
  if(1){
#endif
    FILE *fp=fopen(fname,"wb");
    if (fp==NULL) return -1;
    int status=-1;
    if (FLAGS && CF_BINARY){
      /*status=cf_write_bin(fp,cf_handle);
        */
    }else{
      status=cf_write_ascii(fp,cf_handle);
    }
    fclose(fp);
    return status;
  }
}

int cf_write_ascii(FILE *fp, void *cf_handle){
  int r,c;
  cf_data *cf_=(cf_data *) cf_handle;
  fprintf(fp,"#");
  for (c=0;c<cf_->ncols;c++){
    fprintf(fp," %s",cf_->clabels[c]);
  }
  fprintf(fp,"\n");
  for (r=0;r<cf_->nrows;r++){
    for (c=0;c<cf_->ncols;c++){
      fprintf(fp," %g",cf_->data[c][r]);
    }
    fprintf(fp,"\n");
  }
  return 0;
}

#if HAVE_ZLIB_H
int cf_write_ascii_gz(gzFile fp, void *cf_handle){
  int r,c;
  cf_data *cf_=(cf_data *) cf_handle;
  gzprintf(fp,"#");
  for (i=0;i<cf_->ncols;i++){
    gzprintf(fp," %s",cf_->clabels[i]);
  }
  gzprintf(fp,"\n");
  for (r=0;r<cf_->nrows;r++){
    for (i=0;i<cf_->ncols;i++){
      gzprintf(fp," %g",cf_->data[i][r]);
    }
    gzprintf(fp,"\n");
  }
  return 0;
#endif

/*    
gzFile gzfp=gzopen(fname,"wbh");
    if (gzFile==NULL) return -1;
    gzprintf("# ");
    for (i=0;i<ncols;i++)
      gzprintf("%s ",cf_->clabels[i]);
    gzprintf("\n");
    for (r=0;r<0;
  }else{
    FILE *fp=fopen(fname,"wb");
  }
*/

void *cf_read_ascii(FILE *fp, void *dest){
  /*read the first line and figure out how many columns we have*/
  char line[2048];
  int i,r;
  int nr_alloc=CF_INIT_ROWS;
  int nc_alloc=CF_INIT_COLS;
  int ncols,nrows;
  char **clabels,**cp;
  double **data,**dp;
  char *p;

  /*read the first line into buffer*/
  fgets(line,2048,fp);

  /*initially allocate room for 32 columns - if that is not enough should reallocate*/
  clabels= malloc(CF_INIT_COLS* sizeof(char*));
  for (cp=clabels;cp<clabels+CF_INIT_COLS;cp++){
    *cp=(char *)malloc(CF_HEADER_ITEM*sizeof(char));
  }

  /*try to sscanf it using 32 conversions - if that doesn't work use pedestrian version*/
  ncols=sscanf(line,hdr_ctl,repeat16_inc(clabels,0),repeat16_inc(clabels,16),*(clabels+32));
  if (ncols==32+1 || ncols==0){
    /*aha we probably didn't get it all*/
    /*step through buffer with char ptr and check for whitespace->non-ws slopes. when one is found read from pc-1 into header storage. exit when line is exhausted*/
    /*count the number of entries*/
    ncols=0;
    /*headers are supposed to start with # so skip that*/
    if (*line=='#') p=line+1;
    else p=line;
    while (*p!='\0' || *p!='\n' || p<line+2048){
      if( is_ws(*p) && !is_ws(*(p+1)) && *(p+1)!='\0') {
        sscanf(p,"%s",*(clabels+ncols));
        ncols++;
      }
      p++;
    }
  }

  /*alloc a number of rows*/
  data=malloc(nr_alloc*sizeof(double*));
  for (dp=data;dp<data+nr_alloc;dp++){
    *dp=malloc(ncols*sizeof(double));
  }

  r=0;
  do {
    fgets(line,2048,fp);
    if (feof(fp)) break;
    
    i=0;  
    p=line;

    while (i<ncols && *p!='\0' && *p!='\n' && p<line+2048){
      /*find the starting points of data items. these are transitions from whitespace to non-ws
       * 1st one may not have beginning whitespace*/
      if( (!is_ws(*p) && p==line) || (is_ws(*p) && !is_ws(*(p+1)) && *(p+1)!='\0') ) {
        *(data[r] + i++)=atof(p);//0;//strtod(p,NULL);
      }
      p++;
    }

    r++;
    if (r==nr_alloc){
      /*we need to expand the data buffer*/
      nr_alloc+=nr_alloc;
      data=realloc(data,nr_alloc*sizeof(double*));
      for (dp=data+r;dp<data+nr_alloc;dp++){
        *dp=malloc(ncols*sizeof(double));
      }
    }
  } while (1);

  cf_data *dest_local;
  if (dest==NULL){
    dest_local=malloc(sizeof(cf_data));
  }else{
    dest_local=dest;
  }
  ((cf_data *) dest_local)->ncols=ncols;
  ((cf_data *) dest_local)->nrows=r;
  ((cf_data *) dest_local)->nralloc=nr_alloc;
  ((cf_data *) dest_local)->clabels=clabels;
  ((cf_data *) dest_local)->data=data;

  return (void *) dest_local;
}
