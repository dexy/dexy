from dexy.utils import os_to_posix
import dexy.doc
import dexy.exceptions
import dexy.plugin
import dexy.utils
import os
import posixpath

class FilterException(Exception):
    pass

class Filter(dexy.plugin.Plugin):
    """
    Base class for types of filter.
    """
    __metaclass__ = dexy.plugin.PluginMeta

    ALIASES = ['dexy']
    TAGS = []
    NODOC_SETTINGS = [
            'help', 'nodoc'
            ]
    _SETTINGS = {
            'add-new-files' : ('', False),
            'additional-doc-filters' : ('', {}),
            'ext' : ('Extension to output.', None),
            'help' : ('Help string for filter, if not already specified as a class docstring.', None),
            'input-extensions' : ("List of extensions which this filter can accept as input.", [".*"]),
            'keep-originals' : ('', False),
            'nodoc' : ("Whether filter should be excluded from documentation.", False),
            'output' : ("Whether to output results of this filter by default.", False),
            'output-data-type' : ("Alias of data type to use to store filter output.", "generic"),
            'output-extensions' : ("List of extensions which this filter can produce as output.", [".*"]),
            'preserve-prior-data-class' : ('', False),
            'require-output' : ("Should dexy raise an exception if no output is produced by this filter?", True),
            'variables' : ('', {}),
            'vars' : ('', {}),
            }

    def templates(self):
        """
        List of dexy templates which refer to this filter.
        """
        import dexy.template
        return [t for t in dexy.template.Template if any(a for a in self.ALIASES if a in t.FILTERS_USED)]

    def filter_specific_settings(self):
        nodoc = self.NODOC_SETTINGS
        base = dexy.filter.Filter._SETTINGS
        return dict((k, v) for k, v in self._settings.iteritems() if not k in nodoc and not k in base)

    def info(self):
        info = {}
        info['settings'] = {}
        for k, tup in self.filter_specific_settings().iteritems():
            info['settings'][k] = {}
            info['settings'][k]['help'] = tup[0]
            info['settings'][k]['default'] = tup[1]
            info['settings'][k]['is-env-var'] = hasattr(tup[1], 'startswith') and tup[1].startswith("$")
        return info

    def is_active(self):
        return True

    def inactive_because(self):
        raise Exception("not implemented")

    def update_all_args(self, new_args):
        self.artifact.doc.args.update(new_args)
        for a in self.artifact.doc.children[1:]:
            a.update_args(new_args)

    def data_class_alias(self, file_ext):
        return self.setting('output-data-type')

    def do_add_new_files(self):
        return self.setting('add-new-files')

    def process(self):
        pass

    def calculate_canonical_name(self):
        name_without_ext = posixpath.splitext(self.artifact.key)[0]
        return "%s%s" % (name_without_ext, self.artifact.ext)

    def doc_arg(self, arg_name_hyphen, default=None):
        return self.artifact.doc.arg_value(arg_name_hyphen, default)

    def add_doc(self, doc_name, doc_contents=None, run=True, shortcut=None):
        doc_name = os_to_posix(doc_name)
        if not posixpath.sep in doc_name:
            doc_name = posixpath.join(self.input().parent_dir(), doc_name)

        additional_doc_filters = self.setting('additional-doc-filters')
        self.log.debug("additional-doc-filters are %s" % additional_doc_filters)

        doc_ext = os.path.splitext(doc_name)[1]

        if isinstance(additional_doc_filters, dict):
            filters = additional_doc_filters.get(doc_ext, '')
        elif isinstance(additional_doc_filters, str) or isinstance(additional_doc_filters, unicode):
            filters = additional_doc_filters
        else:
            # TODO allow passing a list of tuples so input can be
            # used in more than 1 way
            raise Exception("not implemented")

        if len(filters) > 0:
            if self.setting('keep-originals'):
                doc_key = doc_name
                doc = dexy.doc.Doc(doc_key, contents=doc_contents)
                self.artifact.add_doc(doc)

            doc_key = "%s|%s" % (doc_name, filters)
            doc = dexy.doc.Doc(doc_key, contents=doc_contents, shortcut=shortcut)
            self.artifact.add_doc(doc, run=run)

        else:
            doc_key = doc_name
            doc = dexy.doc.Doc(doc_key, contents=doc_contents, shortcut=shortcut)
            self.artifact.add_doc(doc, run=run)

        return doc

    def input(self):
        return self.artifact.input_data

    def inputs(self):
        return self.artifact.doc.node.walk_inputs()

    def input_filename(self):
        return self.artifact.input_filename()

    def output_filename(self):
        return self.artifact.output_filename()

    def output(self):
        return self.artifact.output_data

    def output_filepath(self):
        return self.output().storage.data_file()

    def processed(self):
        return self.artifact.doc.node.walk_input_docs()

    def final_ext(self):
        return self.artifact.doc.final_artifact.ext

    def setup_wd(self, populate=True):
        wd = self.artifact.full_wd()
        if not self.artifact._wd_setup:
            self._wd_files_start = set()
            input_filename = self.input_filename()
            for doc, filename in self.artifact.setup_wd(input_filename):
                self.write_to_wd(wd, doc, filename)
        return wd

    def write_to_wd(self, wd, doc, filename):
        try:
            doc.output().output_to_file(filename)
            self._wd_files_start.add(filename)
        except Exception as e:
            args = (e.__class__.__name__, wd, self.artifact.key, doc.key, filename)
            self.log.debug("%s error occurred whlie trying to populate working directory %s for %s with %s (%s)" % args)
            self.log.debug(str(e))

    def resolve_conflict(self, doc, conflict_docs):
        """
        Return true if the doc wins the conflict and should be written to the canonical name, false if not.
        """
        conflict_docs = [d for d in conflict_docs if not (('pyg' in d.key) or ('idio' in d.key))]
        conflict_docs.sort()
        if len(conflict_docs) == 0:
            return True
        else:
            return doc in conflict_docs and conflict_docs.index(doc) == 0

    def is_part_of_script_bundle(self):
        if hasattr(self.artifact.doc.node, 'parent'):
            return hasattr(self.artifact.doc.node.parent, 'script_storage')

    def script_storage(self):
        if not self.is_part_of_script_bundle():
            raise dexy.exceptions.UserFeedback("%s must be part of script bundle to access script storage" % self.key)
        return self.artifact.doc.node.parent.script_storage

class DexyFilter(Filter):
    """
    Filter which implements some default behaviors.
    """
    ALIASES = ['dexy']

    def data_class_alias(klass, file_ext):
        if hasattr(klass, 'process_dict'):
            return 'sectioned'
        elif hasattr(klass, 'process_text_to_dict'):
            return 'sectioned'
        else:
            return klass.setting('output-data-type')

    def process(self):
        if hasattr(self, "process_text_to_dict"):
            output = self.process_text_to_dict(unicode(self.input()))
            self.output().set_data(output)

        elif hasattr(self, "process_dict"):
            output = self.process_dict(self.input().as_sectioned())
            self.output().set_data(output)

        elif hasattr(self, "process_text"):
            output = self.process_text(unicode(self.input()))
            self.output().set_data(output)

        else:
            self.output().copy_from_file(self.input().storage.data_file())

class AliasFilter(DexyFilter):
    """
    Filter to be used when an Alias is specified. Should not change input.
    """
    ALIASES = ['-']
    _SETTINGS = {
            'preserve-prior-data-class' : True
            }

    def calculate_canonical_name(self):
        return self.artifact.prior.filter_instance.calculate_canonical_name()
