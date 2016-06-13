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


def profile(evt, cmt=""):
    evt.wait()
    print("%s Exec time: %.3fms" % (cmt, 1e-6 * (evt.profile.end - evt.profile.start)))

fname = "testimages/run2_1_00148.cbf"
cbf = fabio.cbfimage.CbfImage()
data = fabio.open(fname).data
raw = cbf.read(fname, only_raw=True)
import os
os.environ["PYOPENCL_CTX"] = "2"
os.environ["PYOPENCL_COMPILER_OUTPUT"] = "1"
ctx = pyopencl.create_some_context(interactive=False)
properties = pyopencl.command_queue_properties.PROFILING_ENABLE
# properties = None
queue = pyopencl.CommandQueue(ctx, properties=properties)


raw_n = numpy.fromstring(raw, dtype="int8")
size = raw_n.size
raw_d = pyopencl.array.to_device(queue, raw_n)
int_d = pyopencl.array.empty(queue, (size,), dtype="int32")
data_d = pyopencl.array.empty(queue, (data.size,), dtype="int32")
tmp1_d = pyopencl.array.zeros_like(data_d)
tmp2_d = pyopencl.array.zeros_like(data_d)
lem_d = pyopencl.array.empty_like(data_d)

src = open("sandbox/cbf.cl").read()
prg = pyopencl.Program(ctx, src).build()
# for i in range(11):

WG = 128  # 1 << i
print("WG: %s" % WG)
WS = (size + WG - 1) & ~(WG - 1)
la = pyopencl.LocalMemory(4 * WG)
lb = pyopencl.LocalMemory(4 * WG)
lc = pyopencl.LocalMemory(4 * WG)
# print("Test CumSum", (WS,), (WG,), raw_d.size, int_d.size, numpy.int32(size), numpy.int32(size), la.size, lb.size, lc.size)
evt = prg.cumsum(queue, (WS,), (WG,), raw_d.data, int_d.data, numpy.int32(size), numpy.int32(size), la, lb, lc)
profile(evt, "cumsum")

# prg.dec_byte_offset(queue, (WS,), (WG,), raw_d.data, data_d.data, numpy.int32(size), numpy.int32(size), lem_d.data)
data_d.set(data.ravel())

size = data.size
WS = (size + WG - 1) & ~(WG - 1)
chunk = ((size + WG - 1) // WG + WG - 1) // WG
# print("Test comp_byte_offset1", (WS,), (WG,), data_d.data, tmp1_d.data, numpy.uint32(size))
evt = prg.comp_byte_offset1(queue, (WS,), (WG,), data_d.data, tmp1_d.data, numpy.uint32(size))
profile(evt, "comp_byte_offset1")
zero_d = pyopencl.array.zeros(queue, shape=1, dtype="int32")
wgsum_d = pyopencl.array.zeros(queue, shape=WG, dtype="int32")
print(size, WS, chunk * WG * WG)

# kernel void comp_byte_offset2(
#         global int* input,
#         global int* output,
#         uint input_size,
#         uint chunk,
#         global int* last_wg,
#         global uint* workgroup_counter,
#         __local int *a,
#         __local int *b,
#         __local int *c)

evt = prg.comp_byte_offset2(queue, (WG * WG,), (WG,), data_d.data, tmp2_d.data, numpy.uint32(size), numpy.uint32(chunk), wgsum_d.data, zero_d.data, la, lb, lc)
evt.wait()
profile(evt, "comp_byte_offset2")
dest_size = wgsum_d.get()[-1]
print("Size: %s" % dest_size)
target_d = pyopencl.array.empty(queue, (dest_size,), dtype="int8")

# Create dest buffers

# kernel void comp_byte_offset3(
#         global int* input,
#         global int* local_index,
#         global int* global_offset,
#         global char* output,
#         uint input_size,
#         uint output_size,
#         uint chunk)
evt = prg.comp_byte_offset3(queue, (WG * WG,), (WG,),
                            data_d.data, tmp2_d.data, wgsum_d.data, target_d.data,
                            numpy.uint32(size), numpy.uint32(dest_size), numpy.uint32(chunk))
evt.wait()
profile(evt, "comp_byte_offset3")
