# Ensure all plugins are loaded.
import dexy.plugins

__version__ = "0.7.0"

from dexy.doc import PatternDoc
from dexy.runner import Runner
from dexy.params import RunParams
import logging
import logging.handlers

def conf(*args, **kwargs):
    docs = []

    # Strip out anything in kwargs that isn't a run parameter.

    # Strip out any pre-made doc objects
    if kwargs.has_key('docs'):
        docs_from_kwargs = kwargs['docs']
        del kwargs['docs']
    else:
        docs_from_kwargs = []

    # Pass all remaining kwargs to RunParams generator
    params = RunParams(**kwargs)

    runner = Runner(params)
    runner.setup()

    log = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler(params.log_path, encoding="UTF-8")
    log.addHandler(handler)
    log.propagate = 0

    for pattern in args:
        docs.append(PatternDoc(pattern, params=params, log=log))

    docs = docs + docs_from_kwargs

    runner.run(*docs)
    runner.report()

    print "dexy has run!"
