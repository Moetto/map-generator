from enum import Enum


class AutoNumber(Enum):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj


class MapTypes(AutoNumber):
    HEIGHT_MAP = ()
    COLOR_MAP = ()
    GRADIENT_MAP = ()
    CONTINENT_MAP = ()
    RIVER_MAP = ()
    MEAN_HEIGHT_MAP = ()
