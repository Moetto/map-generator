import numpy as np
from PIL import Image

from base_maps import Map
from events import Invalidated, SeaLevel
from height_map import HeightMap
from observables import Observable, Event


class ContinentMap(Map):
    def __init__(self, controller: Observable, width, height, sea_level: int, height_map: HeightMap):
        super().__init__(controller, width, height)
        self._height_map = height_map
        self._sea_level = sea_level
        self._height_map.subscribe(self)
        self.generate()

    def set_sea_level(self, sea_level):
        self._sea_level = sea_level
        self.notify(Invalidated())

    def generate(self):
        if self.valid:
            return
        self._map = np.zeros_like(self._height_map.get_map())
        effective_sea_level = self._height_map.get_map().max() * self._sea_level / 100

        self._map[self._height_map.get_map() > effective_sea_level] = 1
        self.valid = True
        self.image = Image.fromarray(self._map, "I")

    def handle(self, observable, event: Event):
        super().handle(observable, event)
        if type(event) is SeaLevel:
            self._sea_level = event.sea_level
            self.notify(Invalidated())
