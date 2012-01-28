from dexy.constants import Constants
import dexy.reporter
import dexy
import dexy.artifact
import dexy.dexy_filter
import inspect
import os
import sys

NULL_LOGGER = Constants.NULL_LOGGER
INSTALL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def database_classes(log=NULL_LOGGER):
    """
    Return a dict whose keys are database class names and whose values are the
    corresponding classes.
    """
    database_classes = {}

    d = os.path.join(INSTALL_DIR, 'dexy', 'databases')
    for f in os.listdir(d):
        if f.endswith(".py") and f not in ["base.py", "__init__.py"]:
            log.debug("Loading databases in %s" % os.path.join(d, f))
            basename = f.replace(".py", "")
            module = "dexy.databases.%s" % basename
            try:
                __import__(module)
            except ImportError as e:
                log.warn("database defined in %s are not available: %s" % (module, e))

            if not sys.modules.has_key(module):
                continue

            mod = sys.modules[module]

            for k in dir(mod):
                klass = mod.__dict__[k]
                if inspect.isclass(klass) and not (klass == dexy.database.Database) and issubclass(klass, dexy.database.Database):
                    if database_classes.has_key(k):
                        raise Exception("duplicate database class name %s called from %s in %s" % (k, f, d))
                    database_classes[klass.__name__] = klass

    return database_classes

def artifact_classes(log=NULL_LOGGER):
    """
    Return a dict whose keys are artifact class names and whose values are the
    corresponding classes.
    """
    artifact_classes = {}

    d = os.path.join(INSTALL_DIR, 'dexy', 'artifacts')
    for f in os.listdir(d):
        if f.endswith(".py") and f not in ["base.py", "__init__.py"]:
            log.debug("Loading artifacts in %s" % os.path.join(d, f))
            basename = f.replace(".py", "")
            module = "dexy.artifacts.%s" % basename
            try:
                __import__(module)
            except ImportError as e:
                log.warn("artifact defined in %s are not available: %s" % (module, e))

            if not sys.modules.has_key(module):
                continue

            mod = sys.modules[module]

            for k in dir(mod):
                klass = mod.__dict__[k]
                if inspect.isclass(klass) and not (klass == dexy.artifact.Artifact) and issubclass(klass, dexy.artifact.Artifact):
                    if not artifact_classes.has_key(k):
                        artifact_classes[klass.__name__] = klass

    return artifact_classes

def get_filter_by_name(name, filter_list=None):
    if not filter_list:
        # populate the filter list ourselves if not supplied...
        filter_list = filters()

    classes = [k for k in filter_list if k.__name__ == name]
    if len(classes) == 0:
        raise Exception("no filter class %s found" % name)
    return classes[0]

def get_filter_for_alias(alias, filter_list=None):
    if not filter_list:
        # populate the filter list ourselves if not supplied...
        filter_list = filters()

    if filter_list.has_key(alias):
        return filter_list[alias]
    elif alias.startswith("-") or alias.startswith("alias-") or alias.startswith("al-") or alias in ['al', 'alias']:
        return dexy.dexy_filter.DexyFilter
    else:
        raise Exception("filter alias '%s' not found or not available" % alias)

def filters(log=NULL_LOGGER):
    """
    Returns a dict whose keys are all supported filter alises and whose values
    are the corresponding filter classes.
    """
    dexy_filters = ('dexy.filters', os.path.join(dexy.__path__[0], 'filters'))
    proj_filters = ('filters', os.path.abspath(os.path.join(os.curdir, 'filters')))
    user_filters = ('dexy_filters', os.path.expanduser(os.path.join('~', 'dexy_filters')))

    filter_dirs = []

    if os.path.exists(proj_filters[1]):
        init_py_file = os.path.join(proj_filters[1], "__init__.py")
        path = os.path.abspath(os.curdir)
        if not os.path.exists(init_py_file):
            print "You need to create a __init__.py file in", proj_filters[1], "in order for filters to be available"
        elif not path in sys.path:
            print "Adding", path, "to python sys.path so your custom filters in", proj_filters[1], "will be available"
            sys.path.append(path)

    if os.path.exists(user_filters[1]):
        init_py_file = os.path.join(user_filters[1], "__init__.py")
        path = os.path.expanduser('~')
        if not os.path.exists(init_py_file):
            print "You need to create a __init__.py file in", user_filters[1], "in order for filters to be available"
        elif not path in sys.path:
            print "Adding", path, "to python sys.path so your custom filters in", user_filters[1], "will be available"
            sys.path.append(path)

    for pkg, d in [dexy_filters, proj_filters, user_filters]:
         if os.path.exists(d) and (pkg, d) not in filter_dirs:
             filter_dirs.append((pkg, d))

    filters = {}

    for a in dexy.dexy_filter.DexyFilter.ALIASES:
        filters[a] = dexy.dexy_filter.DexyFilter

    for pkg, d in filter_dirs:
        log.info("Automatically loading all %s found in %s" % (pkg, d))
        for f in os.listdir(d):
            if f.endswith(".py") and f not in ["base.py", "__init__.py"]:
                log.info("Loading filters in %s" % os.path.join(d, f))
                basename = f.replace(".py", "")
                modname = "%s.%s" % (pkg, basename)

                try:
                    __import__(modname)
                except ImportError as e:
                    log.warn("filters defined in %s are not available: %s" % (modname, e))

                if not sys.modules.has_key(modname):
                    continue

                mod = sys.modules[modname]

                for k in dir(mod):
                    klass = mod.__dict__[k]

                    is_class = inspect.isclass(klass)

                    if is_class and issubclass(klass, dexy.dexy_filter.DexyFilter) and (klass.__module__ == modname):
                        if not klass.ALIASES:
                            log.info("class %s is not available because it has no aliases" % klass.__name__)
                        elif not klass.executable_present():
                            log.info("class %s is not available because %s not found" %
                                          (klass.__name__, klass.executable()))
                        elif not klass.enabled():
                            log.info("class %s is not available because it is not enabled" %
                                          (klass.__name__))
                        else:
                            for a in klass.ALIASES:
                                if filters.has_key(a):
                                    raise Exception("duplicate key %s called from %s in %s" % (a, k, f))
                                filters[a] = klass
                                log.info("registered alias %s for class %s" % (a, k))
        log.info("...finished loading filters from %s" % d)
    return filters

def reporters(log=NULL_LOGGER):
    """
    Returns a dict of reporter names and classes.
    """
    # Reporters that come with dexy are installed in the reporters/ subdir:
    d1 = os.path.abspath(os.path.join(INSTALL_DIR, 'reporters'))

    # Custom reporters for a project may be placed in a reporters/ dir in the project:
    d2 = os.path.abspath(os.path.join(os.curdir, 'reporters'))

    if d1 == d2 or not os.path.exists(d2):
        reporter_dirs = [d1]
    else:
        reporter_dirs = [d1,d2]

    reporters = {}
    for d in reporter_dirs:
        log.info("Loading reporters in dir %s" % d)
        for f in os.listdir(d):
            if f.endswith(".py") and f not in ["base.py", "__init__.py"]:
                log.info("Loading reporters in %s" % os.path.join(d, f))
                basename = f.replace(".py", "")
                module = "reporters.%s" % basename

                try:
                    __import__(module)
                except ImportError as e:
                    log.warn("reporters defined in %s are not available: %s" % (module, e))

                if not sys.modules.has_key(module):
                    continue

                mod = sys.modules[module]

                for k in dir(mod):
                    klass = mod.__dict__[k]
                    if inspect.isclass(klass) and not (klass == dexy.reporter.Reporter) and issubclass(klass, dexy.reporter.Reporter):
                        reporters[klass.__name__] = klass
    return reporters

def reports_dirs(log=NULL_LOGGER):
    """
    Returns a list of all directories which reporters declare that they use.
    """
    return [r.REPORTS_DIR for r in reporters(log).values() if r.REPORTS_DIR and not r.REPORTS_DIR.startswith("logs/")]
