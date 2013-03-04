from dexy.common import OrderedDict
from dexy.version import DEXY_VERSION
import dexy.data
import dexy.doc
import dexy.exceptions
import dexy.filter
import dexy.metadata
import dexy.node
import dexy.task
import hashlib
import inspect
import json
import os
import posixpath
import re
import shutil
import stat
import time

class Artifact(dexy.task.Task):
    """
    Task classes representing steps in dexy processing.
    """
    def __init__(self, key, **kwargs):
        super(Artifact, self).__init__(key, **kwargs)
        self.created_by_doc = None
        self.remaining_doc_filters = []
        self.elapsed = 0.0
        self._wd_setup = False

    def key_for_log(self):
        if len(self.remaining_doc_filters) > 0:
            return "%s(|%s)" % (self.key, "|".join(self.remaining_doc_filters))
        else:
            return self.key

    def key_with_class(self):
        return "%s:%s" % (self.__class__.__name__, self.key_for_log())

    def input_filename(self):
        if self.ext and (self.ext == self.prior.ext):
            return "%s-work%s" % (self.input_data.baserootname(), self.prior.ext)
        else:
            return self.input_data.basename()

    def output_filename(self):
        return self.output_data.basename()

    def canonical_name_from_args(self):
        raw_arg_name = self.doc.arg_value('canonical-name')

        if raw_arg_name:
            if "/" in raw_arg_name:
                return raw_arg_name
            else:
                return posixpath.join(posixpath.dirname(self.key), raw_arg_name)

    def calculate_canonical_name(self):
        from_args = self.canonical_name_from_args()
        if from_args:
            return from_args % self.args
        else:
            name_without_ext = posixpath.splitext(self.key)[0]
            return "%s%s" % (name_without_ext, self.ext)

    def wd(self):
        return os.path.join(self.wrapper.artifacts_dir, self.hashstring)

    def full_wd(self):
        return os.path.join(self.wd(), os.path.dirname(self.key))

    def setup_wd(self, input_filename):
        """
        Sets up a working directory for this artifact. Removes any working
        directory that already exists. Yields input docs so behaviour can be
        customized per-filter.
        """
        wd = self.wd()
        full_wd = self.full_wd()

        shutil.rmtree(wd, ignore_errors=True)
        os.makedirs(full_wd)

        parent_dirs_created = set([full_wd])

        for doc in self.doc.node.walk_input_docs():
            if doc.state == 'complete' or len(doc.filters) == 0:
                exclude_wd = self.args.get('exclude_wd')
                if exclude_wd and re.search(exclude_wd, doc.key):
                    msg = "not saving '%s' to wd for '%s' because matches exclude_wd pattern '%s'"
                    msg_args = (doc.key, self.key, exclude_wd,)
                    self.log.debug(msg % msg_args)

                else:
                    # Figure out path to write this child doc.
                    input_filepath = os.path.join(wd, doc.output().name)
                    parent_dir = os.path.dirname(input_filepath)

                    # Ensure all parent directories exist.
                    if not parent_dir in parent_dirs_created:
                        try:
                            os.makedirs(parent_dir)
                            parent_dirs_created.add(parent_dir)
                        except os.error:
                            pass

                    yield(doc, input_filepath)

        input_filepath = os.path.join(full_wd, input_filename)
        self.input_data.output_to_file(input_filepath)
        self._wd_setup = True

    def data_class_alias(self):
        return 'generic'

    def setup_output_data(self):
        alias = self.data_class_alias()
        instanceargs = (self.key, self.ext, self.calculate_canonical_name(), self.hashstring, self.args, self.wrapper,)
        self.output_data = dexy.data.Data.create_instance(alias, *instanceargs)
        self.output_data_type = self.output_data.ALIASES[0]

    def setup(self):
        self.set_log()
        self.log.debug("setting up %s" % self.key_with_class())

        self.set_extension()

        self.metadata = dexy.metadata.Md5()
        self.set_metadata_attrs()

        # sets hashstring w/o node data, will be set again by node.
        self.set_hashstring()

        if hasattr(self, 'prior') and self.prior:
            self.input_data = self.prior.output_data
        self.setup_output_data()

class InitialArtifact(Artifact):
    """
    The artifact class representing an initial artifact, pretty much just a copy of the original file being processed.
    """
    def append_child_hashstrings(self):
        pass

    def set_metadata_attrs(self):
        self.metadata.key = self.key

        stat_info = self.wrapper.filemap[self.name]['stat']
        self.metadata.mtime = stat_info[stat.ST_MTIME]
        self.metadata.size = stat_info[stat.ST_SIZE]

    def set_output_data(self):
        self.output_data.copy_from_file(self.name)

    def set_extension(self):
        self.ext = os.path.splitext(self.name)[1]

    def run(self, *args, **kw):
        self.log.debug("hashstring is %s" % self.hashstring)
        if self.wrapper.timing:
            start_time = time.time()
        if not self.output_data.is_cached():
            self.set_output_data()
        if self.wrapper.timing:
            self.elapsed = time.time() - start_time

class InitialVirtualArtifact(InitialArtifact):
    """
    The artifact class representing an initial virtual artifact, basically just holds the contents specified in config.
    """
    def get_contents(self):
        contents = self.args.get('contents')
        if not contents and not isinstance(contents, dict):
            msg = "No contents found for virtual file '%s'.\n" % self.key
            msg += inspect.cleandoc("""If you didn't mean to request a virtual file of this name,
            and want dexy to look for only real files, you need a wildcard character
            in the file name. Otherwise either assign contents to the virtual file
            or remove the entry from your config file.""")
            raise dexy.exceptions.UserFeedback(msg)
        return contents

    def get_contents_hash(self):
        if self.args.get('contentshash'):
            return self.args['contentshash']
        else:
            contents = self.get_contents()
            if isinstance(contents, basestring):
                try:
                    return hashlib.md5(contents).hexdigest()
                except UnicodeEncodeError:
                    return hashlib.md5(contents.encode("utf-8")).hexdigest()
            else:
                try:
                    return hashlib.md5(unicode(contents)).hexdigest()
                except UnicodeDecodeError:
                    return hashlib.md5(str(contents)).hexdigest()

    def data_class_alias(self):
        data_class_alias = self.args.get('data-class-alias')

        if data_class_alias:
            return data_class_alias
        else:
            contents = self.get_contents()
            if isinstance(contents, OrderedDict):
                return 'sectioned'
            elif isinstance(contents, dict):
                return 'keyvalue'
            else:
                return 'generic'

    def set_metadata_attrs(self):
        if self.args.get('dirty'):
            self.metadata.dirty = time.time()

        self.metadata.key = self.key
        self.metadata.contentshash = self.get_contents_hash()

    def set_output_data(self):
        self.output_data.set_data(self.get_contents())

class FilterArtifact(Artifact):
    """
    Artifact class which applies filter processing to input from previous step.
    """
    def data_class_alias(self):
        if self.filter_instance.setting('preserve-prior-data-class'):
            return self.input_data.__class__.ALIASES[0]
        else:
            return self.filter_instance.data_class_alias(self.ext)

    def calculate_canonical_name(self):
        from_args = self.canonical_name_from_args()
        if from_args:
            return from_args % self.args
        else:
            return self.filter_instance.calculate_canonical_name()

    def update_args(self, new_args):
        """
        Update the 'args' for this artifact.
        """
        self.args.update(new_args)
        self.filter_instance.update_settings(new_args.get(self.filter_alias, {}))

    def setup_filter_instance(self):
        self.filter_instance = dexy.filter.Filter.create_instance(self.filter_alias)
        self.filter_instance.artifact = self
        self.filter_instance.log = self.log
        self.filter_instance.update_settings(self.args.get(self.filter_alias, {}))

    def run(self, *args, **kw):
        if self.wrapper.timing:
            start_time = time.time()
        self.log.debug("Running %s" % self.key_with_class())

        is_cached = self.output_data.is_cached()
        cache_ok = False

        if is_cached:
            self.log.info("output is cached (hashstring %s)" % self.hashstring)
            cache_ok = self.load_cached_args()
            if cache_ok:
                self.reconstitute_cached_children()
                self.content_source = 'cached'
            else:
                self.output_data.clear_cache()
                self.output_data.setup()

        if (not is_cached) or (not cache_ok):
            self.log.info("output is not cached (hashstring %s)" % self.hashstring)
            self.filter_instance.process()
            if not self.output_data.is_cached():
                if self.filter_instance.setting('require-output'):
                    raise dexy.exceptions.NoFilterOutput("No output file after filter ran: %s" % self.key)
            self.content_source = 'generated'

        if self.wrapper.timing:
            self.elapsed = time.time() - start_time

    def load_cached_args(self):
        """
        Loads args from cache in case they have changed, returns False if cache is corrupt.
        """
        rows = self.wrapper.db.task_from_previous_batch(self.hashstring)

        if len(rows) == 0:
            rows = self.wrapper.db.task_from_current_batch(self.hashstring)

        if len(rows) == 0:
            raise dexy.exceptions.InternalDexyProblem("No rows found for %s in current or previous batch." % self.hashstring)

        raw_args = rows[0]['args']

        if not raw_args:
            self.log.debug("args not found in DB, cache may be corrupt")
            self.log.debug(rows[0])
            return False
        else:
            stored_args = json.loads(raw_args)
            self.args.update(stored_args)
            self.doc.args.update(stored_args)
            return True

    def reconstitute_cached_children(self):
        """
        Look for artifacts which were created as side effects of this filter
        running, re-run these docs (which should be present in cache).
        """
        rows = self.wrapper.db.get_child_hashes_in_previous_batch(self.hashstring)
        for row in rows:
            self.log.debug("Reconstituting %s from database and cache" % row['doc_key'])
            if 'Initial' in row['class_name']:
                doc_args = json.loads(row['args'])
                doc = dexy.doc.Doc(row['doc_key'], **doc_args)
                self.add_doc(doc)

                new_calc_hashstring = doc.children[0].hashstring
                db_hashstring = row['hashstring']
                msg = "unexpected calculated hashstring '%s' for %s, expected '%s'" % (new_calc_hashstring, doc.children[0].key, db_hashstring)
                assert new_calc_hashstring == db_hashstring, msg

    def set_metadata_attrs(self):
        self.metadata.dexy_version = DEXY_VERSION
        self.metadata.ext = self.ext
        self.metadata.key = self.key
        self.metadata.next_filter_name = self.next_filter_name

        # hash of the artifact supplying input to this
        self.metadata.prior_hash = self.prior.hashstring

        # args passed to this document by user
        strargs = []
        skip_arg_keys = ['wrapper']
        for k in sorted(self.args):
            if not k in skip_arg_keys:
                v = str(self.args[k])
                strargs.append("%s: %s" % (k, v))
        self.metadata.argstr = ", ".join(strargs)

        # version of external software being run, if any
        if hasattr(self.filter_instance, 'version'):
            version = self.filter_instance.version()
            self.metadata.software_version = version

    def add_doc(self, doc, run=True):
        if doc.state == 'complete':
            raise Exception("Already complete!")

        self.log.debug("adding additional doc %s (created by %s)" % (doc.key, self.key))
        doc.created_by_doc = self.hashstring
        doc.created_by_doc_key = self.doc.key_with_class()
        doc.wrapper = self.wrapper
        doc.args['canon'] = True

        doc.node = self.doc.node
        self.doc.node.children.append(doc)

        if run:
            for task in (doc,):
                for t in task:
                    t()
            for task in (doc,):
                for t in task:
                    t()
            for task in (doc,):
                for t in task:
                    t()

    def set_extension(self):
        this_filter_outputs = self.filter_instance.setting('output-extensions')
        this_filter_accepts = self.filter_instance.setting('input-extensions')

        # Check that we can handle input extension
        if set([self.prior.ext, ".*"]).isdisjoint(set(this_filter_accepts)):
            msg = "Filter '%s' in '%s' can't handle file extension %s, supported extensions are %s"
            params = (self.filter_alias, self.key, self.prior.ext, ", ".join(this_filter_accepts))
            raise dexy.exceptions.UserFeedback(msg % params)

        # Figure out output extension
        ext = self.filter_instance.setting('ext')
        if ext:
            # User has specified desired extension
            if not ext.startswith('.'):
                ext = '.%s' % ext

            # Make sure it's a valid one
            if (not ext in this_filter_outputs) and (not ".*" in this_filter_outputs):
                msg = "You have requested file extension %s in %s but filter %s can't generate that."
                raise dexy.exceptions.UserFeedback(msg % (ext, self.key, self.filter_alias))

            self.ext = ext

        elif ".*" in this_filter_outputs:
            self.ext = self.prior.ext

        else:
            # User has not specified desired extension, and we don't output wildcards,
            # figure out extension based on next filter in sequence, if any.
            if self.next_filter_class:
                next_filter_accepts = self.next_filter_class.setting('input-extensions')

                if ".*" in next_filter_accepts:
                    self.ext = this_filter_outputs[0]
                else:
                    if set(this_filter_outputs).isdisjoint(set(next_filter_accepts)):
                        msg = "Filter %s can't go after filter %s, no file extensions in common."
                        raise dexy.exceptions.UserFeedback(msg % (self.next_filter_alias, self.filter_alias))

                    for e in this_filter_outputs:
                        if e in next_filter_accepts:
                            self.ext = e

                    if not self.ext:
                        msg = "no file extension found but checked already for disjointed, should not be here"
                        raise dexy.exceptions.InternalDexyProblem(msg)
            else:
                self.ext = this_filter_outputs[0]
