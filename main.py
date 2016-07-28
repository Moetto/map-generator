from noise import snoise2
import numpy as np
import random
from PIL import Image
import configargparse
import re
from webcolors import hex_to_rgb
from scipy.ndimage.morphology import binary_erosion


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
    def __init__(self, size_x, size_y, filters, sea_level, seed=10):
        self.size_x = size_x
        self.size_y = size_y
        self.grid = np.zeros((size_y, size_x), np.float32)
        self.theoretical_max_height = (sum([pair.effect for pair in filters])) * 2
        self.sea_level = sea_level

        random.seed(seed)
        offset = random.randint(0, 10000)
        mountain_scale = 100
        mountain_range = 1
        for x in range(size_x):
            for y in range(size_y):
                height = self.theoretical_max_height / 2
                for pair in filters:
                    height += snoise2((x + offset) / pair.scale, (y + offset) / pair.scale, 1) * pair.effect

                if height > sea_level:
                    height += abs(
                        snoise2((x + offset) / mountain_scale, (y + offset) / mountain_scale, 1) * mountain_range)

                self.grid[y, x] = height
        self.effective_sea_level = np.max(self.grid) * self.sea_level / 100

    @staticmethod
    def _calculate_gradient_value(value, start_value, end_value, start_rgb, end_rgb, channel):
        percentage = (value - start_value) / (end_value - start_value)
        return int(start_rgb[channel] * (1 - percentage) + end_rgb[channel] * percentage)

    def generate_mountain(self, area):
        """
        Generate mountain to given area
        :param area: bit mask of map area(s) to hold mountains
        """
        distance_map = np.zeros_like(self.grid)
        s = np.ones((3, 3))
        distance = 0.05
        while True:
            new_area = binary_erosion(area, s)
            edge = area - new_area
            if not np.any(edge):
                break
            distance_map[edge == 1] = distance
            area = new_area
            distance += 0.05
        self.theoretical_max_height += np.max(distance_map)
        self.grid = self.grid + distance_map

    def get_continents(self):
        mask = np.zeros_like(self.grid)
        mask[self.grid > self.sea_level / 100 * np.max(self.grid)] = 1
        Map.show_height_map(mask)
        return mask

    @staticmethod
    def show_height_map(grid):
        max_height = np.max(grid)
        height_map = np.copy(grid)
        for pixel in np.nditer(height_map, op_flags=['readwrite']):
            pixel[...] = 255 * pixel / max_height
        image = Image.fromarray(height_map, "F")
        image.show()

    def show_self(self, sea_deep, sea_shore, ground_shore, ground_high):
        sea_deep_rgb = hex_to_rgb(sea_deep)
        sea_shore_rgb = hex_to_rgb(sea_shore)
        ground_shore_rgb = hex_to_rgb(ground_shore)
        ground_high_rgb = hex_to_rgb(ground_high)
        rgb = []

        for i in range(3):
            rgb.append(np.zeros(self.grid.shape, 'uint8'))

        for y in range(self.size_y):
            for x in range(self.size_x):
                val = self.grid[y, x]
                if val > self.effective_sea_level:
                    start_value = self.effective_sea_level
                    end_value = self.theoretical_max_height
                    start_rgb = ground_shore_rgb
                    end_rgb = ground_high_rgb
                else:
                    start_value = 0
                    end_value = self.effective_sea_level
                    start_rgb = sea_deep_rgb
                    end_rgb = sea_shore_rgb

                for i in range(3):
                    rgb[i][y, x] = self._calculate_gradient_value(val, start_value, end_value, start_rgb, end_rgb, i)

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
    p.add('--sea_level', type=int, default=75, help="Percentage of max height below which area is covered in water")
    p.add('--seed', type=int, default=random.randint(0, 10000))
    p.add('-f', '--filters', type=scale_pair)
    p.add('--sea_deep', type=check_hex)
    p.add('--sea_shore', type=check_hex)
    p.add('--ground_shore', type=check_hex)
    p.add('--ground_high', type=check_hex)

    args = p.parse_args()
    print(args.seed)
    map = Map(size_x=args.xSize, size_y=args.ySize, sea_level=args.sea_level, seed=args.seed, filters=args.filters)
    map.generate_mountain(map.get_continents())
    map.show_self(args.sea_deep, args.sea_shore, args.ground_shore, args.ground_high)
    # map.show_height_map(map.grid)


if __name__ == "__main__":
    main()
