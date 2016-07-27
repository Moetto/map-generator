from noise import snoise2
import numpy
from random import randint
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


class Map:
    SEA = " "
    SHORE = "~"
    LAND = "x"
    EMPTY = " "

    def __init__(self, size_x=50, size_y=50, seed=10, scale=100, scale2=50):
        self.size_x = size_x
        self.size_y = size_y
        self.grid = numpy.zeros((size_y, size_x), numpy.float32)
        for x in range(size_x):
            for y in range(size_y):
                height = snoise2((x + seed) / scale, (y + seed) / scale, 1) + 1.1 + \
                         snoise2((x + seed) / scale2, (y + seed) / scale2, 1) / 10
                # self.grid[y][x] = self.LAND if height > sea_height else self.SEA
                self.grid[y][x] = height

    def print_self(self):
        print(" " + "".join(["-" for i in range(self.size_x)]) + " ")
        for row in self.grid:
            print("|" + "".join(row) + "|")
        print(" " + "".join(["-" for i in range(self.size_x)]) + " ")

    def _calculate_gradient_value(self, value, start_value, end_value, start_rgb, end_rgb, channel):
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
                        end_value = 2.2
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
    p.add('--seed', type=int, default=randint(0, 10000))
    p.add('-s', '--scale', type=check_positive_integer, default=100)
    p.add('-s2', '--scale2', type=check_positive_integer, default=50)
    p.add('--sea_deep', type=check_hex)
    p.add('--sea_shore', type=check_hex)
    p.add('--ground_shore', type=check_hex)
    p.add('--ground_high', type=check_hex)

    args = p.parse_args()
    map = Map(size_x=args.xSize, size_y=args.ySize, seed=args.seed, scale=args.scale, scale2=args.scale2)
    map.show_self(args.sea_deep, args.sea_shore, args.ground_shore, args.ground_high, args.sea_level)


if __name__ == "__main__":
    main()
