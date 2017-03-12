import pyopencl as cl


class CLUtils:
    @staticmethod
    def load_program(ctx, filename):
        return cl.Program(ctx, open(filename).read()).build()
