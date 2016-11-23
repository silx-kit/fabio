# Demonstrator for Byte offset decompression in OpenCL

import numpy
import fabio
import pyopencl, pyopencl.array
import time
import os
# os.environ["PYOPENCL_CTX"] = "1:0"
os.environ["PYOPENCL_COMPILER_OUTPUT"] = "1"


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


ctx = pyopencl.create_some_context(interactive=True)


fname = "testimages/run2_1_00148.cbf"
cbf = fabio.cbfimage.CbfImage()
data = fabio.open(fname).data
raw = cbf.read(fname, only_raw=True)
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
tmp3_d = pyopencl.array.zeros_like(data_d)
lem_d = pyopencl.array.empty_like(data_d)
zero_d = pyopencl.array.zeros(queue, shape=1, dtype="int32")

src = open("sandbox/cbf.cl").read()
prg = pyopencl.Program(ctx, src).build()

for i in range(11):
    WG = 1 << i
    print("#" * 80)
    print("WG: %s" % WG)
    la = pyopencl.LocalMemory(4 * WG)
    lb = pyopencl.LocalMemory(4 * WG)
    lc = pyopencl.LocalMemory(4 * WG)
#     ld = pyopencl.LocalMemory(4)
    debug1_d = pyopencl.array.zeros(queue, shape=WG, dtype="int32")
    debug2_d = pyopencl.array.zeros(queue, shape=WG, dtype="int32")
    debug3_d = pyopencl.array.zeros(queue, shape=WG, dtype="int32")
    size = data.size

    wgsum_d = pyopencl.array.zeros(queue, shape=WG, dtype="int32")

    t0 = time.time()
    data_d.set(data.ravel())

    size = data.size
    WS = (size + WG - 1) & ~(WG - 1)
    chunk = ((size + WG - 1) // WG + WG - 1) // WG
    zero_d.fill(0)
    tmp2_d.fill(0)

    evt = prg.comp_byte_offset1(queue, (WG * WG,), (WG,),
                                data_d.data, tmp2_d.data, numpy.uint32(size), numpy.uint32(chunk), wgsum_d.data, zero_d.data,
                                la, lb, lc, debug1_d.data, debug2_d.data, debug3_d.data)
    profile(evt, "comp_byte_offset1")

    # Create dest buffers
    tmp_cumsum = wgsum_d.get()
    dest_size = tmp_cumsum[-1]

    print("Start process: %s" % debug3_d)
    print("End process: %s" % debug2_d)
    print("Total Size: %s" % (dest_size))
    print("After small cumsum=%s" % (tmp_cumsum))
    print("Counters= %s" % (debug1_d))
    target_d = pyopencl.array.zeros(queue, (dest_size,), dtype="int8")

    evt = prg.comp_byte_offset2(queue, (WG * WG,), (WG,),
                                data_d.data, tmp2_d.data, wgsum_d.data, target_d.data,
                                numpy.uint32(size), numpy.uint32(dest_size), numpy.uint32(chunk))
    profile(evt, "comp_byte_offset2")
    print("Total time : %.3fms" % (1000 * (time.time() - t0)))
    print("residual error: %s" % (numpy.where(raw_n - target_d.get())))
