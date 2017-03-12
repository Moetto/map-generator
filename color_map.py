from typing import Sequence

import numpy as np
import pyopencl as cl
from PIL import Image
from webcolors import hex_to_rgb

from base_maps import CLMap
from events import SeaLevel, Invalidated
from height_map import HeightMap
from observables import Observable, Event
from river_map import RiverMap


class ColorRange:
    def __init__(self, start: float, end: float, underwater, start_rgb: Sequence[int], end_rgb: Sequence[int]):
        self.start = start
        self.end = end
        self.start_rgb = start_rgb
        self.end_rgb = end_rgb
        self.underwater = underwater


class ColorMap(CLMap):
    def __init__(self, controller: Observable, width: int, height: int, context: cl.Context,
                 height_map: HeightMap,
                 river_map: RiverMap,
                 sea_level: int,
                 color_ranges: Sequence[ColorRange]):
        super().__init__(controller, width, height, context)
        self.height_map = height_map
        self.height_map.subscribe(self)
        self.river_map = river_map
        self.river_map.subscribe(self)
        self._sea_level = sea_level
        self._color_buffers = color_ranges
        self.map_tools = cl.Program(self.ctx, open("maptools.cl").read()).build()
        self.generate()

    def generate(self):
        if self.valid:
            return
        queue = cl.CommandQueue(self.ctx)

        r = np.empty((self.height, self.width), 'uint8')
        g = np.empty((self.height, self.width), 'uint8')
        b = np.empty((self.height, self.width), 'uint8')

        colors = [r, g, b]

        input_buf = cl.Buffer(self.ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                              hostbuf=self.height_map.get_map())
        destination_r = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, r.nbytes)
        destination_g = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, r.nbytes)
        destination_b = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, r.nbytes)

        color_buffers = [destination_r, destination_g, destination_b]

        max_height = self.height_map.get_map().max()
        effective_sea_level = max_height * self._sea_level / 100
        events = []
        for color_buf in self._color_buffers:
            if color_buf.underwater:
                start = color_buf.start * effective_sea_level / 100
                end = color_buf.end * effective_sea_level / 100
            else:
                start = effective_sea_level + color_buf.start * (max_height-effective_sea_level) / 100
                end = effective_sea_level + color_buf.end * (max_height - effective_sea_level) / 100
            e = self.map_tools.ColoredMap(queue, (self.height, self.width), None,
                                          input_buf,
                                          destination_r,
                                          destination_g,
                                          destination_b,
                                          np.float32(start),
                                          np.float32(end),
                                          np.int32(np.array(color_buf.start_rgb)),
                                          np.int32(np.array(color_buf.end_rgb)),
                                          np.int32(self.width),
                                          np.int32(self.height),
                                          wait_for=events)
            events.append(e)

        for i in range(3):
            cl.enqueue_copy(queue, colors[i], color_buffers[i], wait_for=[events[-1]])
        b[self.river_map.get_map() > 200] = 255

        self.image = Image.merge("RGB", (
            Image.fromarray(r, "L"),
            Image.fromarray(g, "L"),
            Image.fromarray(b, "L")))
        self.valid = True

    def handle(self, observable, event: Event):
        super().handle(observable, event)
        if type(event) is SeaLevel:
            self._sea_level = event.sea_level
            self.notify(Invalidated())

    @classmethod
    def hex_to_rgb4(cls, hex_color):
        rgb = hex_to_rgb(hex_color)
        l = [x for x in rgb]
        l.append(0)
        return l
