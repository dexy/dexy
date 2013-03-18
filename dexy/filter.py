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

    aliases = ['dexy']
    TAGS = []
    NODOC_settings = [
            'help', 'nodoc'
            ]
    _settings = {
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

    def __init__(self, doc=None):
        self.doc = doc

    def data_class_alias(self, ext):
        return self.setting('output-data-type')

    def setup(self, key, storage_key, prev_filter, next_filter):
        self.key = key
        self.storage_key = storage_key
        self.prev_filter = prev_filter
        self.next_filter = next_filter

        if self.prev_filter:
            self.input_data = self.prev_filter.output
            self.prev_ext = self.prev_filter.ext
        else:
            self.input_data = self.doc.initial_data
            self.prev_ext = self.doc.initial_data.ext

        self.set_extension()
    
        self.output = dexy.data.Data.create_instance(
                self.data_class_alias(self.ext),
                self.key,
                self.ext,
                self.calculate_canonical_name(),
                self.storage_key,
                {},
                None,
                self.doc.wrapper
                )
        self.output.setup_storage()

    def set_extension(self):
        i_accept = self.setting('input-extensions')
        i_output = self.setting('output-extensions')

        if self.prev_filter:
            prev_ext = self.prev_filter.ext
        else:
            prev_ext = self.doc.ext

        # Check that we can handle input extension
        if set([prev_ext, ".*"]).isdisjoint(set(i_accept)):
            msg = "Filter '%s' in '%s' can't handle file extension %s, supported extensions are %s"
            params = (self.filter_alias, self.key, prev_ext, ", ".join(i_accept))
            raise dexy.exceptions.UserFeedback(msg % params)

        # Figure out output extension
        ext = self.setting('ext')
        if ext:
            # User has specified desired extension
            if not ext.startswith('.'):
                ext = '.%s' % ext

            # Make sure it's a valid one
            if (not ext in i_output) and (not ".*" in i_output):
                msg = "You have requested file extension %s in %s but filter %s can't generate that."
                raise dexy.exceptions.UserFeedback(msg % (ext, self.key, self.filter_alias))

            self.ext = ext

        elif ".*" in i_output:
            self.ext = prev_ext

        else:
            # User has not specified desired extension, and we don't output wildcards,
            # figure out extension based on next filter in sequence, if any.
            if self.next_filter:
                next_filter_accepts = self.next_filter.setting('input-extensions')

                if ".*" in next_filter_accepts:
                    self.ext = i_output[0]
                else:
                    if set(i_output).isdisjoint(set(next_filter_accepts)):
                        msg = "Filter %s can't go after filter %s, no file extensions in common."
                        raise dexy.exceptions.UserFeedback(msg % (self.next_filter_alias, self.filter_alias))

                    for e in i_output:
                        if e in next_filter_accepts:
                            self.ext = e

                    if not self.ext:
                        msg = "no file extension found but checked already for disjointed, should not be here"
                        raise dexy.exceptions.InternalDexyProblem(msg)
            else:
                self.ext = i_output[0]

    def templates(self):
        """
        List of dexy templates which refer to this filter.
        """
        import dexy.template
        return [t for t in dexy.template.Template if any(a for a in self.aliases if a in t.FILTERS_USED)]

    def filter_specific_settings(self):
        nodoc = self.NODOC_settings
        base = dexy.filter.Filter._settings
        return dict((k, v) for k, v in self._settings.iteritems() if not k in nodoc and not k in base)

    def key_with_class(self):
        return "%s:%s" % (self.__class__.__name__, self.key)

    def log_debug(self, message):
        self.doc.wrapper.log.debug("%s: %s" % (self.key_with_class(), message))

    def log_info(self, message):
        self.doc.wrapper.log.info("%s: %s" % (self.key_with_class(), message))

    def log_warn(self, message):
        self.doc.wrapper.log.warn("%s: %s" % (self.key_with_class(), message))

    def process(self):
        """
        Run the filter, converting input to output.
        """
        pass

    def calculate_canonical_name(self):
        name_without_ext = posixpath.splitext(self.key)[0]
        return "%s%s" % (name_without_ext, self.ext)

    def doc_arg(self, arg_name_hyphen, default=None):
        return self.doc.arg_value(arg_name_hyphen, default)

    def add_doc(self, doc_name, doc_contents=None, run=True, shortcut=None):
        doc_name = os_to_posix(doc_name)
        if not posixpath.sep in doc_name:
            doc_name = posixpath.join(self.input().parent_dir(), doc_name)

        additional_doc_filters = self.setting('additional-doc-filters')
        self.log_debug("additional-doc-filters are %s" % additional_doc_filters)

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
                self.doc.add_doc(doc)

            doc_key = "%s|%s" % (doc_name, filters)
            doc = dexy.doc.Doc(doc_key, contents=doc_contents, shortcut=shortcut)
            self.doc.add_doc(doc, run=run)

        else:
            doc_key = doc_name
            doc = dexy.doc.Doc(doc_key, contents=doc_contents, shortcut=shortcut)
            self.doc.add_doc(doc, run=run)

        return doc

    def workspace(self):
        return os.path.join(self.doc.wrapper.artifacts_dir, self.doc.wrapper.workspace, self.storage_key)

    def populate_workspace(self):
        os.makedirs(self.workspace())
        for inpt in self.doc.walk_inputs():
            print inpt.key_with_class()
            print inpt.filters[-1].output_data.name

    def write_to_wd(self, wd, doc, filename):
        try:
            doc.output.output_to_file(filename)
            self._wd_files_start.add(filename)
        except Exception as e:
            args = (e.__class__.__name__, wd, self.artifact.key, doc.key, filename)
            self.log_debug("%s error occurred whlie trying to populate working directory %s for %s with %s (%s)" % args)
            self.log_debug(str(e))

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
    aliases = ['dexy']

    def data_class_alias(self, file_ext):
        if hasattr(self, 'process_dict'):
            return 'sectioned'
        elif hasattr(self, 'process_text_to_dict'):
            return 'sectioned'
        else:
            return self.setting('output-data-type')

    def process(self):
        if hasattr(self, "process_text_to_dict"):
            output = self.process_text_to_dict(unicode(self.input_data))
            self.output.set_data(output)

        elif hasattr(self, "process_dict"):
            output = self.process_dict(self.input_data.as_sectioned())
            self.output.set_data(output)

        elif hasattr(self, "process_text"):
            output = self.process_text(unicode(self.input_data))
            self.output.set_data(output)

        else:
            self.output.copy_from_file(self.input_data.storage.data_file())

class AliasFilter(DexyFilter):
    """
    Filter to be used when an Alias is specified. Should not change input.
    """
    aliases = ['-']
    _settings = {
            'preserve-prior-data-class' : True
            }

    def calculate_canonical_name(self):
        return self.artifact.prior.filter_instance.calculate_canonical_name()
