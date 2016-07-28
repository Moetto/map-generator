from noise import snoise2
import numpy
import random
from PIL import Image
import configargparse
import re
from webcolors import hex_to_rgb


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


class Map:
    def __init__(self, size_x, size_y, filters, seed=10):
        self.size_x = size_x
        self.size_y = size_y
        self.grid = numpy.zeros((size_y, size_x), numpy.float32)
        self.max_height = sum([pair.effect for pair in filters]) * 2

        random.seed(seed)
        offset = random.randint(0, 10000)
        for x in range(size_x):
            for y in range(size_y):
                height = self.max_height / 2
                for pair in filters:
                    height += snoise2((x + offset) / pair.scale, (y + offset) / pair.scale, 1) * pair.effect
                self.grid[y][x] = height

    @staticmethod
    def _calculate_gradient_value(value, start_value, end_value, start_rgb, end_rgb, channel):
        percentage = (value - start_value) / (end_value - start_value)
        return int(start_rgb[channel] * (1 - percentage) + end_rgb[channel] * percentage)

    def show_self(self, sea_deep, sea_shore, ground_shore, ground_high, sea_level=0.5):
        sea_deep_rgb = hex_to_rgb(sea_deep)
        sea_shore_rgb = hex_to_rgb(sea_shore)
        ground_shore_rgb = hex_to_rgb(ground_shore)
        ground_high_rgb = hex_to_rgb(ground_high)
        r = numpy.zeros((self.size_y, self.size_x), dtype='uint8')
        g = numpy.zeros((self.size_y, self.size_x), dtype='uint8')
        b = numpy.zeros((self.size_y, self.size_x), dtype='uint8')
        rgb = [r, g, b]
        for y in range(self.size_y):
            for x in range(self.size_x):
                for i in range(3):
                    val = self.grid[y][x]
                    if val > sea_level:
                        start_value = sea_level
                        end_value = self.max_height
                        start_rgb = ground_shore_rgb
                        end_rgb = ground_high_rgb
                    else:
                        start_value = 0
                        end_value = sea_level
                        start_rgb = sea_deep_rgb
                        end_rgb = sea_shore_rgb

                    rgb[i][y][x] = self._calculate_gradient_value(self.grid[y][x], start_value, end_value, start_rgb,
                                                                  end_rgb, i)
        image = Image.merge("RGB", (
            Image.fromarray(rgb[0], "L"),
            Image.fromarray(rgb[1], "L"),
            Image.fromarray(rgb[2], "L")))
        image.show()


def main():
    p = configargparse.ArgParser(default_config_files='map.conf')
    p.add('-c', '--config', required=False, is_config_file=True, help='Custom config file')
    p.add('-x', '--xSize', type=check_positive_integer)
    p.add('-y', '--ySize', type=check_positive_integer)
    p.add('--sea_level', type=float, default=0.0)
    p.add('--seed', type=int, default=random.randint(0, 10000))
    p.add('-f', '--filters', type=scale_pair)
    p.add('--sea_deep', type=check_hex)
    p.add('--sea_shore', type=check_hex)
    p.add('--ground_shore', type=check_hex)
    p.add('--ground_high', type=check_hex)

    args = p.parse_args()
    print(args.seed)
    map = Map(size_x=args.xSize, size_y=args.ySize, seed=args.seed, filters=args.filters)
    map.show_self(args.sea_deep, args.sea_shore, args.ground_shore, args.ground_high, args.sea_level)


if __name__ == "__main__":
    main()
