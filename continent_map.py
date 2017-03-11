import numpy as np
from PIL import Image

from base_maps import Map
from height_map import HeightMap
from obeserver import Observer


class ContinentMap(Map, Observer):
    def __init__(self, width, height, sea_level: int, height_map: HeightMap):
        super().__init__(width, height)
        self._height_map = height_map
        self._sea_level = sea_level
        self._height_map.subscribe(self)
        self.generate()

    def set_sea_level(self, sea_level):
        self._sea_level = sea_level
        self.invalidate()

    def generate(self):
        if self.valid:
            return
        if not self._height_map.valid:
            self._height_map.generate()
        self.map = np.zeros_like(self._height_map.map)
        effective_sea_level = self._height_map.map.max() * self._sea_level / 100

        self.map[self._height_map.map > effective_sea_level] = 1
        self.valid = True
        self.image = Image.fromarray(self.map, "I")
