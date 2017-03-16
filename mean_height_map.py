import numpy as np
import pyopencl as cl

from base_maps import CLMap
from height_map import HeightMap
from observables import Observable


class MeanHeightMap(CLMap):
    def __init__(self, controller: Observable, width, height, ctx, height_map: HeightMap):
        super().__init__(controller, width, height, ctx)
        self.height_map = height_map
        self.map_tools = cl.Program(self.ctx, open("maptools.cl").read()).build()

    def generate(self):
        if self.valid:
            return
        queue = cl.CommandQueue(self.ctx)
        self._map = np.zeros_like(self.height_map.get_map(), dtype=np.float32)
        input_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self.height_map.get_map())
        output_buf = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, size=self._map.nbytes)

        event = self.map_tools.calculate_mean(queue, (self.height, self.width), None,
                                              input_buf,
                                              output_buf,
                                              np.int32(30),
                                              np.int32(self.width),
                                              np.int32(self.height))
        cl.enqueue_copy(queue, self._map, output_buf, wait_for=[event])
        self.valid = True
