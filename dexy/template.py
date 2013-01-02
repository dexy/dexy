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

        dexy_rst = os.path.join(directory, 'dexy.rst')
        if os.path.exists(dexy_rst):
            if not kwargs.get('meta'):
                os.remove(dexy_rst)

    @classmethod
    def dexy(klass, meta=True, additional_doc_keys=None):
        """
        Run dexy on this template's files in a temporary directory.

        Yields the batch object for the dexy run, so we can call methods on it
        while still in the tempdir.
        """
        DOC_KEYS = [
                "dexy.yaml|idio|t",
                "dexy.rst|idio|t",
                "dexy.rst|jinja|rst2html",
                "dexy.rst|jinja|rst2man"
                ]

        with dexy.tests.utils.tempdir():
            # Copy files to directory 'ex'
            klass.run("ex", meta=meta)

            # Run dexy in directory 'ex'
            os.chdir("ex")
            wrapper = dexy.wrapper.Wrapper()
            wrapper.setup(True)
            wrapper.batch = dexy.batch.Batch(wrapper)

            ast = wrapper.load_doc_config()

            if additional_doc_keys:
                for doc_key in additional_doc_keys:
                    ast.add_task_info(doc_key)

            if meta and os.path.exists('dexy.rst'):
                for doc_key in DOC_KEYS:
                    ast.add_task_info(doc_key)
                    for task in ast.lookup_table.keys():
                        if 'jinja' in doc_key and not 'jinja' in task:
                            ast.add_dependency(doc_key, task)

            wrapper.batch.load_ast(ast)

            try:
                wrapper.batch.run()
                wrapper.save_db()
            except:
                raise Exception("pushd %s" % os.path.abspath("."))

            yield(wrapper.batch)

    @classmethod
    def validate(klass):
        """
        Runs dexy and validates filter list.
        """
        for batch in klass.dexy(False):
            filters_used = batch.filters_used()

        for f in klass.FILTERS_USED:
            assert f in filters_used, "filter %s not used by %s" % (f, klass.__name__)

        for f in filters_used:
            if not f in klass.FILTERS_USED:
                print "filter %s used by %s but not listed in klass.FILTERS_USED, adjust list to:" % (f, klass.__name__)
                print "   FILTERS_USED = [%s]" % ", ".join("'%s'" % f for f in filters_used)

        return True
