# Ensure all plugins are loaded.
import dexy.plugins

__version__ = "0.7.0"

from dexy.wrapper import Wrapper

def run(*args, **kwargs):
    wrapper = Wrapper(*args, **kwargs)
    wrapper.run()
    wrapper.report()
