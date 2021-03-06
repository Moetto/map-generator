import numpy as np
import pyopencl as cl
from PIL import Image

from base_maps import CLMap
from mean_height_map import MeanHeightMap
from observables import Observable


class GradientMap(CLMap):
    def __init__(self, controller: Observable, width, height, ctx, mean_height_map: MeanHeightMap):
        super().__init__(controller, width, height, ctx)
        self.mean_height_map = mean_height_map
        self.map_tools = cl.Program(self.ctx, open("maptools.cl").read()).build()
        self.generate()

    def generate(self):
        if self.valid:
            return
        if not self.mean_height_map.valid:
            self.mean_height_map.generate()
        gradients = np.gradient(self.mean_height_map.get_map())
        self._map = np.empty((self.height, self.width), np.uint8)

        queue = cl.CommandQueue(self.ctx)
        y_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=gradients[0])
        x_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=gradients[1])
        output_buf = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, size=self._map.nbytes)

        event = self.map_tools.gradient_direction(queue, self._map.shape, None,
                                                  x_buf,
                                                  y_buf,
                                                  output_buf,
                                                  np.int32(self.width))
        cl.enqueue_copy(queue, self._map, output_buf, wait_for=[event])
        self.image = Image.fromarray(self._map * 35, 'P')
