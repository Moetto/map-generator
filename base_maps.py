import pyopencl as cl
from PIL import Image

from obeserver import Observable


class Map(Observable):
    def __init__(self, width: int, height: int):
        super().__init__()
        self.width = width
        self.height = height
        self.map = None
        self.image = None
        self.valid = False

    def generate(self) -> None:
        raise NotImplemented

    def get_image(self) -> Image:
        if not self.valid:
            self.generate()
        return self.image

    def notify(self, invalid):
        self.invalidate()
        self.valid = False


class CLMap(Map):
    def __init__(self, width: int, height: int, context: cl.Context):
        super().__init__(width, height)
        self.ctx = context
