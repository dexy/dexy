from dexy.constants import Constants
from dexy.reporter import Reporter
from dexy.tests.utils import tempdir
from dexy.utils import remove_all_handlers
from dexy.utils import get_log
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
import os

def setup():
    log = get_log(logsdir=None, logfile=None)
    remove_all_handlers(log)

def test_logging_to_stderr():
    r = Reporter(None, None, dbfile=None)
    assert len(r.log.handlers) == 1
    assert isinstance(r.log.handlers[0], StreamHandler)
    assert not isinstance(r.log.handlers[0], RotatingFileHandler)
    remove_all_handlers(r.log)

def test_logging_to_file():
    with tempdir():
        os.mkdir(Constants.DEFAULT_LDIR)
        r = Reporter()
        assert len(r.log.handlers) == 1
        assert isinstance(r.log.handlers[0], RotatingFileHandler)
        remove_all_handlers(r.log)
