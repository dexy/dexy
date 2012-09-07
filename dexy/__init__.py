# Ensure all plugins are loaded.
import dexy.plugins

__version__ = "0.7.0"

from dexy.runner import Runner
from dexy.params import RunParams

def run(*args, **kwargs):
    params = RunParams(**kwargs)

    runner = Runner(params, args)
    runner.run()
    runner.report()
