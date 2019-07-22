from dexy.utils import copy_or_link
from dexy.utils import os_to_posix
from operator import attrgetter
import dexy.doc
import dexy.exceptions
import dexy.plugin
import dexy.utils
import os
import posixpath

class FilterException(Exception):
    pass

class Filter(dexy.plugin.Plugin, metaclass=dexy.plugin.PluginMeta):
    """
    Base class for types of filter.
    """

    TAGS = []
    _class_settings = {'max-docstring-length' : 75}
    nodoc_settings = [
            'help', 'nodoc'
            ]
    _settings = {
            'added-in-version' : (
                "Dexy version when this filter was first available.",
                ''),
            'add-new-files' : (
                "Boolean or list of extensions/patterns to match.",
                False),
            'exclude-add-new-files' : (
                "List of patterns to skip even if they match add-new-files.",
                []),
            'exclude-new-files-from-dir' : (
                "List of directories to skip when adding new files.",
                []),
            'additional-doc-filters' : (
                "Filters to apply to additional documents created as side effects.",
                {}),
            'additional-doc-settings' : (
                "Settings to apply to additional documents created as side effects.",
                {}),
            'examples' : (
                "Templates which should be used as examples for this filter.",
                []),
            'ext' : (
                'File extension to output.',
                None),
            'extension-map' : (
                "Dictionary mapping input extensions to default output extensions.",
                None),
            'help' : (
                'Help string for filter, if not already specified as a class docstring.',
                None),
            'input-extensions' : (
                "List of extensions which this filter can accept as input.",
                [".*"]),
            'keep-originals' : (
                """Whether, if additional-doc-filters are specified, the
                original unmodified docs should also be added.""",
                False),
            'mkdir' : (
                "A directory which should be created in working dir.",
                None),
            'mkdirs' : (
                "A list of directories which should be created in working dir.",
                []),
            'nodoc' : (
                "Whether filter should be excluded from documentation.",
                False),
            'output' : (
                """Whether to output results of this filter by default by
                reporters such as 'output' or 'website'.""",
                False),
            'data-type' : (
                "Alias of custom data class to use to store filter output.",
                "generic"),
            'output-extensions' : (
                "List of extensions which this filter can produce as output.",
                [".*"]),
            'preserve-prior-data-class' : (
                "Whether output data class should be set to match the input data class.",
                False),
            'require-output' : (
                "Should dexy raise an exception if no output is produced by this filter?",
                True),
            'tags' : (
                "Tags which describe the filter.",
                []),
            'variables' : (
                'A dictionary of variable names and values to make available to this filter.',
                {}),
            'vars' : (
                'A dictionary of variable names and values to make available to this filter.',
                {}),
            'workspace-exclude-filters' : (
                "Filters whose output should be excluded from workspace.",
                ['pyg']),
            'override-workspace-exclude-filters' : (
                """If True, document will be populated to other workspaces
                ignoring workspace-exclude-filters.""", False),
            'workspace-includes' : (
                """If set to a list of filenames or extensions, only these will
                be populated to working dir.""",
                None)
            }

    def __init__(self, doc=None):
        self.doc = doc

    def filter_commands(self):
        """
        Return dictionary of filter command canonical names and method objects.
        """
        fcmds = {}
        for m in dir(self):
            if m.startswith("docmd_"):
                key = m.replace("docmd_", "")
                fcmds[key] = getattr(self, m)
        return fcmds

    def final_ext(self):
        return self.doc.output_data().ext

    def data_class_alias(self, ext):
        if self.setting('preserve-prior-data-class'):
            return self.input_data.alias
        else:
            return self.setting('data-type')

    def add_runtime_args(self, new_args):
        self.doc.add_runtime_args(new_args)

    def update_all_args(self, new_args):
        self.doc.add_runtime_args(new_args)

    def setup(self, key, storage_key, prev_filter, next_filter, custom_settings):
        self.key = key
        self.storage_key = storage_key
        self.prev_filter = prev_filter
        self.next_filter = next_filter

        self.update_settings(custom_settings)

        if self.prev_filter:
            self.input_data = self.prev_filter.output_data
            self.prev_ext = self.prev_filter.ext
        else:
            self.input_data = self.doc.initial_data
            self.prev_ext = self.doc.initial_data.ext

        self.set_extension()

        settings = self.input_data.setting_values()

        del settings['storage-type']
        del settings['aliases']
        
        settings.update({
                'canonical-name' : self.calculate_canonical_name(),
                'canonical-output' : self.is_canonical_output()
                })

        self.output_data = dexy.data.Data.create_instance(
                self.data_class_alias(self.ext),
                self.key,
                self.ext,
                self.storage_key,
                settings,
                self.doc.wrapper
                )

    def is_canonical_output(self):
        if self.input_data.setting('canonical-output') == True:
            return True
        elif (self.input_data.setting('canonical-output') == False):
            return False
        elif self.setting('output'):
            return True
        else:
            return None

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
            params = (self.alias, self.key, prev_ext, ", ".join(i_accept))
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
                raise dexy.exceptions.UserFeedback(msg % (ext, self.key, self.alias))

            self.ext = ext

        elif ".*" in i_output:
            self.ext = prev_ext

        else:
            # User has not specified desired extension, and we don't output wildcards,
            # figure out extension based on next filter in sequence, if any.
            ext_from_map = None
            if self.setting('extension-map'):
                ext_from_map = self.setting('extension-map')[prev_ext]

            next_filter_accepts = [".*"]
            if self.next_filter:
                next_filter_accepts = self.next_filter.setting('input-extensions')

            if ".*" in next_filter_accepts:
                if ext_from_map:
                    self.ext = ext_from_map
                else:
                    self.ext = i_output[0]

            elif ext_from_map:
                if not ext_from_map in next_filter_accepts:
                    msg = "Filter %s wants to output %s but %s doesn't accept this format."
                    msgargs = (self.alias, ext_from_map, self.next_filter.alias)
                    raise dexy.exceptions.UserFeedback(msg % msgargs)

                self.ext = ext_from_map

            else:
                if set(i_output).isdisjoint(set(next_filter_accepts)):
                    msg = "Filter %s can't go after filter %s, no file extensions in common."
                    raise dexy.exceptions.UserFeedback(msg % (self.next_filter.alias, self.alias))

                for e in i_output:
                    if e in next_filter_accepts:
                        self.ext = e

                if not self.ext:
                    msg = "no file extension found but checked already for disjointed, should not be here"
                    raise dexy.exceptions.InternalDexyProblem(msg)

    def templates(self):
        """
        List of dexy templates which refer to this filter.
        """
        import dexy.template
        templates = [dexy.template.Template.create_instance(a) for a in self.setting('examples')]
        return templates

    def key_with_class(self):
        return "%s:%s" % (self.__class__.__name__, self.key)

    def log_debug(self, message):
        self.doc.log_debug(message)

    def log_info(self, message):
        self.doc.log_info(message)

    def log_warn(self, message):
        self.doc.log_warn(message)

    def process(self):
        """
        Run the filter, converting input to output.
        """
        pass

    def calculate_canonical_name(self):
        name_without_ext = posixpath.splitext(self.doc.name)[0]
        return "%s%s" % (name_without_ext, self.ext)

    def output_filepath(self):
        return self.output_data.storage.data_file()

    def doc_arg(self, arg_name_hyphen, default=None):
        return self.doc.arg_value(arg_name_hyphen, default)

    def add_doc(self, doc_name, doc_contents=None, doc_args = None):
        """
        Creates a new Doc object for an on-the-fly document.
        """
        self.log_debug("adding doc with contents type %s" % doc_contents.__class__.__name__)
        doc_name = os_to_posix(doc_name)
        if not posixpath.sep in doc_name:
            doc_name = posixpath.join(self.input_data.parent_dir(), doc_name)

        doc_ext = os.path.splitext(doc_name)[1]

        additional_doc_filters = self.setting('additional-doc-filters')
        self.log_debug("additional-doc-filters are %s" % additional_doc_filters)

        
        additional_doc_settings = self.setting('additional-doc-settings')

        settings = None
        if isinstance(additional_doc_settings, list):
            # figure out which settings to apply based on file extension
            for pattern, settings in additional_doc_settings:
                if doc_ext == pattern or pattern == ".*":
                    break
        elif isinstance(additional_doc_settings, dict):
            settings = additional_doc_settings

        else:
            raise Exception("Unexpected type %s" % type(settings))

        if doc_args:
            settings.update(doc_args)

        self.log_debug("additional-doc-settings are %s" % settings)


        def create_doc(name, filters, contents, args=None):
            if filters:
                doc_key = "%s|%s" % (name, filters)
            else:
                doc_key = name

            if not args:
                args = {}

            doc = dexy.doc.Doc(
                    doc_key,
                    self.doc.wrapper,
                    [],
                    contents=contents,
                    **args
                    )

            doc.output_data().setup()
            doc.output_data().storage.connect()

            self.doc.add_additional_doc(doc)
            return doc

        doc = None

        if isinstance(additional_doc_filters, str):
            doc = create_doc(doc_name,
                    additional_doc_filters, doc_contents, settings)

        elif isinstance(additional_doc_filters, list):
            for f in reversed(additional_doc_filters):
                doc = create_doc(doc_name, f, doc_contents, settings)

        elif isinstance(additional_doc_filters, dict):
            filters = additional_doc_filters.get(doc_ext)
            if isinstance(filters, list):
                for f in filters:
                    doc = create_doc(doc_name, f, doc_contents, settings)
            elif isinstance(filters, str):
                doc = create_doc(doc_name, filters, doc_contents, settings)
            elif filters is None:
                pass
            else:
                msg = "additional_doc_filters values should be list of string. Received %s"
                msgargs = filters.__class__.__name__
                raise Exception(msg % msgargs)

        else:
            msg = "additional-doc-filters should be string, list or dict. Received %s"
            msgargs = additional_doc_filters.__class__.__name__
            raise dexy.exceptions.InternalDexyProblem(msg % msgargs)

        if self.setting('keep-originals') or doc is None:
            doc = create_doc(doc_name, '', doc_contents, settings)

        return doc

    def workspace(self):
        """
        Directory in which all working files for this filter are stored.

        The `populate_workspace` method will populate this directory with
        inputs to this filter.
        """
        ws = self.doc.wrapper.work_cache_dir()
        return os.path.join(ws, self.storage_key[0:2], self.storage_key)

    def parent_work_dir(self):
        """
        Within the 'workspace', this is the parent directory of the file to be
        processed. This is the directory which subprocess/pexpect will 'cwd' to
        and execute processes.
        """
        return os.path.join(self.workspace(), self.output_data.parent_dir())

    def work_input_filename(self):
        """
        Name of work file to use input from. Processes will take this file name
        as input. Does not contain full path to file, just the file name. File
        will be in parent_work_dir() and processes should set their working
        directory to parent_work_dir() before running.
        """
        if self.ext and (self.ext == self.prev_ext):
            return "%s-work%s" % (self.input_data.baserootname(), self.prev_ext)
        else:
            return self.input_data.basename()

    def work_input_filepath(self):
        return os.path.join(self.parent_work_dir(), self.work_input_filename())

    def work_output_filename(self):
        """
        Name of work file to save output to. Processes will take this file name
        as output. Does not contain full path to file, just the file name. File
        will be in parent_work_dir() and processes should set their working
        directory to parent_work_dir() before running.
        """
        return self.output_data.basename()

    def work_output_filepath(self):
        return os.path.join(self.parent_work_dir(), self.work_output_filename())

    def include_input_in_workspace(self, inpt):
        """
        Whether to include the contents of the input file inpt in the workspace
        for this filter.
        """
        workspace_includes = self.setting('workspace-includes')

        if workspace_includes is not None:
            if inpt.ext in workspace_includes:
                self.log_debug("Including %s because file extension matches." % inpt)
                return True
            elif inpt.output_data().basename() in workspace_includes:
                self.log_debug("Including %s because base name matches." % inpt)
                return True
            else:
                self.log_debug("Excluding %s because does not match workspace-includes" % inpt)
                return False

        elif not inpt.filters:
            self.log_debug("Including because %s has no filters." % inpt)
            return True

        elif inpt.filters[-1].setting('override-workspace-exclude-filters'):
            self.log_debug("Including %s because override-workspace-exclude-filters is set." % inpt)
            return True

        else:
            workspace_exclude_filters = self.setting('workspace-exclude-filters')

            if workspace_exclude_filters is None:
                self.log_debug("Including because exclude_filters is None.")
                return True
            elif any(a in workspace_exclude_filters for a in inpt.filter_aliases):
                self.log_debug("Excluding %s because of workspace-exclude-filters" % inpt)
                return False
            else:
                self.log_debug("Including %s because not excluded" % inpt)
                return True

    def makedirs(self):
        mkdirs = self.setting('mkdirs')

        # mkdir should be a string, but handle either string or list
        mkdir = self.setting('mkdir')
        if mkdir:
            if isinstance(mkdir, str):
                mkdirs.append(mkdir)
            else:
                mkdirs.extend(mkdir)

        for d in mkdirs:
            dirpath = os.path.join(self.workspace(), d)
            self.log_debug("Creating directory %s" % dirpath)
            os.makedirs(dirpath)

    def populate_workspace(self):
        """
        Populates the workspace directory with inputs to the filter, under
        their canonical names.
        """
        self.log_debug("in populate_workspace method")
        already_created_dirs = set()
        wd = self.parent_work_dir()

        self._files_workspace_populated_with = set()

        self.doc.wrapper.trash(wd)

        try:
            os.makedirs(wd)
            already_created_dirs.add(wd)
        except OSError:
            msg = "workspace '%s' for filter '%s' already exists"
            msgargs = (os.path.abspath(wd), self.key,)
            raise dexy.exceptions.InternalDexyProblem(msg % msgargs)

        self.makedirs()

        traditional_input_docs = list(self.doc.walk_input_docs())
        input_docs = traditional_input_docs + self.doc.additional_docs
        self.log_debug("input docs %s" % input_docs)

        for i, inpt in enumerate(input_docs):
            if not self.include_input_in_workspace(inpt):
                self.log_debug("not populating workspace with input '%s'" % inpt.key)
                continue

            data = inpt.output_data()

            filepath = data.name

            # Ensure parent dir exists.
            parent_dir = os.path.join(self.workspace(), os.path.dirname(filepath))
            if not parent_dir in already_created_dirs:
                try:
                    os.makedirs(parent_dir)
                    already_created_dirs.add(parent_dir)
                except OSError:
                    pass

            # Save contents of file to workspace
            self.log_debug("populating workspace with %s for %s" % (filepath, inpt.key))
            file_dest = os.path.join(self.workspace(), filepath)

            try:
                if i > len(traditional_input_docs)-1:
                    contents = inpt.setting('contents')
                    data.storage.write_data(contents, file_dest)
                else:
                    copy_or_link(data, file_dest, use_links=False)

            except Exception as e:
                self.log_debug("problem populating working dir with input %s" % data.key)
                self.log_debug(e)

            self._files_workspace_populated_with.add(filepath)

        self.input_data.output_to_file(self.work_input_filepath())
        rel_path_to_work_file = os.path.join(os.path.dirname(self.key), self.work_input_filename())
        self._files_workspace_populated_with.add(rel_path_to_work_file)

        self.custom_populate_workspace()

    def custom_populate_workspace(self):
        """
        Allow filters to run the standard populate_workspace, and also do extra
        things to workspace after populate_workspace runs. Filters can also
        just override populate_workspace.
        """
        pass

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
        if hasattr(self.doc, 'parent'):
            return hasattr(self.doc.parent, 'script_storage')

    def script_storage(self):
        if not self.is_part_of_script_bundle():
            msg = "%s must be part of script bundle to access script storage"
            raise dexy.exceptions.UserFeedback(msg % self.key)
        return self.doc.parent.script_storage

class DexyFilter(Filter):
    """
    Filter which implements some default behaviors.
    """
    aliases = ['dexy']

    def process(self):
        if hasattr(self, "process_text"):
            output = self.process_text(str(self.input_data))
            self.output_data.set_data(output)
        else:
            self.output_data.copy_from_file(self.input_data.storage.data_file())

class AliasFilter(DexyFilter):
    """
    Filter to be used when an Alias is specified. Should not change input.
    """
    aliases = ['-']
    _settings = {
            'preserve-prior-data-class' : True
            }

    def calculate_canonical_name(self):
        return self.input_data.name

def filters_by_tag():
    """
    Returns a dict with tags as keys and lists of corresponding filter instances as values.
    """
    tags_filters = {}
    for filter_instance in Filter:
        if filter_instance.setting('nodoc'):
            continue

        for tag in filter_instance.setting('tags'):
            if not tag in tags_filters:
                tags_filters[tag] = []
            tags_filters[tag].append(filter_instance)

    return tags_filters

def filter_aliases_by_tag():
    tags_filters = filters_by_tag()
    tags = sorted(tags_filters.keys())
    return [(tag,
            [(filter_instance.alias, filter_instance.setting('help'))
                for filter_instance in sorted(tags_filters[tag], key=attrgetter('alias'))])
            for tag in tags]
