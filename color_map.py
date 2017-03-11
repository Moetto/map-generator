from typing import Sequence

import numpy as np
import pyopencl as cl
from PIL import Image
from webcolors import hex_to_rgb

from base_maps import CLMap
from height_map import HeightMap
from obeserver import Observer
from river_map import RiverMap


class ColorRange:
    def __init__(self, start: float, end: float, start_rgb: Sequence[int], end_rgb: Sequence[int]):
        self.start = start
        self.end = end
        self.start_rgb = start_rgb
        self.end_rgb = end_rgb


class ColorMap(CLMap, Observer):
    def __init__(self, width, height, context: cl.Context, height_map: HeightMap, river_map: RiverMap,
                 color_ranges: Sequence[ColorRange]):
        super().__init__(width, height, context)
        self.height_map = height_map
        self.river_map = river_map
        self.height_map.subscribe(self)
        self.river_map.subscribe(self)
        self.color_ranges = color_ranges
        self.map_tools = cl.Program(self.ctx, open("maptools.cl").read()).build()
        self.generate()

    def generate(self):
        if self.valid:
            return
        if not self.height_map.valid:
            self.height_map.generate()
        if not self.river_map.valid:
            self.river_map.generate()
        queue = cl.CommandQueue(self.ctx)

        r = np.empty((self.height, self.width), 'uint8')
        g = np.empty((self.height, self.width), 'uint8')
        b = np.empty((self.height, self.width), 'uint8')

        colors = [r, g, b]

        input_buf = cl.Buffer(self.ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                              hostbuf=self.height_map.map)
        destination_r = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, r.nbytes)
        destination_g = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, r.nbytes)
        destination_b = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, r.nbytes)

        color_buffers = [destination_r, destination_g, destination_b]

        max_height = self.height_map.map.max()
        events = []
        for color_buf in self.color_ranges:
            e = self.map_tools.ColoredMap(queue, (self.height, self.width), None,
                                          input_buf,
                                          destination_r,
                                          destination_g,
                                          destination_b,
                                          np.float32(color_buf.start * max_height / 100),
                                          np.float32(color_buf.end * max_height / 100),
                                          np.int32(np.array(color_buf.start_rgb)),
                                          np.int32(np.array(color_buf.end_rgb)),
                                          np.int32(self.width),
                                          np.int32(self.height),
                                          wait_for=events)
            events.append(e)

        for i in range(3):
            cl.enqueue_copy(queue, colors[i], color_buffers[i], wait_for=[events[-1]])
        b[self.river_map.map > 200] = 255

        self.image = Image.merge("RGB", (
            Image.fromarray(r, "L"),
            Image.fromarray(g, "L"),
            Image.fromarray(b, "L")))
        self.valid = True

    @classmethod
    def hex_to_rgb4(cls, hex_color):
        rgb = hex_to_rgb(hex_color)
        l = [x for x in rgb]
        l.append(0)
        return l
