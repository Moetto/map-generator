import random
from PIL import ImageTk
import configargparse
import re
import tkinter as tk
from tkinter import ttk
from map import Map


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


class UI(ttk.Frame):
    def __init__(self, parent, args):
        super().__init__(parent, padding="3 3 12 12")
        self.map = None
        self.args = args
        self.controls = ttk.Frame(self)
        self.controls.grid(column=0, row=0, sticky=(tk.W, tk.N))

        self.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)

        seed_label = tk.Label(self.controls, text="Seed")
        seed_label.grid(column=0, row=0, sticky=(tk.W, tk.N))
        self.seed_value = tk.StringVar(value=args.seed)
        self.entry_seed = ttk.Entry(self.controls, textvariable=self.seed_value)
        self.entry_seed.grid(column=1, row=0, sticky=(tk.W, tk.N))
        random_seed_label = tk.Label(self.controls, text="Random seed")
        random_seed_label.grid(column=0, row=1, sticky=(tk.W, tk.N))
        self.random_seed = tk.BooleanVar(value=False)
        random_seed_button = tk.Checkbutton(self.controls, command=self.random_seed_action, variable=self.random_seed)
        random_seed_button.grid(column=1, row=1, sticky=(tk.W, tk.N))

        vno = parent.register(self._validate_number_only)
        width_label = tk.Label(self.controls, text="Width")
        width_label.grid(column=0, row=2, sticky=(tk.W, tk.N))
        self.x_value = tk.IntVar(value=args.xSize)
        entry_x = ttk.Entry(self.controls, textvariable=self.x_value, validate='all', validatecommand=(vno, '%P'),
                            width=7)
        entry_x.grid(column=1, row=2)

        height_label = tk.Label(self.controls, text="Height")
        height_label.grid(column=0, row=3, sticky=(tk.W, tk.N))
        self.y_value = tk.IntVar(value=args.ySize)
        entry_y = ttk.Entry(self.controls, textvariable=self.y_value, validate='all', validatecommand=(vno, '%P'),
                            width=7)
        entry_y.grid(column=1, row=3)

        sea_label = tk.Label(self.controls, text="Sea level")
        sea_label.grid(column=0, row=4, sticky=(tk.W, tk.N))
        self.sea_level_value = tk.DoubleVar(value=args.sea_level)
        sea_level_slider = ttk.Scale(self.controls, from_=0, to=100, variable=self.sea_level_value,
                                     command=self.show_sea_level, orient="horizontal")
        sea_level_slider.grid(column=1, row=4)
        self.sea_level_display = tk.Label(self.controls, text=args.sea_level)
        self.sea_level_display.grid(column=0, row=4, sticky=(tk.E, tk.N))

        ttk.Button(self.controls, text="Generate height map", command=self.generate_height_map).grid(column=0, row=5)
        ttk.Button(self.controls, text="Generate map", command=self.generate_map).grid(column=1, row=5)

    def generate_map(self):
        self._generate_map()
        self.map.generate_map_image(self.args.sea_deep, self.args.sea_shore, self.args.ground_shore,
                                    self.args.ground_high)
        self._show_image(self.map.image)

    def generate_height_map(self):
        self._generate_map()
        self.map.generate_height_map_image()
        self._show_image(self.map.image)

    def _generate_map(self):
        if self.random_seed.get():
            self.seed_value.set(random.randint(0, 10000))

        self.map = Map(self.x_value.get(), self.y_value.get(), sea_level=int(self.sea_level_value.get()),
                       seed=self.seed_value.get(),
                       filters=self.args.filters)

    def _show_image(self, image):
        photo = ImageTk.PhotoImage(image)
        map_label = tk.Label(self, image=photo)
        map_label.image = photo
        map_label.grid(column=2, row=0)

    def random_seed_action(self):
        if self.random_seed.get():
            self.entry_seed.configure(state='disabled')
        else:
            self.entry_seed.configure(state='normal')

    @staticmethod
    def _validate_number_only(value):
        regex = re.compile("^\d+$")
        if regex.match(value):
            return True
        return False

    def show_sea_level(self, value):
        self.sea_level_display['text'] = int(float(value))




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

    root_window = tk.Tk()
    root_window.title("Random map generator")
    ui = UI(root_window, args)
    ui.grid()
    root_window.mainloop()


if __name__ == "__main__":
    main()
