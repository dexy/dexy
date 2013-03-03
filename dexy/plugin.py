import dexy.exceptions
import inspect
import json
import os
import sys
import yaml

class Plugin(object):
    """
    Base class for plugins. Define *instance* methods shared by plugins here.
    """
    def help(self):
        return inspect.getdoc(self.__class__)

    def json_info(self):
        return json.dumps(self.info())

    def info(self):
        return {}

    def setting(self, name_hyphen):
        if name_hyphen in self._settings:
            value = self._settings[name_hyphen][1]
        else:
            name_underscore = name_hyphen.replace("-", "_")
            if name_underscore in self._settings:
                value = self._settings[name_underscore][1]
            else:
                if name_underscore == name_hyphen:
                    msg = "no setting named %s" % name_hyphen
                else:
                    msg = "no setting named '%s' or '%s'"
                    msg = msg % (name_hyphen, name_underscore)
                raise Exception(msg)

        if hasattr(value, 'startswith') and value.startswith("$"):
            env_var = value.lstrip("$")
            if os.environ.has_key(env_var):
                return os.getenv(env_var)
            else:
                raise dexy.exceptions.UserFeedback("'%s' is not defined in your environment" % env_var)
        elif hasattr(value, 'startswith') and value.startswith("\$"):
            return value.replace("\$", "$")
        else:
            return value

    def has_setting(self, name):
        return self._settings.has_key(name)

    def setting_values(self, skip=None):
        """
        Returns dict of all setting values (removes the helpstrings)
        """
        if not skip:
            skip = []
        return dict((k, v[1]) for k, v in self._settings.iteritems() if not k in skip)

    def update_settings(self, new_settings):
        self.__class__.class_update_settings(self, new_settings, False)

class PluginMeta(type):
    """
    Base meta class for anything plugin-able.
    """
    def __init__(cls, name, bases, attrs):
        assert issubclass(cls, Plugin), "%s should inherit from class Plugin" % name
        if '__metaclass__' in attrs:
            cls.plugins = {}
        else:
            assert hasattr(cls, 'plugins')
            cls.register_plugin(cls.ALIASES, cls, {})

    def __iter__(cls, *instanceargs):
        processed = []
        for alias in sorted(cls.plugins):
            value = cls.plugins[alias]
            if not value in processed:
                try:
                    instance = cls.create_instance(alias, *instanceargs)
                    yield(instance)
                except dexy.exceptions.InactiveFilter:
                    pass
                processed.append(value)

    def standardize_alias(cls, alias):
        obj = cls.plugins[alias]
        keys = []
        for k, v in cls.plugins.iteritems():
            if v == obj:
                keys.append(k)
        assert alias in keys
        return sorted(keys)[0]

    def check_docstring(cls):
        if not inspect.getdoc(cls):
            breadcrumbs = " -> ".join(t.__name__ for t in inspect.getmro(cls)[:-1][::-1])
            msg = "docstring required for dexy plugin '%s' (%s, defined in %s)"
            args = (cls.__name__, breadcrumbs, cls.__module__)
            raise dexy.exceptions.InternalDexyProblem(msg % args)

    def register_plugins(cls, plugin_info):
        for k, v in plugin_info.iteritems():
            cls.register_plugin(k.split("|"), v[0], v[1])

    def register_plugins_from_yaml(cls, yaml_file):
        with open(yaml_file, "rb") as f:
            plugin_info = yaml.safe_load(f.read())

        for alias, info_dict in plugin_info.iteritems():
            if ":" in alias:
                _, alias = alias.split(":")

            class_name = info_dict['class']
            del info_dict['class']
            cls.register_plugin(alias.split("|"), class_name, info_dict)

    def register_plugin(cls, alias_or_aliases, class_or_class_name, settings):
        if isinstance(alias_or_aliases, basestring):
            aliases = [alias_or_aliases]
        else:
            aliases = alias_or_aliases

        if not settings.has_key('help'):
            klass = cls.get_reference_to_class(class_or_class_name)
            settings['help'] = ("Helpstring for filter.", inspect.getdoc(klass))

        class_info = (class_or_class_name, settings)
        for alias in aliases:
            if cls.plugins.has_key(alias):
                raise Exception("Already have alias %s" % alias)
            cls.plugins[alias] = class_info

    def imro(cls):
        """
        Returns MRO in reverse order, skipping 'object/type' class.
        """
        return reversed(inspect.getmro(cls)[0:-2])

    def get_reference_to_class(cls, class_or_class_name):
        if isinstance(class_or_class_name, type):
            return class_or_class_name
        elif isinstance(class_or_class_name, basestring):
            if ":" in class_or_class_name:
                mod_name, class_name = class_or_class_name.split(":")

                # load the module
                if not mod_name in sys.modules:
                    __import__(mod_name)
                mod = sys.modules[mod_name]

                return mod.__dict__[class_name]
            else:
                from dexy.filters.pexp import PexpectReplFilter
                from dexy.filters.process import SubprocessCompileFilter
                from dexy.filters.process import SubprocessCompileInputFilter
                from dexy.filters.process import SubprocessExtToFormatFilter
                from dexy.filters.process import SubprocessFilter
                from dexy.filters.process import SubprocessFormatFlagFilter
                from dexy.filters.process import SubprocessInputFileFilter
                from dexy.filters.process import SubprocessInputFilter
                from dexy.filters.process import SubprocessStdoutFilter
                from dexy.filters.process import SubprocessStdoutTextFilter
                from dexy.filters.standard import PreserveDataClassFilter
                return locals()[class_or_class_name]
        else:
            raise Exception("Unexpected type %s" % type(class_or_class_name))

    def class_update_settings(cls, instance, new_settings, enforce_helpstring=True):
        for raw_key, value in new_settings.iteritems():
            key = raw_key.replace("_", "-")
            key_in_settings = instance._settings.has_key(key)
            value_is_list_len_2 = isinstance(value, list) and len(value) == 2
            if isinstance(value, tuple) or (not key_in_settings and value_is_list_len_2):
                instance._settings[key] = value
            else:
                if not instance._settings.has_key(key):
                    if enforce_helpstring:
                        raise Exception("You must specify param '%s' as a tuple of (helpstring, value)" % key)
                    else:
                        # TODO check and warn if key is similar to an existing key
                        instance._settings[key] = ('', value,)
                else:
                    orig = instance._settings[key]
                    instance._settings[key] = (orig[0], value,)

    def create_instance(cls, alias, *instanceargs, **instancekwargs):
        if not alias in cls.plugins:
            raise dexy.exceptions.NoPlugin("No alias %s available." % alias)
        class_or_class_name, settings = cls.plugins[alias]

        klass = cls.get_reference_to_class(class_or_class_name)


        instance = klass(*instanceargs, **instancekwargs)
        instance._settings = {}
        instance.alias = alias

        for parent_class in klass.imro():
            klass.class_update_settings(instance, parent_class._SETTINGS)
            if hasattr(parent_class, 'UNSET'):
                for unset in parent_class.UNSET:
                    print "Removing setting '%s' from %s" % (unset, parent_class.__name__)
                    del instance._settings[unset]

        # Update with any settings defined at time plugin was registered.
        klass.class_update_settings(instance, settings)

        # TODO update settings from environment, dexy config

        if not instance.is_active():
            raise dexy.exceptions.InactiveFilter(alias)

        return instance

#            basenames = [k.__name__ for k in cls.__bases__]
#            if hasattr(cls, 'ALIASES'):
#                for alias in cls.ALIASES:
#
#                    # Namespace templates by their plugin name (after dexy_)
#                    if 'Template' in basenames:
#                        if cls.__module__ == 'dexy.plugins.templates':
#                            prefix = 'dexy'
#                        else:
#                            prefix = cls.__module__.replace("dexy_", "")
#                        alias = "%s:%s" % (prefix, alias)
#
#                    if alias in cls.aliases:
#                        raise Exception("duplicate alias %s found in %s, already present in %s" % (alias, cls.__name__, cls.aliases[alias].__name__))
#                    cls.aliases[alias] = cls
#            elif hasattr(cls, 'NAMESPACE'):
#                cls.aliases[cls.NAMESPACE] = cls

class Command(Plugin):
    """
    Parent class for custom dexy commands.
    """
    __metaclass__ = PluginMeta
    _SETTINGS = {}
    ALIASES = []
    DEFAULT_COMMAND = None
    NAMESPACE = None

    def is_active(klass):
        return True
