import random

import pyopencl as cl
from PIL import Image

from color_map import ColorMap, ColorRange
from continent_map import ContinentMap
from events import Seed, SeaLevel
from gradient_map import GradientMap
from height_map import HeightMap
from maptypes import MapTypes
from mean_height_map import MeanHeightMap
from observables import Observable
from river_map import RiverMap


class Controller(Observable):
    def __init__(self, width, height, filters, sea_level, seed=random.randint(1, 100000)):
        super().__init__()
        self.ctx = cl.create_some_context(interactive=False)
        self.width = width
        self.height = height
        self.seed = seed
        self.sea_level = sea_level
        height_map = HeightMap(self, self.width, self.height, self.ctx, filters, self.seed)
        mean_height_map = MeanHeightMap(self, self.width, self.height, self.ctx, height_map)
        gradient_map = GradientMap(self, self.width, self.height, self.ctx, mean_height_map)
        continent_map = ContinentMap(self, self.width, self.height, self.sea_level, height_map)
        river_map = RiverMap(self, self.width, self.height, self.ctx, gradient_map, continent_map)

        self._maps = {
            MapTypes.HEIGHT_MAP: height_map,
            MapTypes.RIVER_MAP: river_map,
            MapTypes.COLOR_MAP: ColorMap(self, self.width, self.height, self.ctx, height_map, river_map, sea_level,
                                         [ColorRange(0, 100, True, [30, 80, 160, 0], [91, 154, 255, 0]),
                                          ColorRange(0, 30, False, [255, 243, 114, 0], [76, 211, 27, 0]),
                                          ColorRange(30, 100, False, [76, 211, 27, 0], [55, 122, 33, 0]),
                                          ]),
            MapTypes.CONTINENT_MAP: continent_map,
            MapTypes.MEAN_HEIGHT_MAP: mean_height_map,
            MapTypes.GRADIENT_MAP: gradient_map,
        }

    def get_map_image(self, map_type: MapTypes) -> Image:
        return self._maps[map_type].get_image()

    def set_seed(self, seed):
        if seed != self.seed:
            self.seed = seed
            self.notify(Seed(seed))

    def set_sea_level(self, sea_level):
        if sea_level != self.sea_level:
            self.sea_level = sea_level
            self.notify(SeaLevel(sea_level))
