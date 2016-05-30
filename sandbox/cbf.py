# Demonstrator for Byte offset decompression in OpenCL

import numpy
import fabio
import pyopencl, pyopencl.array


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


def profile(evt):
    print("Exec time: %.3fms" % (1e-6 * (evt.profile.end - evt.profile.start)))



fname = "testimages/run2_1_00148.cbf"
cbf = fabio.cbfimage.CbfImage()
data = fabio.open(fname).data
raw = cbf.read(fname, only_raw=True)
import os
os.environ["PYOPENCL_CTX"] = "0:0"
ctx = pyopencl.create_some_context(interactive=False)
properties = pyopencl.command_queue_properties.PROFILING_ENABLE
# properties = None
queue = pyopencl.CommandQueue(ctx, properties=properties)


raw_n = numpy.fromstring(raw, dtype="int8")
size = raw_n.size
raw_d = pyopencl.array.to_device(queue, raw_n)
data_d = pyopencl.array.empty(queue, (data.size,), dtype="int32")
tmp1_d = pyopencl.array.zeros_like(data_d)
tmp2_d = pyopencl.array.zeros_like(data_d)
lem_d = pyopencl.array.empty_like(data_d)

src = open("sandbox/cbf.cl").read()
prg = pyopencl.Program(ctx, src).build()

WG = 128
WS = (size + WG - 1) & ~(WG - 1)
la = pyopencl.LocalMemory(4 * WG)
lb = pyopencl.LocalMemory(4 * WG)
lc = pyopencl.LocalMemory(4 * WG)
prg.cumsum(queue, (WS,), (WG,), raw_d.data, data_d.data, numpy.int32(size), numpy.int32(size), la, lb, lc)

# prg.dec_byte_offset(queue, (WS,), (WG,), raw_d.data, data_d.data, numpy.int32(size), numpy.int32(size), lem_d.data)
data_d.set(data.ravel())

size = data.size
WS = (size + WG - 1) & ~(WG - 1)
chunk = ((size + WG - 1) // WG + WG - 1) // WG
evt = prg.comp_byte_offset1(queue, (WS,), (WG,), data_d.data, tmp1_d.data, numpy.uint32(size))
evt.wait()
profile(evt)
zero_d = pyopencl.array.zeros(queue, shape=1, dtype="int32")
wgsum_d = pyopencl.array.zeros(queue, shape=WG, dtype="int32")
print(size, WS, chunk * WG * WG)
evt = prg.comp_byte_offset2(queue, (WG * WG,), (WG,), data_d.data, tmp2_d.data, numpy.uint32(size), numpy.uint32(chunk), wgsum_d.data, zero_d.data, la, lb, lc)
evt.wait()
profile(evt)

# prg.cumsum(queue, (WS,), (WG,), raw_d.data, data_d.data, numpy.int32(size), numpy.int32(size), la, lb, lc)
