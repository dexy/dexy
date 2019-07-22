from dexy.utils import s
import dexy.plugin
import dexy.utils
import dexy.wrapper
import os
import shutil
import sys

class Template(dexy.plugin.Plugin, metaclass=dexy.plugin.PluginMeta):
    """
    Parent class for templates.
    """
    _settings = {
            'contents-dir' : ("Directory containing contents of template.", None),
            'nodoc' : ("Whether to not document this template.", False),
            'copy-output-dir' : ("", False)
            }
    aliases = []
    filters_used = []

    def __init__(self):
        self.initialize_settings()

    def template_source_dir(self):
        if self.safe_setting('install-dir'):
            template_install_dir = self.setting('install-dir')
        else:
            template_install_dir = os.path.dirname(sys.modules[self.__module__].__file__)

        if self.setting('contents-dir'):
            contents_dirname = self.setting('contents-dir')
        else:
            if self.__class__.aliases:
                canonical_alias = self.__class__.aliases[0]
            else:
                canonical_alias = self.alias

            # default is to have contents in directory with same name as alias followed by "-template"
            contents_dirname = "%s-template" % canonical_alias

        return os.path.join(template_install_dir, contents_dirname)

    def generate(self, directory, **kwargs):
        """
        Generates the template, making a copy of the template's files in
        the specified directory. Does not run dexy.
        """
        if dexy.utils.file_exists(directory):
            msg = "directory '%s' already exists, aborting" % directory
            raise dexy.exceptions.UserFeedback(msg)

        # copy template files
        source = self.template_source_dir()
        shutil.copytree(source, directory)

        # remove template documentation unless 'meta' is specified
        if not kwargs.get('meta'):
            dexy_rst = os.path.join(directory, 'dexy.rst')
            if dexy.utils.file_exists(dexy_rst):
                os.remove(dexy_rst)

    def dexy(self, meta=True, additional_doc_keys=None):
        """
        Run dexy on this template's files in a temporary directory.

        Yields the batch object for the dexy run, so we can call methods on it
        while still in the tempdir.
        """
        meta_doc_keys = [
                ".*",
                "dexy.yaml|idio|t",
                "dexy.rst|idio|t",
                "dexy.rst|jinja|rst2html",
                "dexy.rst|jinja|rst2man"
                ]

        with dexy.utils.tempdir():
            # Copy template files to directory 'ex'
            self.generate("ex", meta=meta)

            # Run dexy in directory 'ex'
            os.chdir("ex")
            wrapper = dexy.wrapper.Wrapper()
            wrapper.create_dexy_dirs()
            wrapper = dexy.wrapper.Wrapper(log_level='DEBUG')
            wrapper.to_valid()
            wrapper.nodes = {}
            wrapper.roots = []
            wrapper.batch = dexy.batch.Batch(wrapper)
            wrapper.filemap = wrapper.map_files()

            ast = wrapper.parse_configs()
            if additional_doc_keys:
                for doc_key in additional_doc_keys:
                    ast.add_node(doc_key)

            if meta and dexy.utils.file_exists('dexy.rst'):
                for doc_key in meta_doc_keys:
                    ast.add_node(doc_key)
                    if 'jinja' in doc_key:
                        for task in list(ast.lookup_table.keys()):
                            if not task in meta_doc_keys:
                                ast.add_dependency(doc_key, task)

            ast.walk()

            wrapper.transition('walked')
            wrapper.to_checked()

            try:
                wrapper.run()
            except (Exception, SystemExit,) as e:
                error = str(e)
                template_dir = os.path.abspath(".")
                msg = "%s\npushd %s" % (error, template_dir)
                raise dexy.exceptions.TemplateException(msg)

            if wrapper.state == 'error':
                template_dir = os.path.abspath(".")
                msg = "pushd %s" % (template_dir)
                raise dexy.exceptions.TemplateException(msg)

            yield(wrapper)

    def validate(self):
        """
        Runs dexy and validates filter list.
        """
        for wrapper in self.dexy(False):
            filters_used = wrapper.batch.filters_used

            for f in self.__class__.filters_used:
                msg = "filter %s not used by %s" % (f, self.__class__.__name__)
                assert f in filters_used, msg
    
            for f in filters_used:
                if not f.startswith('-') and not f in self.__class__.filters_used:
                    msg = s("""filter %(filter)s used by %(template)s
                            but not listed in klass.filters_used,
                            adjust list to: filters_used = [%(list)s]""")
                    msgargs = {
                            'filter' : f,
                            'template' : self.__class__.__name__,
                            'list'  : ", ".join("'%s'" % f for f in filters_used)
                            }
                    print((msg % msgargs))

            return wrapper.state == 'ran'
