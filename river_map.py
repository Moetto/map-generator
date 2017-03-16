import numpy as np
import pyopencl as cl
from PIL import Image

from base_maps import CLMap
from continent_map import ContinentMap
from gradient_map import GradientMap
from observables import Observable


class RiverMap(CLMap):
    def __init__(self, controller: Observable, width, height, ctx, gradient_map: GradientMap,
                 continent_map: ContinentMap):
        super().__init__(controller, width, height, ctx)
        self.map_tools = cl.Program(self.ctx, open("maptools.cl").read()).build()
        self.gradient_map = gradient_map
        self.gradient_map.subscribe(self)
        self.continent_map = continent_map
        self.continent_map.subscribe(self)

    def generate(self):
        if self.valid:
            return
        self._map = np.zeros((self.height, self.width), np.int32)

        queue = cl.CommandQueue(self.ctx)
        gradient_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self.gradient_map.get_map())
        river_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self._map)

        event = self.map_tools.generate_rivers(queue, self._map.shape, None,
                                               gradient_buf,
                                               river_buf,
                                               np.int32(self.width),
                                               np.int32(self.height))
        cl.enqueue_copy(queue, self._map, river_buf, wait_for=[event])
        self._map[self.continent_map.get_map() == 0] = 0
        self._map *= 10
        self.image = Image.fromarray(self._map, 'I')
        self.valid = True
