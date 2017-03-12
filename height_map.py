from random import Random

import numpy as np
import pyopencl as cl
from PIL import Image

from base_maps import CLMap
from events import Invalidated, Seed
from height_map_filter import HeightMapFilter
from observables import Observable, Event


class HeightMap(CLMap):
    def __init__(self, controller: Observable, width, height, context, filters, seed=10000):
        super().__init__(controller, width, height, context)
        self.filters = filters
        self.seed = seed
        self.noise = cl.Program(self.ctx, open("noise/Noise.cl").read()).build()
        self.valid = False
        self.generate()

    def generate(self):
        if self.valid:
            return
        random = Random(self.seed)
        queue = cl.CommandQueue(self.ctx)
        self._map = np.empty((self.height, self.width), np.float32)
        destination_buf = cl.Buffer(self.ctx, cl.mem_flags.HOST_READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                                    hostbuf=np.full(self._map.size, 127.5, np.float32))
        events = []
        for f in self.filters:
            events.append(self.noise.HeightMap(queue, self._map.shape, None, destination_buf,
                                               np.int32(self.width), np.int32(self.height),
                                               np.int32(random.randint(0, 1000000)),
                                               np.float32(f.scale), np.float32(f.effect), wait_for=events))
        cl.enqueue_copy(queue, self._map, destination_buf, wait_for=events)
        self._map = HeightMapFilter(self.ctx).run_filter(self._map)

        self.image = Image.fromarray(self._map, "F")
        self.valid = True

    def handle(self, observable, event: Event):
        super().handle(observable, event)
        if type(event) is Seed:
            self.seed = event.seed
            self.notify(Invalidated())
