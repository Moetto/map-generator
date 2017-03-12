from cl_utils import CLUtils
from height_map_filter import HeightMapFilter


class IslandMapFilter(HeightMapFilter):
    def __init__(self, ctx):
        super().__init__(ctx, CLUtils.load_program(ctx, "island_filter.cl"))
