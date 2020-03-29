import dexy.exceptions
import dexy.filter
import dexy.node
import os
import pickle
import shutil
import stat
import time

class Doc(dexy.node.Node):
    """
    A single Dexy document.
    """
    aliases = ['doc']
    _settings = {
            'contents' : (
                "Custom contents for a virtual document.",
                None
                ),
            'ws-template' : (
                "custom website template to apply.",
                None
                ),
            'data-type' : (
                "Alias of custom data class to use to store document content.",
                None
                ),
            'shortcut' : (
                "A nickname for document so you don't have to use full key.",
                None
                ),
            'title' : (
                "Custom title.",
                None
                ),
            'output-name' : (
                "Override default canonical name.",
                None
                ),
            'output' : (
                "Whether document should be included in output/ and output-site/",
                None
                ),
            'dirty' : (
                'Whether document should always be regenerared.',
                False
                )
            }

    def name_args(self):
        name_args = self.setting_values()
        name_args['name'] = self.name
        name_args['rootname'] = os.path.splitext(self.name)[0]
        name_args['basename'] = os.path.basename(self.name)
        name_args['baserootname'] = os.path.splitext(os.path.basename(self.name))[0]
        name_args['dirname'] = os.path.dirname(self.name)
        name_args.update(self.safe_setting('environment', {}))
        return name_args

    def setup_output_name(self):
        """
        Applies string interpolation to %(foo)s settings in output name.
        """
        if not self.setting('output-name'):
            return

        name_args = self.name_args()
        output_name = self.setting('output-name')

        self.log_debug("Name interpolation variables:")
        for key, value in name_args.items():
            self.log_debug("%s: %s" % (key, value))

        if not "/" in output_name:
            output_name = os.path.join(os.path.dirname(self.name), output_name)
        elif output_name.startswith("/"):
            output_name = output_name.lstrip("/")

        try:
            if '%' in output_name:
                updated_output_name = output_name % name_args
            elif '{' in self.setting('output-name'):
                updated_output_name = output_name.format(**name_args)
            else:
                updated_output_name = output_name

        except KeyError as e:
            msg = "Trying to process %s but '%s' is not a valid key. Valid keys are: %s"
            msgargs = (output_name, str(e), ", ".join(sorted(name_args)))
            raise dexy.exceptions.UserFeedback(msg % msgargs)

        self.update_settings({'output-name' : updated_output_name})

    def setup(self):
        self.update_settings(self.args)

        self.name = self.key.split("|")[0]
        self.ext = os.path.splitext(self.name)[1]
        self.filter_aliases = self.key.split("|")[1:]
        self.filters = []

        self.setup_output_name()
        self.setup_initial_data()

        for alias in self.filter_aliases:
            f = dexy.filter.Filter.create_instance(alias, self)
            self.filters.append(f)

        prev_filter = None
        for i, f in enumerate(self.filters):
            filter_aliases = self.filter_aliases[0:i+1]
            filter_key = "%s|%s" % (self.name, "|".join(filter_aliases))
            storage_key = "%s-%03d-%s" % (self.hashid, i+1, "-".join(filter_aliases))

            if i < len(self.filters) - 1:
                next_filter = self.filters[i+1]
            else:
                next_filter = None

            filter_settings_from_args = self.args.get(f.alias, {})
            f.setup(filter_key, storage_key, prev_filter,
                    next_filter, filter_settings_from_args)
            prev_filter = f

    def setup_datas(self):
        """
        Convenience function to ensure all datas are set up. Should not need to be called normally.
        """
        for d in self.datas():
            if d.state == 'new':
                d.setup()

    def setup_initial_data(self):
        storage_key = "%s-000" % self.hashid

        if self.setting('output') is not None:
            canonical_output = self.setting('output')
        else:
            if len(self.filter_aliases) == 0:
                canonical_output = True
            else:
                canonical_output = None

        settings = {
                'canonical-name' : self.name,
                'canonical-output' : canonical_output,
                'shortcut' : self.setting('shortcut'),
                'output-name' : self.setting('output-name'),
                'title' : self.setting('title')
                }

        self.initial_data = dexy.data.Data.create_instance(
                self.data_class_alias(),
                self.name, # key
                self.ext, #ext
                storage_key,
                settings,
                self.wrapper
                )

    def consolidate_cache_files(self):
        for node in self.input_nodes():
            node.consolidate_cache_files()

        if self.state == 'cached':
            self.setup_datas()

            # move cache files to new cache
            for d in self.datas():
                if os.path.exists(d.storage.last_data_file()):
                    last_loc = d.storage.last_data_file()
                    this_loc = d.storage.this_data_file()

                    self.log_debug("moving %s from %s to %s..." % (d.key, last_loc, this_loc))
                    shutil.move(last_loc, this_loc)

            if os.path.exists(self.runtime_info_filename(False)):
                shutil.move(self.runtime_info_filename(False), self.runtime_info_filename(True))

            self.apply_runtime_info()

            for d in self.datas():
                if hasattr(d.storage, 'connect'):
                    d.storage.connect()
            self.transition('consolidated')

    def apply_runtime_info(self):
            runtime_info = self.load_runtime_info()
            if runtime_info:
                self.add_runtime_args(runtime_info['runtime-args'])
                self.load_additional_docs(runtime_info['additional-docs'])

    def datas(self):
        """
        Returns all associated `data` objects.
        """
        return [self.initial_data] + [f.output_data for f in self.filters]

    def update_setting(self, key, value):
        self.update_all_settings({key : value})

    def update_all_settings(self, new_settings):
        self.update_settings(new_settings)

        for data in self.datas():
            data.update_settings(new_settings)

        for f in self.filters:
            f.update_settings(new_settings)

    def check_cache_elements_present(self):
        """
        Returns a boolean to indicate whether all files are present in cache.
        """
        # Take this opportunity to ensure Data objects are in `setup` state.
        for d in self.datas():
            if d.state == 'new':
                d.setup()

        return all(
                os.path.exists(d.storage.last_data_file()) or
                os.path.exists(d.storage.this_data_file())
                for d in self.datas())

    def check_doc_changed(self):
        if self.setting('dirty'):
            return True
        elif self.name in self.wrapper.filemap:
            live_stat = self.wrapper.filemap[self.name]['stat']

            self.initial_data.setup()

            in_this_cache = os.path.exists(self.initial_data.storage.this_data_file())
            in_last_cache = os.path.exists(self.initial_data.storage.last_data_file())

            if in_this_cache or in_last_cache:
                # we have a file in the cache from a previous run, compare its
                # mtime to filemap to determine whether it has changed
                if in_this_cache:
                    cache_stat = os.stat(self.initial_data.storage.this_data_file())
                else:
                    cache_stat = os.stat(self.initial_data.storage.last_data_file())

                cache_mtime = cache_stat[stat.ST_MTIME]
                live_mtime = live_stat[stat.ST_MTIME]
                msg = "    cache mtime %s live mtime %s now %s changed (live gt cache) %s"
                msgargs = (cache_mtime, live_mtime, time.time(), live_mtime > cache_mtime)
                self.log_debug(msg % msgargs)
                return live_mtime > cache_mtime
            else:
                # there is no file in the cache, therefore it has 'changed'
                return True
        else:
            # TODO check hash of contents of virtual files
            return False

    def data_class_alias(self):
        data_class_alias = self.setting('data-type')

        if data_class_alias:
            return data_class_alias
        else:
            contents = self.get_contents()
            if isinstance(contents, dict):
                return 'keyvalue'
            elif isinstance(contents, list):
                return "sectioned"
            else:
                return 'generic'

    def get_contents(self):
        contents = self.setting('contents')
        return contents

    # Runtime Info
    def runtime_info_filename(self, this=True):
        name = "%s.runtimeargs.pickle" % self.hashid
        return os.path.join(self.initial_data.storage.storage_dir(this), name)

    def save_runtime_info(self):
        """
        Save runtime changes to metadata so they can be reapplied when node has
        been cached.
        """

        info = {
            'runtime-args' : self.runtime_args,
            'additional-docs' : self.additional_doc_info()
            }

        with open(self.runtime_info_filename(), 'wb') as f:
            pickle.dump(info, f)

    def load_runtime_info(self):
        info = None

        # Load from 'this' first
        try:
            with open(self.runtime_info_filename(), 'rb') as f:
                info = pickle.load(f)
        except IOError:
            pass

        # Load from 'last' if there's nothing in 'this'
        if not info:
            try:
                with open(self.runtime_info_filename(False), 'rb') as f:
                    info = pickle.load(f)
            except IOError:
                pass

        return info

    def run(self):
        if self.wrapper.directory != '.':
            if not self.wrapper.directory in self.name:
                print(("skipping", self.name, "not in", self.wrapper.directory))
                return

        self.start_time = time.time()

        if self.name in self.wrapper.filemap:
            # This is a real file on the file system.
            if self.doc_changed or not self.initial_data.is_cached():
                self.initial_data.copy_from_file(self.name)
        else:
            is_dummy = self.initial_data.is_cached() and self.get_contents() == 'dummy contents'
            if is_dummy:
                self.initial_data.load_data()
            else:
                self.initial_data.set_data(self.get_contents())

        for f in self.filters:
            f.start_time = time.time()
            if f.output_data.state == 'new':
                f.output_data.setup()
            if hasattr(f.output_data.storage, 'connect'):
                f.output_data.storage.connect()
            f.process()
            f.finish_time = time.time()
            f.elapsed = f.finish_time - f.start_time

        self.finish_time = time.time()
        self.elapsed_time = self.finish_time - self.start_time
        self.wrapper.batch.add_doc(self)
        self.save_runtime_info()

        # Run additional docs
        for doc in self.additional_docs:
            doc.check_is_cached()
            for task in doc:
                task()

    def output_data(self):
        """
        Returns a reference to the final data object for this document.
        """
        if self.filters:
            return self.filters[-1].output_data
        else:
            return self.initial_data

    def batch_info(self):
        return {
                'input-data' : self.initial_data.args_to_data_init(),
                'output-data' : self.output_data().args_to_data_init(),
                'filters-data' : [f.output_data.args_to_data_init() for f in self.filters],
                # below are convenience attributes, not strictly necessary for dexy to run
                'title' : self.output_data().title(),
                'start_time' : self.start_time,
                'finish_time' : self.finish_time,
                'elapsed' : self.elapsed_time,
                'state' : self.state
                }

    def finalize_additional_doc(self):
        """
        Fixes 'contents' setting of additional docs where initial content is
        set after creation.
        """
        self.update_settings({"contents" : self.output_data().data()})
