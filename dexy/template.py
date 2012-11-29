import dexy.plugin
import os
import sys
import shutil
import dexy.tests.utils
import dexy.wrapper

class Template(object):
    ALIASES = []
    FILTERS_USED = []
    __metaclass__ = dexy.plugin.PluginMeta

    @classmethod
    def is_active(klass):
        return True

    @classmethod
    def template_source_dir(klass):
        template_install_dir = os.path.dirname(sys.modules[klass.__module__].__file__)

        if hasattr(klass, 'CONTENTS'):
            contents_dirname = klass.CONTENTS
        else:
            # default is to have contents in directory with same name as alias followed by "-template"
            contents_dirname = "%s-template" % klass.ALIASES[0]

        return os.path.join(template_install_dir, contents_dirname)

    @classmethod
    def run(klass, directory, **kwargs):
        if os.path.exists(directory):
            raise dexy.exceptions.UserFeedback("Directory '%s' already exists, aborting." % directory)
        source = klass.template_source_dir()
        shutil.copytree(source, directory)

    @classmethod
    def dexy(klass):
        """
        Run dexy on this template's files in a temporary directory.

        Returns the batch object for the dexy run.
        """
        with dexy.tests.utils.tempdir():
            klass.run("ex")
            os.chdir("ex")
            wrapper = dexy.wrapper.Wrapper()
            wrapper.setup_dexy_dirs()
            wrapper.setup_log()
            wrapper.setup_db()
            wrapper.run()
            return wrapper.batch

    @classmethod
    def validate(klass):
        """
        Runs dexy and validates filter list.
        """
        batch = klass.dexy()
        filters_used = batch.filters_used()

        for f in klass.FILTERS_USED:
            assert f in filters_used, "filter %s not used by %s" % (f, klass.__name__)

        for f in filters_used:
            if (not f in klass.FILTERS_USED) and (not f.startswith("-")):
                print "filter %s used by %s but not listed in klass.FILTERS_USED" % (f, klass.__name__)
