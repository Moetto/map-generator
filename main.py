import random
import re

import configargparse

from ui import Gui


def check_positive_integer(value):
    val = int(value)
    if val < 0:
        raise configargparse.ArgumentTypeError("{} is not positive integer".format(val))
    return val


def check_hex(value):
    pattern = re.compile('^([A-F0-9]{2}){3}$')
    if not pattern.match(value):
        raise configargparse.ArgumentTypeError("{} is not valid hex color code in format #AABBCC".format(value))
    return "#" + value


def scale_pair(value):
    values = value.split(',')
    pairs = []
    for value in values:
        pairs.append(_ScaleEffectPair.parse_pair(value))
    return pairs


class _ScaleEffectPair:
    def __init__(self, scale, effect):
        self.scale = int(scale)
        self.effect = float(effect)

    @staticmethod
    def parse_pair(value):
        scale, effect = value.split("/")
        return _ScaleEffectPair(scale, effect)

    def __str__(self):
        return "{} / {}".format(self.scale, self.effect)


def main():
    p = configargparse.ArgParser(default_config_files=['map.conf'])
    p.add('-c', '--config', required=False, is_config_file=True, help='Custom config file')
    p.add('-x', '--xSize', type=check_positive_integer)
    p.add('-y', '--ySize', type=check_positive_integer)
    p.add('--sea_level', type=int, default=75, help="Percentage of max height below which area is covered in water")
    p.add('--seed', default=random.randint(0, 10000))
    p.add('-f', '--filters', type=scale_pair)
    p.add('--sea_deep', type=check_hex)
    p.add('--sea_shore', type=check_hex)
    p.add('--ground_shore', type=check_hex)
    p.add('--ground_high', type=check_hex)

    args = p.parse_args()

    ui = Gui(args)
    ui.start()


if __name__ == "__main__":
    main()
