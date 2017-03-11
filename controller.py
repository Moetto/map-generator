import random

import numpy as np
import pyopencl as cl
from PIL import Image
from scipy.ndimage.morphology import binary_erosion

from color_map import ColorMap, ColorRange
from continent_map import ContinentMap
from gradient_map import GradientMap
from height_map import HeightMap
from maptypes import MapTypes
from mean_height_map import MeanHeightMap
from river_map import RiverMap


class Controller:
    def __init__(self, width, height, filters, sea_level, seed=random.randint(1, 100000)):
        self.ctx = cl.create_some_context(interactive=False)
        self.width = width
        self.height = height
        self.seed = seed
        self.sea_level = sea_level
        height_map = HeightMap(self.width, self.height, self.ctx, [], self.seed)
        mean_height_map = MeanHeightMap(self.width, self.height, self.ctx, height_map)
        gradient_map = GradientMap(self.width, self.height, self.ctx, mean_height_map)
        continent_map = ContinentMap(self.width, self.height, self.sea_level, height_map)
        river_map = RiverMap(self.width, self.height, self.ctx, gradient_map, continent_map)

        self._maps = {
            MapTypes.HEIGHT_MAP: height_map,
            MapTypes.RIVER_MAP: river_map,
            MapTypes.COLOR_MAP: ColorMap(self.width, self.height, self.ctx, height_map, river_map,
                                         [ColorRange(0, self.sea_level, [30, 80, 160, 0], [91, 154, 255, 0]),
                                          ColorRange(self.sea_level, 100, [255, 243, 114, 0], [76, 211, 27, 0])]),
            MapTypes.CONTINENT_MAP: continent_map,
            MapTypes.MEAN_HEIGHT_MAP: mean_height_map,
            MapTypes.GRADIENT_MAP: gradient_map,
        }
        self._seedable_maps = [height_map]
        self.theoretical_max_height = 255  # (sum([pair.effect for pair in filters])) * 2

    def get_map_image(self, map_type: MapTypes) -> Image:
        return self._maps[map_type].get_image()

    def set_seed(self, seed):
        if seed != self.seed:
            self.seed = seed
            for seedable in self._seedable_maps:
                seedable.set_seed(seed)

    def set_sea_level(self, sea_level):
        if sea_level != self.sea_level:
            self.sea_level = sea_level
            self._maps[MapTypes.CONTINENT_MAP].set_sea_level(sea_level)

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
        self.map += distance_map
