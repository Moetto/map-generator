import numpy as np
import pyopencl as cl


class HeightMapFilter:
    def __init__(self, ctx, program):
        self.ctx = ctx
        self.program = program

    def run_filter(self, _map):
        queue = cl.CommandQueue(self.ctx)
        destination_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=_map)
        events = [self.program.filter(queue, _map.shape, None,
                                      destination_buf,
                                      np.int32(_map.shape[1]),
                                      np.int32(_map.shape[0]),
                                      )]
        cl.enqueue_copy(queue, _map, destination_buf, wait_for=events)
        return _map
