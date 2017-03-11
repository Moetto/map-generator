from random import Random

import numpy as np
import pyopencl as cl
from PIL import Image

from base_maps import CLMap


class HeightMap(CLMap):
    def __init__(self, width, height, context, filters, seed=10000):
        super().__init__(width, height, context)
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
        self.map = np.empty((self.height, self.width), np.float32)
        destination_buf = cl.Buffer(self.ctx, cl.mem_flags.HOST_READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                                    hostbuf=np.full(self.map.size, 127.5, np.float32))
        events = []
        for f in [(0.01, 0.6), (0.05, 0.3), (0.2, 0.1)]:
            events.append(self.noise.HeightMap(queue, self.map.shape, None, destination_buf,
                                               np.int32(self.width), np.int32(self.height),
                                               np.int32(random.randint(0, 1000000)),
                                               np.float32(f[0]), np.float32(f[1]), wait_for=events))
        cl.enqueue_copy(queue, self.map, destination_buf, wait_for=events)
        # self.effective_sea_level = np.max(self.height_map) * self.sea_level / 100
        self.image = Image.fromarray(self.map, "F")
        self.valid = True

    def set_seed(self, seed):
        self.seed = seed
        self.invalidate()
