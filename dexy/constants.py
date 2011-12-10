import logging

try:
    from logging import NullHandler
except:
    # NullHandler not in Python 2.6
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

class Constants():

    # Create a null logger for testing and other times when we don't want to
    # worry about logfiles
    NULL_LOGGER = logging.getLogger("null")
    NULL_LOGGER.addHandler(NullHandler())
    NULL_LOGGER.propagate = 0

    LOGLEVELS = {
        'DEBUG' : logging.DEBUG,
        'INFO' : logging.INFO,
        'WARNING' : logging.WARNING,
        'ERROR' : logging.ERROR,
        'CRITICAL' : logging.CRITICAL
    }

    DEFAULT_ACLASS = 'FileSystemJsonArtifact'
    DEFAULT_ADIR = 'artifacts'
    DEFAULT_COMMAND = 'dexy'
    DEFAULT_CONFIG = '.dexy'
    DEFAULT_LDIR = 'logs'
    DEFAULT_REPORTS = "Output LongOutput Run Source"
    DEFAULT_LOGGER_NAME = 'dexy'
    DEFAULT_LFILE = 'dexy.log'
    DEFAULT_DBCLASS = 'SqliteDatabase'
    DEFAULT_DBFILE = "db.sql"
    DEFAULT_LOGLEVEL="DEBUG"
    DEFAULT_LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Directories with this name should be excluded anywhere
    EXCLUDE_DIRS_ALL_LEVELS = ['.bzr', '.hg', '.git', '.svn']

    # Directories with these names should be excluded only at the project root
    EXCLUDE_DIRS_ROOT = ['ignore']

    EXCLUDE_HELP = """Specify directory names to exclude from processing by dexy.
    Directories with these names will be skipped anywhere in your project.
    The following patterns are automatically excluded anywhere in your project: %s.
    The directories designated for artifacts and logs are automatically excluded,
    and the following directory names are also excluded if they appear at the root
    level of your project: %s.
    Any directory with a file named .nodexy will be skipped, and subdirectories of this will also be skipped.
    """ % (", ".join(EXCLUDE_DIRS_ALL_LEVELS), ", ".join(EXCLUDE_DIRS_ROOT))

    ARTIFACT_HASH_WHITELIST = [
        'args',
        'artifact_class_source',
        'ctime',
        'dexy_version',
        'dirty',
        'dirty_string',
        'ext',
        'filter_name',
        'filter_source',
        'filter_version',
        'inode',
        'input_data_dict',
        'input_ext',
        'inputs',
        'key',
        'mtime',
        'next_filter_name'
    ]
