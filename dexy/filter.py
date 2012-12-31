from dexy.utils import os_to_posix
import dexy.doc
import dexy.exceptions
import dexy.plugin
import dexy.utils
import os
import posixpath

class FilterException(Exception):
    pass

class Filter:
    __metaclass__ = dexy.plugin.PluginMeta

    ALIASES = ['dexy']
    FRAGMENT = True
    INPUT_EXTENSIONS = [".*"]
    NODOC = False
    OUTPUT_DATA_TYPE = 'generic'
    OUTPUT_EXTENSIONS = [".*"]
    PRESERVE_PRIOR_DATA_CLASS = False
    REQUIRE_OUTPUT = True
    TAGS = []

    @classmethod
    def templates(klass):
        """
        List of dexy templates which refer to this filter.
        """
        import dexy.template
        return [p for p in dexy.template.Template.plugins if any(a for a in klass.ALIASES if a in p.FILTERS_USED)]

    @classmethod
    def is_active(klass):
        return True

    @classmethod
    def inactive_because_missing(klass):
        if hasattr(klass, 'executables'):
            return klass.executables()
        elif hasattr(klass, 'IMPORTS'):
            return klass.IMPORTS

    def args(self):
        return self.artifact.filter_args()

    def arg_value(self, arg_name_hyphen, default=None):
        return dexy.utils.value_for_hyphenated_or_underscored_arg(self.args(), arg_name_hyphen, default)

    @classmethod
    def data_class_alias(klass, file_ext):
        return klass.OUTPUT_DATA_TYPE

    def do_add_new_files(self):
        return self.ADD_NEW_FILES or self.arg_value("add-new-files", False)

    def process(self):
        pass

    def calculate_canonical_name(self):
        name_without_ext = posixpath.splitext(self.artifact.key)[0]
        return "%s%s" % (name_without_ext, self.artifact.ext)

    def doc_arg(self, arg_name_hyphen, default=None):
        return self.artifact.doc.arg_value(arg_name_hyphen, default)

    def add_doc(self, doc_name, doc_contents=None):
        doc_name = os_to_posix(doc_name)
        if not posixpath.sep in doc_name:
            doc_name = posixpath.join(self.input().parent_dir(), doc_name)

        additional_doc_filters = self.arg_value('additional-doc-filters', {}) 
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
            if self.arg_value('keep-originals', True):
                doc_key = doc_name
                doc = dexy.doc.Doc(doc_key, contents=doc_contents)
                self.artifact.add_doc(doc)

            doc_key = "%s|%s" % (doc_name, filters)
            doc = dexy.doc.Doc(doc_key, contents=doc_contents)
            self.artifact.add_doc(doc)

        else:
            doc_key = doc_name
            doc = dexy.doc.Doc(doc_key, contents=doc_contents)
            self.artifact.add_doc(doc)

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
        wd = self.artifact.working_dir()
        wd_exists = os.path.exists(wd)
        self.log.debug("setting up wd for %s. exists already: %s" % (self.artifact.key, wd))
        written_already = set()
        if not wd_exists:
            for doc, filename in self.artifact.setup_wd(self.input_filename()):
                wa = filename in written_already
                self.write_to_wd(wd, doc, filename, wa)
                written_already.add(filename)

        return wd

    def write_to_wd(self, wd, doc, filename, wa=False):
        try:
            doc.output().output_to_file(filename)
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

class DexyFilter(Filter):
    """
    Filter which implements some default behaviors.
    """
    ALIASES = ['dexy']

    @classmethod
    def data_class_alias(klass, file_ext):
        if hasattr(klass, 'process_dict'):
            return 'sectioned'
        elif hasattr(klass, 'process_text_to_dict'):
            return 'sectioned'
        else:
            return klass.OUTPUT_DATA_TYPE

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
    PRESERVE_PRIOR_DATA_CLASS = True
    ALIASES = []

    def calculate_canonical_name(self):
        return self.artifact.prior.filter_instance.calculate_canonical_name()
