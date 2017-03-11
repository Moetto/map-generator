import random
import re
import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from controller import Controller
from maptypes import MapTypes


class Gui(ttk.Frame):
    def __init__(self, args, parent=tk.Tk()):
        super().__init__(parent, padding="3 3 12 12")
        self.parent = parent
        self.controller = Controller(args.xSize, args.ySize, args.filters, args.sea_level, args.seed)
        self.parent.title("Random map generator")
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
        random_seed_button = tk.Checkbutton(self.controls, command=self._random_seed_action, variable=self.random_seed)
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
                                     command=self._show_sea_level, orient="horizontal")
        sea_level_slider.grid(column=1, row=4)
        self.sea_level_display = tk.Label(self.controls, text=args.sea_level)
        self.sea_level_display.grid(column=0, row=4, sticky=(tk.E, tk.N))

        ttk.Button(self.controls, text="Show height map", command=self.show_height_map).grid(column=0, row=5)
        ttk.Button(self.controls, text="Show map", command=self.show_color_map).grid(column=1, row=5)
        ttk.Button(self.controls, text="Show continents", command=self.show_continent_map).grid(column=1,
                                                                                                       row=6)
        ttk.Button(self.controls, text="Show gradient map", command=self.show_gradient_map).grid(row=7, column=0)
        ttk.Button(self.controls, text="Show waterfall map", command=self.show_rivers).grid(row=8, column=0)

    def start(self):
        self._show_map(MapTypes.COLOR_MAP)
        self.parent.mainloop()

    def _show_map(self, map_type):
        self._set_map_parameters()
        self._show_image(self.controller.get_map_image(map_type))

    def show_color_map(self):
        self._show_map(MapTypes.COLOR_MAP)

    def show_height_map(self):
        self._show_map(MapTypes.HEIGHT_MAP)

    def show_continent_map(self):
        self._show_map(MapTypes.CONTINENT_MAP)

    def _set_map_parameters(self):
        if self.random_seed.get():
            self.seed_value.set(random.randint(0, 10000))
        self.controller.set_seed(self.seed_value.get())
        self.controller.set_sea_level(self.sea_level_value.get())

    def show_gradient_map(self):
        self._show_map(MapTypes.GRADIENT_MAP)

    def show_rivers(self):
        self._show_map(MapTypes.RIVER_MAP)

    def _show_image(self, image):
        photo = ImageTk.PhotoImage(image)
        map_label = tk.Label(self, image=photo)
        map_label.image = photo
        map_label.grid(column=2, row=0)

    def _random_seed_action(self):
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

    def _show_sea_level(self, value):
        self.sea_level_display['text'] = int(float(value))
