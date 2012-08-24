# Ensure all plugins are loaded.
import dexy.plugins

__version__ = "0.7.0"

from dexy.doc import PatternDoc
from dexy.runner import Runner
from dexy.params import RunParams

def conf(*args, **kwargs):
    docs = []

    # Strip out anything in kwargs that isn't a run parameter.
    if kwargs.has_key('docs'):
        docs_from_kwargs = kwargs['docs']
        del kwargs['docs']
    else:
        docs_from_kwargs = []

    # Pass all remaining kwargs to RunParams generator
    params = RunParams(kwargs)

    for pattern in args:
        docs.append(PatternDoc(pattern, params))

    docs = docs + docs_from_kwargs

    runner = Runner()
    runner.setup()
    runner.run(*docs)
    runner.report()
