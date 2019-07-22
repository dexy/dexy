import cashew
from cashew import Plugin

class PluginMeta(cashew.PluginMeta):
    """
    PluginMeta customized for dexy.
    """
    _store_other_class_settings = {} # allow plugins to define settings for other classes
    official_dexy_plugins = ("dexy_templates", "dexy_viewer", "dexy_filter_examples")

    def load_class_from_locals(cls, class_name):
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
        return locals()[class_name]

    def apply_prefix(cls, modname, alias):
        if modname.startswith("dexy_") and not modname in PluginMeta.official_dexy_plugins:
            prefix = modname.split(".")[0].replace("dexy_", "")
            return "%s:%s" % (prefix, alias)
        else:
            return alias 

    def adjust_alias(cls, alias):
        """
        All of '-' or '-foo' or '---' should map to '-' which is a registered alias.

        This way we can always create unique names by including arbitrary
        distinguishing content after a '-'.
        """
        if alias.startswith('-'):
            alias = '-'
        return alias

class Command(Plugin, metaclass=PluginMeta):
    """
    Parent class for custom dexy commands.
    """
    _settings = {}
    aliases = []
    default_cmd = None
    namespace = None

class TemplatePlugin(Plugin, metaclass=PluginMeta):
    """
    Parent class for template plugins.
    """
    aliases = []
    _settings = {
            'no-jinja-filter' : ("Listed entries should not be made into jinja filters.")
            }

    def is_active(self):
        return True

    def __init__(self, filter_instance=None):
        if filter_instance:
            self.filter_instance = filter_instance

    def run(self):
        return {}
