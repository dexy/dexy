import inspect
import dexy.exceptions

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

            if not inspect.getdoc(cls):
                breadcrumbs = " -> ".join(t.__name__ for t in inspect.getmro(cls)[:-1][::-1])
                raise dexy.exceptions.InternalDexyProblem("no docstring found for dexy plugin '%s' (%s, defined in %s), docstrings are required" % (cls.__name__, breadcrumbs, cls.__module__))

            basenames = [k.__name__ for k in cls.__bases__]

            if hasattr(cls, 'ALIASES'):
                for alias in cls.ALIASES:

                    # Namespace templates by their plugin name (after dexy_)
                    if 'Template' in basenames:
                        if cls.__module__ == 'dexy.plugins.templates':
                            prefix = 'dexy'
                        else:
                            prefix = cls.__module__.replace("dexy_", "")
                        alias = "%s:%s" % (prefix, alias)

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
