import random

import numpy as np
import pyopencl as cl

from webcolors import hex_to_rgb
from scipy.ndimage.morphology import binary_erosion
from PIL import Image


class Map:
    def __init__(self, size_x, size_y, filters, sea_level, seed=10):
        self.ctx = cl.create_some_context(interactive=False)
        self.queue = cl.CommandQueue(self.ctx)
        self.program = cl.Program(self.ctx, open("Noise.cl").read()).build()
        self.queue = cl.CommandQueue(self.ctx)
        self.size_x = size_x
        self.size_y = size_y
        self.map = np.zeros((size_y, size_x), np.float32)
        self.height_map = None
        self.theoretical_max_height = 255  # (sum([pair.effect for pair in filters])) * 2
        self.sea_level = sea_level
        self.effective_sea_level = 0
        self.image = None

    @staticmethod
    def _calculate_gradient_value(value, start_value, end_value, start_rgb, end_rgb, channel):
        percentage = (value - start_value) / (end_value - start_value)
        return int(start_rgb[channel] * (1 - percentage) + end_rgb[channel] * percentage)

    def generate_mountain(self, area):
        """
        Generate mountain to given area
        :param area: bit mask of map area(s) to hold mountains
        """
        distance_map = np.zeros_like(self.map)
        s = np.ones((3, 3))
        distance = 0.05
        while True:
            new_area = binary_erosion(area, s)
            edge = area - new_area
            if not np.any(edge):
                break
            distance_map[edge == 1] = distance
            area = new_area
            distance += 0.05
        self.theoretical_max_height += np.max(distance_map)
        self.map = self.map + distance_map

    def get_continents(self):
        mask = np.zeros_like(self.map)
        mask[self.map > self.sea_level / 100 * np.max(self.map)] = 1
        return mask

    def generate_height_map_image(self):
        self.height_map = np.empty(self.map.shape, np.float32)
        destination_buf = cl.Buffer(self.ctx, cl.mem_flags.HOST_READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                                    hostbuf=np.full(self.map.size, 127.5, np.float32))
        events = []
        for f in [(0.01, 0.6), (0.05, 0.3), (0.2, 0.1)]:
            events.append(self.program.HeightMap(self.queue, self.map.shape, None, destination_buf,
                                                 np.int32(self.size_x), np.int32(self.size_y),
                                                 np.int32(random.randint(0, 1000000)),
                                                 np.float32(f[0]), np.float32(f[1]), wait_for=events))
        cl.enqueue_copy(self.queue, self.height_map, destination_buf, wait_for=events)
        self.effective_sea_level = np.max(self.height_map) * self.sea_level / 100
        self.image = Image.fromarray(self.height_map, "F")

    @classmethod
    def hex_to_rgb4(cls, hex_color):
        rgb = hex_to_rgb(hex_color)
        l = [x for x in rgb]
        l.append(0)
        return l

    def generate_map_image(self, sea_deep, sea_shore, ground_shore, ground_high):
        self.generate_height_map_image()
        r = np.empty((self.size_y, self.size_x), 'uint8')
        g = np.empty((self.size_y, self.size_x), 'uint8')
        b = np.empty((self.size_y, self.size_x), 'uint8')

        colors = [r, g, b]

        input_buf = cl.Buffer(self.ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=self.height_map)
        destination_r = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, r.nbytes)
        destination_g = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, r.nbytes)
        destination_b = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, r.nbytes)

        color_bufs = [destination_r, destination_g, destination_b]

        events = []
        for i in range(3):
            k = self.program.ColoredMap
            # k.set_scalar_arg_dtypes([None, None, np.int32, np.int32, np.int32, np.int32])
            e = k(self.queue, (self.size_y, self.size_x), None, input_buf, color_bufs[i],
                  np.int32(i),
                  np.float32(self.effective_sea_level),
                  np.int32(np.array(self.hex_to_rgb4(sea_deep))),
                  np.int32(np.array(self.hex_to_rgb4(sea_shore))),
                  np.int32(np.array(self.hex_to_rgb4(ground_shore))),
                  np.int32(np.array(self.hex_to_rgb4(ground_high))),
                  np.int32(self.size_x),
                  np.int32(self.size_y))
            events.append(e)

        for i in range(3):
            cl.enqueue_copy(self.queue, colors[i], color_bufs[i], wait_for=[events[i]])

        self.image = Image.merge("RGB", (
            Image.fromarray(r, "L"),
            Image.fromarray(g, "L"),
            Image.fromarray(b, "L")))
