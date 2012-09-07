import inspect
"""
Plugins can create custom versions of:

filters
reporters
commands
data
metadata

Dexy will look in standard locations (TODO - allow disabling any of these)
   - dexy package's own plugin directory
   - all installed packages whose names start with 'dexy-' or 'dexy_'
   - system-wide plugin directory
   - user-level plugin directory
   - project plugin directory

Also can explicitly import a package and its plugins will be loaded.
"""
class PluginMeta(type):
    """
    Based on http://martyalchin.com/2008/jan/10/simple-plugin-framework/
    """
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.plugins = []
            cls.aliases = {}
            cls.source = {}
            cls.source[cls.__name__] = inspect.getsource(cls)
        else:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            cls.plugins.append(cls)
            cls.source[cls.__name__] = inspect.getsource(cls)
            if hasattr(cls, 'ALIASES'):
                for alias in cls.ALIASES:
                    if alias in cls.aliases:
                        raise Exception("duplicate alias %s found in %s, already present in %s" % (alias, cls.__name__, cls.aliases[alias].__name__))
                    cls.aliases[alias] = cls
            elif hasattr(cls, 'NAMESPACE'):
                cls.aliases[cls.NAMESPACE] = cls


class Command:
    NAMESPACE = None
    DEFAULT_COMMAND = None
    __metaclass__ = PluginMeta

    @classmethod
    def is_active(klass):
        return True
