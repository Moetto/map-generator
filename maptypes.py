"""
class AutoNumber(Enum):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

"""
from enum import Enum


class MapTypes(Enum):
    HEIGHT_MAP = "height map"
    COLOR_MAP = "color map"
    GRADIENT_MAP = "gradient map"
    CONTINENT_MAP = "continent map"
    RIVER_MAP = "river map"
    MEAN_HEIGHT_MAP = "mean height map"
