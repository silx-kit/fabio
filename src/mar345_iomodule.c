#include <Python.h>
#include <numpy/arrayobject.h>
#include <stdlib.h>
#include <stdio.h>

void *mar345_read_data(FILE *file, unsigned int ocount, unsigned int dim1, unsigned int dim2);

static PyObject * mar345_io_unpack(PyObject *self, PyObject *args){
  const int dim1,dim2,ocount;
  npy_intp dims[2];
  PyArrayObject *py_unpacked;
  PyObject *py_file;
  int *unpacked;
  FILE *file;
  if (!PyArg_ParseTuple(args, "Oiii", &py_file,&dim1,&dim2,&ocount))
    return NULL;
  dims[0]=dim1;dims[1]=dim2;

  file=PyFile_AsFile(py_file);

  /* Space is malloc'ed in here */
  unpacked=mar345_read_data(file,ocount,dim1,dim2);
  
  /* memcpy(py_unpacked->data,unpacked,dim1*dim2*2); would also need a free */
  
  py_unpacked=(PyArrayObject*)PyArray_SimpleNewFromData(2, dims, NPY_UINT, (void *)unpacked);

  return Py_BuildValue ("O", PyArray_Return(py_unpacked));
}

static PyMethodDef mar345_io_Methods[] = {
  {"unpack", mar345_io_unpack, METH_VARARGS, "Unpack a mar345 compressed image"},
  {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initmar345_io(void)
{
  (void) Py_InitModule("mar345_io", mar345_io_Methods);
  import_array();

  if(PyErr_Occurred())
    Py_FatalError("cannot initialize mar345_iomodule.c");
}
