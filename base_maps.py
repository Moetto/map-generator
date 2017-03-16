import pyopencl as cl
from PIL import Image

from events import Invalidated
from observables import Observable, Observer, Event


class Map(Observable, Observer):
    def __init__(self, controller: Observable, width: int, height: int):
        super().__init__()
        controller.subscribe(self)
        self.width = width
        self.height = height
        self._map = None
        self.image = None
        self.valid = False

    def generate(self) -> None:
        raise NotImplemented

    def get_image(self) -> Image:
        if not self.valid:
            self.generate()
        return self.image

    def get_map(self):
        if not self.valid:
            self.generate()
        return self._map

    def handle(self, observable, event: Event):
        if type(event) is Invalidated:
            self.valid = False
            self.notify(event)

    def setup(self, config):
        print("Setting up {} with config keys {}".format(self.__class__, config.keys()))


class CLMap(Map):
    def __init__(self, controller: Observable, width: int, height: int, context: cl.Context):
        super().__init__(controller, width, height)
        self.ctx = context
