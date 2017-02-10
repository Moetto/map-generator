import numpy as np
import pyopencl as cl
import random

from webcolors import hex_to_rgb
from scipy.ndimage.morphology import binary_erosion
from PIL import Image
from random import Random


class Map:
    def __init__(self, size_x, size_y, filters, sea_level, seed=random.randint(1, 100000)):
        self.ctx = cl.create_some_context(interactive=False)
        self.queue = cl.CommandQueue(self.ctx)
        self.noise = cl.Program(self.ctx, open("noise/Noise.cl").read()).build()
        self.map_tools = cl.Program(self.ctx, open("maptools.cl").read()).build()
        self.queue = cl.CommandQueue(self.ctx)
        self.size_x = size_x
        self.size_y = size_y
        self.map = np.zeros((size_y, size_x), np.float32)
        self.height_map = None
        self.mean_height_map = None
        self.gradients = None
        self.gradient_image = None
        self.gradient_direction = None
        self.rivers = None
        self.rivers_image = None
        self.theoretical_max_height = 255  # (sum([pair.effect for pair in filters])) * 2
        self.sea_level = sea_level
        self.effective_sea_level = 0
        self.image = None
        self.random = Random(seed)

    def _random_pixel(self):
        return random.randint(0, self.size_y), random.randint(0, self.size_x)

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
            events.append(self.noise.HeightMap(self.queue, self.map.shape, None, destination_buf,
                                               np.int32(self.size_x), np.int32(self.size_y),
                                               np.int32(self.random.randint(0, 1000000)),
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

    def calculate_mean_height_map(self):
        if self.height_map is None:
            self.generate_height_map_image()
        self.mean_height_map = np.empty_like(self.height_map)
        input_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self.height_map)
        output_buf = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, size=self.mean_height_map.nbytes)

        event = self.map_tools.calculate_mean(self.queue, self.map.shape, None, input_buf, output_buf, np.int32(30),
                                              np.int32(self.size_x), np.int32(self.size_y))
        cl.enqueue_copy(self.queue, self.mean_height_map, output_buf, wait_for=[event])

    def calculate_gradient(self):
        if self.mean_height_map is None:
            self.calculate_mean_height_map()
        self.gradients = np.gradient(self.mean_height_map)
        self.gradient_direction = np.empty(self.map.shape, np.uint8)

        y_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self.gradients[0])
        x_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self.gradients[1])
        output_buf = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, size=self.map.nbytes)

        event = self.map_tools.gradient_direction(self.queue, self.gradient_direction.shape, None,
                                                  x_buf,
                                                  y_buf,
                                                  output_buf,
                                                  np.int32(self.size_x))
        cl.enqueue_copy(self.queue, self.gradient_direction, output_buf, wait_for=[event])
        self.gradient_image = Image.fromarray(self.gradient_direction * 35, 'P')

    def generate_rivers(self):
        if self.gradient_image is None:
            self.calculate_gradient()
        self.rivers = np.zeros(self.map.shape, np.int32)

        start_points = [self._random_pixel() for i in range(100)]
        x_points = [p[1] for p in start_points]
        y_points = [p[0] for p in start_points]

        gradient_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self.gradient_direction)
        river_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=self.rivers)
        start_points_x_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=np.int32(x_points))
        start_points_y_buf = cl.Buffer(self.ctx, cl.mem_flags.COPY_HOST_PTR, hostbuf=np.int32(y_points))

        event = self.map_tools.generate_rivers(self.queue, (len(start_points),), None,
                                               gradient_buf,
                                               river_buf,
                                               start_points_x_buf,
                                               start_points_y_buf,
                                               np.int32(self.size_x),
                                               np.int32(self.size_y))
        cl.enqueue_copy(self.queue, self.rivers, river_buf, wait_for=[event])
        self.rivers *= 10;
        self.rivers_image = Image.fromarray(self.rivers, 'I')

    def generate_map_image(self, sea_deep, sea_shore, ground_shore, ground_high):
        self.generate_height_map_image()
        self.generate_rivers()
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
            e = self.map_tools.ColoredMap(self.queue, (self.size_y, self.size_x), None, input_buf, color_bufs[i],
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
        b[self.rivers > 0] = 255

        self.image = Image.merge("RGB", (
            Image.fromarray(r, "L"),
            Image.fromarray(g, "L"),
            Image.fromarray(b, "L")))
