# Demonstrator for Byte offset decompression in OpenCL

import numpy
import fabio
import pyopencl, pyopencl.array

fname = "testimages/run2_1_00148.cbf"
cbf = fabio.cbfimage.CbfImage()
data = fabio.open(fname).data
raw = cbf.read(fname, only_raw=True)

ctx = pyopencl.create_some_context(interactive=False)
queue = pyopencl.CommandQueue(ctx)


raw_n = numpy.fromstring(raw, dtype="int8")
size = raw_n.size
raw_d = pyopencl.array.to_device(queue, raw_n)
data_d = pyopencl.array.empty(queue, (raw_n.size,), dtype="int32")
lem_d = pyopencl.array.empty_like(raw_d)


def decomp_vec(raw_n):
    "principle of implementation in numpy"
    size = raw_n.size
    lel = numpy.ones(size, dtype="uint8")
    mask8 = raw_n == -128
    lel[mask8] = 3
    for i in numpy.where(mask8)[0]:
        if (raw_n[i + 1] == 0) and (raw_n[i + 2] == -128):
            lel[i] = 7
            print(i)
    lem = numpy.zeros_like(lel)
    return lel

src = open("sandbox/cbf.cl").read()
prg = pyopencl.Program(ctx, src).build()

WG = 128
WS = (size + WG - 1) & ~(WG - 1)
la = pyopencl.LocalMemory(4 * WG)
lb = pyopencl.LocalMemory(4 * WG)
lc = pyopencl.LocalMemory(4 * WG)
prg.cumsum(queue, (WS,), (WG,), raw_d.data, data_d.data, numpy.int32(size), numpy.int32(size), la, lb, lc)

prg.dec_byte_offset(queue, (WS,), (WG,), raw_d.data, data_d.data, numpy.int32(size), numpy.int32(size), lem_d.data)
