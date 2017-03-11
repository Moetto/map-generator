from observables import Event


class Invalidated(Event):
    pass


class Seed(Event):
    def __init__(self, seed):
        self.seed = seed


class SeaLevel(Event):
    def __init__(self, sea_level):
        self.sea_level = sea_level
