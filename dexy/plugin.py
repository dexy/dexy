import dexy.exceptions
import inspect
import os
import sys
import yaml
import inflection

class Plugin(object):
    """
    Base class for plugins. Define *instance* methods shared by plugins here.
    """
    def is_active(self):
        return True

    def name(self):
        return inflection.titleize(self.setting('aliases')[0])

    def help(self):
        return self.setting('help')

    def initialize_settings(self, **raw_kwargs):
        self._instance_settings = {}
        for parent_class in self.__class__.imro():
            if parent_class._settings:
                self.__class__.class_update_settings(self, parent_class._settings)
            if hasattr(parent_class, 'UNSET'):
                for unset in parent_class.UNSET:
                    del self._instance_settings[unset]

        if hasattr(self.__class__, 'aliases') and self.__class__.aliases:
            alias = self.__class__.aliases[0]
            settings_from_other_classes = PluginMeta._store_other_class_settings.get(alias)
            if settings_from_other_classes:
                self.__class__.class_update_settings(self, settings_from_other_classes)

        # Apply raw_kwargs settings
        hyphen_settings = dict((k, v) for k, v in raw_kwargs.items() if k in self._instance_settings)
        underscore_settings = dict((k.replace("_", "-"), v) for k, v in raw_kwargs.items() if k.replace("_", "-") in self._instance_settings)
        self.__class__.class_update_settings(self, hyphen_settings)
        self.__class__.class_update_settings(self, underscore_settings)

    def setting(self, name_hyphen):
        """
        Retrieves the setting value whose name is indicated by name_hyphen.

        Values starting with $ are assumed to reference environment variables,
        and the value stored in environment variables is retrieved. (It's an
        error if there's no corresponding environment variable set.)
        """
        if name_hyphen in self._instance_settings:
            value = self._instance_settings[name_hyphen][1]
        else:
            name_underscore = name_hyphen.replace("-", "_")
            if name_underscore in self._instance_settings:
                value = self._instance_settings[name_underscore][1]
            else:
                if name_underscore == name_hyphen:
                    msg = "no setting named %s" % name_hyphen
                else:
                    msg = "no setting named '%s' or '%s'"
                    msg = msg % (name_hyphen, name_underscore)
                raise dexy.exceptions.UserFeedback(msg)

        if hasattr(value, 'startswith') and value.startswith("$"):
            env_var = value.lstrip("$")
            if os.environ.has_key(env_var):
                return os.getenv(env_var)
            else:
                msg = "'%s' is not defined in your environment" % env_var
                raise dexy.exceptions.UserFeedback(msg)
        elif hasattr(value, 'startswith') and value.startswith("\$"):
            return value.replace("\$", "$")
        else:
            return value

    def setting_values(self, skip=None):
        """
        Returns dict of all setting values (removes the helpstrings)
        """
        if not skip:
            skip = []
        return dict((k, v[1]) for k, v in self._instance_settings.iteritems() if not k in skip)

    def update_settings(self, new_settings):
        self.__class__.class_update_settings(self, new_settings, False)

class PluginMeta(type):
    """
    Base meta class for anything plugin-able.
    """
    _store_other_class_settings = {} # allow plugins to define settings for other classes
    official_dexy_plugins = ("dexy_templates", "dexy_viewer", "dexy_filter_examples")

    def __init__(cls, name, bases, attrs):
        assert issubclass(cls, Plugin), "%s should inherit from class Plugin" % name
        if '__metaclass__' in attrs:
            cls.plugins = {}
        if hasattr(cls, 'aliases'):
            cls.register_plugin(cls.aliases, cls, {})

    def __iter__(cls, *instanceargs):
        processed_aliases = set()
        for alias in sorted(cls.plugins):
            if alias in processed_aliases:
                continue

            try:
                instance = cls.create_instance(alias, *instanceargs)
                yield(instance)
                for alias in instance.aliases:
                    processed_aliases.add(alias)

            except dexy.exceptions.InactiveFilter:
                pass

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

        klass = cls.get_reference_to_class(class_or_class_name)

        if not settings.has_key('help'):
            settings['help'] = ("Helpstring for filter.", inspect.getdoc(klass))

        settings['aliases'] = ('aliases', aliases)

        class_info = (class_or_class_name, settings)
        for alias in aliases:
            if isinstance(class_or_class_name, type):
                modname = class_or_class_name.__module__
                if modname.startswith("dexy_") and not modname in PluginMeta.official_dexy_plugins:
                    prefix = modname.split(".")[0].replace("dexy_", "")
                    alias = "%s:%s" % (prefix, alias)
            if cls.plugins.has_key(alias):
                    msg = "Trying to define alias '%s' for %s, already an alias for %s"
                    msg_args = (alias, class_or_class_name, cls.plugins[alias][0],)
                    print msg%msg_args
            else:
                cls.plugins[alias] = class_info

        if hasattr(klass, '_other_class_settings') and klass._other_class_settings:
            PluginMeta._store_other_class_settings.update(klass._other_class_settings)

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
                from dexy.template import Template
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
            key_in_settings = instance._instance_settings.has_key(key)
            value_is_list_len_2 = isinstance(value, list) and len(value) == 2
            if isinstance(value, tuple) or (not key_in_settings and value_is_list_len_2):
                instance._instance_settings[key] = value
            else:
                if not instance._instance_settings.has_key(key):
                    if enforce_helpstring:
                        raise Exception("You must specify param '%s' as a tuple of (helpstring, value)" % key)
                    else:
                        # TODO check and warn if key is similar to an existing key
                        instance._instance_settings[key] = ('', value,)
                else:
                    orig = instance._instance_settings[key]
                    instance._instance_settings[key] = (orig[0], value,)

    def create_instance(cls, alias, *instanceargs, **instancekwargs):
        if alias.startswith('-'):
            alias = '-'
        elif not alias in cls.plugins:
            msg = "no alias '%s' available for '%s'"
            msgargs = (alias, cls.__name__)
            raise dexy.exceptions.NoPlugin(msg % msgargs)

        class_or_class_name, settings = cls.plugins[alias]
        klass = cls.get_reference_to_class(class_or_class_name)

        instance = klass(*instanceargs, **instancekwargs)
        instance.alias = alias

        if not hasattr(instance, '_instance_settings'):
            instance.initialize_settings()
        instance.update_settings(settings)

        if not instance.is_active():
            raise dexy.exceptions.InactiveFilter(alias)

        return instance

class Command(Plugin):
    """
    Parent class for custom dexy commands.
    """
    __metaclass__ = PluginMeta
    _settings = {}
    aliases = []
    DEFAULT_COMMAND = None
    NAMESPACE = None
