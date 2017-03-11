import numpy as np
import pyopencl as cl
from PIL import Image

from base_maps import CLMap
from continent_map import ContinentMap
from gradient_map import GradientMap
from obeserver import Observer


class RiverMap(CLMap, Observer):
    def __init__(self, width, height, ctx, gradient_map: GradientMap, continent_map: ContinentMap):
        super().__init__(width, height, ctx)
        self.map_tools = cl.Program(self.ctx, open("maptools.cl").read()).build()
        self.gradient_map = gradient_map
        self.gradient_map.subscribe(self)
        self.continent_map = continent_map
        self.continent_map.subscribe(self)
        self.generate()

    def generate(self):
        if self.valid:
            return
        if not self.gradient_map.valid:
            self.gradient_map.generate()
        if not self.continent_map.valid:
            self.continent_map.generate()

        self.map = np.zeros((self.height, self.width), np.int32)

        queue = cl.CommandQueue(self.ctx)
        gradient_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self.gradient_map.map)
        river_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self.map)

        event = self.map_tools.generate_rivers(queue, self.map.shape, None,
                                               gradient_buf,
                                               river_buf,
                                               np.int32(self.width),
                                               np.int32(self.height))
        cl.enqueue_copy(queue, self.map, river_buf, wait_for=[event])
        self.map[self.continent_map.map == 0] = 0
        self.map *= 10
        self.image = Image.fromarray(self.map, 'I')
