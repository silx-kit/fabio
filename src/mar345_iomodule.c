#include <Python.h>
#include <Numeric/arrayobject.h>
#include <stdlib.h>
#include <stdio.h>

void *mar345_read_data(FILE *file, unsigned int ocount, unsigned int dim1, unsigned int dim2);

static PyObject * mar345_io_unpack(PyObject *self, PyObject *args){
  const int dim1,dim2,ocount;
  int dims[2];
  PyArrayObject *py_unpacked;
  PyObject *py_file;
  int *unpacked;
  FILE *file;
  if (!PyArg_ParseTuple(args, "Oiii", &py_file,&dim1,&dim2,&ocount))
    return NULL;
  dims[0]=dim1;dims[1]=dim2;
  py_unpacked=(PyArrayObject*)PyArray_FromDims(2,dims,PyArray_USHORT);
  file=PyFile_AsFile(py_file);

  unpacked=mar345_read_data(file,ocount,dim1,dim2);
  //memcpy(py_unpacked->data,unpacked,dim1*dim2*2);
  py_unpacked->data=(void *)unpacked;
  PyArray_Return(py_unpacked);
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
}
