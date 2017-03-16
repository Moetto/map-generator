import random

import click
from click import ParamType
from click_configfile import matches_section, SectionSchema, Param, ConfigFileReader

from controller import Controller
from main import _ScaleEffectPair
from ui import Gui


class FilterParamType(ParamType):
    name = "filter"

    def convert(self, value, param, ctx):
        try:
            values = value.split('/')

            if len(values) != 2:
                raise ValueError

            scale = float(values[0])
            magnitude = float(values[1])

            return _ScaleEffectPair(scale, magnitude)

        except ValueError:
            self.fail("%s is not two floats separated by '/'")

    def __repr__(self):
        return "FILTER"


class ConfigSectionSchema:
    @matches_section("maps")
    class MapConfig(SectionSchema):
        pass

    @matches_section("global")
    class GlobalMapConfig(SectionSchema):
        width = Param(type=click.INT, default=1200)
        height = Param(type=click.INT, default=1000)
        seed = Param(type=click.INT, default=random.Random().randint(0, 100000))
        sea_level = Param(type=click.INT, default=75)

    @matches_section("height map")
    class HeightMapConfig(SectionSchema):
        filters = Param(multiple=True, type=FilterParamType())
        seed = Param(type=click.INT)


class ConfigFileProcessor(ConfigFileReader):
    config_files = ["map.cfg"]
    config_section_schemas = [
        ConfigSectionSchema.MapConfig,
        ConfigSectionSchema.GlobalMapConfig,
        ConfigSectionSchema.HeightMapConfig
    ]


CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor.read_config())


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx):
    ctx.obj = Controller(ctx.default_map)


pass_controller = click.make_pass_decorator(Controller)

basic_options = [
    click.option("--width", "-w", default=1200),
    click.option("--height", "-h", default=1000)
]

height_map_options = [
    click.option("--filters", required=True, multiple=True, type=(str, float))
]


def add_options(options):
    def _add_options(func):
        for option in options:
            func = option(func)
        return func

    return _add_options


@cli.command()
@pass_controller
@click.pass_context
def gui(ctx, controller):
    Gui(controller).start()


@cli.command(context_settings=CONTEXT_SETTINGS)
@pass_controller
@click.pass_context
def generate(ctx, controller):
    controller.setup(ctx.default_map)
    for key in ctx.default_map.keys():
        print("{}: {}".format(key, ctx.default_map[key]))


if __name__ == "__main__":
    cli()
