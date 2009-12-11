#include <Python.h>
#include <numpy/arrayobject.h>
#include <stdio.h>
#include <stdlib.h>
#include "columnfile.h"

static PyObject *cf_read(PyObject *self, PyObject *args, PyObject *keywds){
  cf_data *cf__;
  PyArrayObject *py_data;
  PyStringObject *str;
  PyListObject *clabels;

  static char *kwlist[]={"file","mode",NULL};
  const char mode[]="a ";
  unsigned int flags=0;

  /* perhaps not const */
  int dim1,dim2,ocount;
  int dims[2];
  int i;
  FILE *file;

  PyObject *py_file; 
  if (!PyArg_ParseTupleAndKeywords(args,keywds,"O|s",kwlist,&py_file,&mode))
   return NULL;
  file=PyFile_AsFile(py_file);

  if (strchr(mode,'z')){
    flags|=CF_GZ_COMP;
  }
  if(strchr(mode,'b')){
    cf__=(cf_data *) cf_read_bin(file,NULL,flags);
  }else if (strchr(mode,'a')) {
    cf__=(cf_data *) cf_read_ascii(file,NULL,flags);
  }else{
    fprintf(stderr,"unrecognized mode for columnfile %s (assuming ascii)\n",mode);
    cf__= (cf_data *)cf_read_ascii(file,NULL,flags);
  }
  /*check for failure to read*/
  if (cf__==NULL){
    return Py_BuildValue("OO",Py_None,Py_None);
  } 
  dims[0]=cf__->nrows;dims[1]=cf__->ncols;
  /*since data may be non-contigous we can't simply create a numpy-array from cf__->data, as Numpy's memory model prohibits it*/
  /*i.e. py_data=(PyArrayObject*)PyArray_SimpleNewFromData(2, dims, NPY_DOUBLE, (void*)(&(cf__->data[0][0])));
   * won't work*/
  py_data=(PyArrayObject *)PyArray_SimpleNew(2,dims,NPY_DOUBLE);
  for (i=0;i<cf__->nrows;i++){
    memcpy((double *)PyArray_GETPTR2(py_data,i,0),cf__->data[i],cf__->ncols*sizeof(double));
  }
  clabels=(PyListObject *)PyList_New(0);
  for (i=0;i<cf__->ncols;i++){
    str = (PyStringObject*)PyString_FromString(cf__->clabels[i]);
    if (PyList_Append((PyObject*)clabels,(PyObject*)str)){
      fprintf(stderr,"cannot insert column label %d\n",i);
    }
  }
  cf_free(cf__);
  return Py_BuildValue("OO", PyArray_Return(py_data),clabels);
}



static PyMethodDef cf_io_Methods[] = {
  {"read",(PyCFunction)cf_read, METH_VARARGS | METH_KEYWORDS, "call the c-columnfile reading interface. The mode keyword argument is either:\n  \"a\" for ascii (the default)\n  \"b\" for binary"},
  {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC initcf_io(void)
{
  (void) Py_InitModule("cf_io",cf_io_Methods);
  import_array();

  if (PyErr_Occurred())
    Py_FatalError("cannot initialize cf_iomodule.c");
}


