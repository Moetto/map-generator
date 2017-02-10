import re
import random
import tkinter as tk
from PIL import ImageTk
from tkinter import ttk
from map import Map


class UI(ttk.Frame):
    def __init__(self, args, parent=tk.Tk()):
        super().__init__(parent, padding="3 3 12 12")
        self.parent = parent
        self.parent.title("Random map generator")
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
        ttk.Button(self.controls, text="Generate gradient map", command=self.show_gradient).grid(row=6, column=0)
        ttk.Button(self.controls, text="Generate river map", command=self.show_rivers).grid(row=7, column=0)

    def start(self):
        self.parent.mainloop()

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

    def show_gradient(self):
        if self.map is None:
            self._generate_map()
        if self.map.gradient_image is None:
            self.map.calculate_gradient()
        self._show_image(self.map.gradient_image)

    def show_rivers(self):
        if self.map is None:
            self._generate_map()
        if self.map.rivers_image is None:
            self.map.generate_rivers()
        self._show_image(self.map.rivers_image)

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
