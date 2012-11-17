import dexy.plugin
import os
import sys
import shutil

class Template(object):
    ALIASES = []
    __metaclass__ = dexy.plugin.PluginMeta

    @classmethod
    def is_active(klass):
        return True

    def template_source_dir(self):
        template_install_dir = os.path.dirname(sys.modules[self.__class__.__module__].__file__)

        if hasattr(self, 'CONTENTS'):
            contents_dirname = self.CONTENTS
        else:
            # default is to have contents in directory with same name as alias followed by "-template"
            contents_dirname = "%s-template" % self.ALIASES[0]

        return os.path.join(template_install_dir, contents_dirname)

    def run(self, directory, **kwargs):
        if os.path.exists(directory):
            raise dexy.exceptions.UserFeedback("Directory '%s' already exists, aborting." % directory)
        source = self.template_source_dir()
        shutil.copytree(source, directory)

