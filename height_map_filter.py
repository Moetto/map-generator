import numpy as np
import pyopencl as cl


class HeightMapFilter:
    def __init__(self, ctx):
        self.ctx = ctx
        self.program = cl.Program(self.ctx, open("island_filter.cl").read()).build()

    def run_filter(self, height_map):
        queue = cl.CommandQueue(self.ctx)
        destination_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR,
                                    hostbuf=height_map)
        events = [self.program.filter(queue, height_map.shape, None,
                                      destination_buf,
                                      np.int32(height_map.shape[1]),
                                      np.int32(height_map.shape[0]),
                                      )]
        cl.enqueue_copy(queue, height_map, destination_buf, wait_for=events)
        return height_map
