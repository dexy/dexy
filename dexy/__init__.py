# Ensure all plugins are loaded.
import dexy.plugins

__version__ = "0.7.0"

from dexy.doc import PatternDoc
from dexy.doc import Doc
from dexy.runner import Runner
from dexy.params import RunParams
import logging
import logging.handlers

def conf(*args, **kwargs):
    docs = []
    params = RunParams(**kwargs)

    runner = Runner(params)
    runner.setup()

    log = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler(params.log_path, encoding="UTF-8")
    log.addHandler(handler)
    log.propagate = 0

    for arg in args:
        if isinstance(arg, Doc):
            docs.append(arg)
        else:
            doc = PatternDoc(arg, params=params, log=log)
            docs.append(doc)

    runner.run(*docs)
    runner.report()

    print "dexy has run!"
