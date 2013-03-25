import time
from dexy.common import OrderedDict
import dexy.exceptions
import dexy.filter
import dexy.node
import os
import posixpath
import stat

class Doc(dexy.node.Node):
    """
    Node representing a single doc.
    """
    aliases = ['doc']

    def canonical_name_from_args(self):
        raw_arg_name = self.arg_value('canonical-name')
    
        if raw_arg_name:
            raw_arg_name = raw_arg_name % self.args

            if "/" in raw_arg_name:
                return raw_arg_name
            else:
                return posixpath.join(posixpath.dirname(self.key), raw_arg_name)

    def setup_initial_data(self):
        canonical_name = self.canonical_name_from_args() or self.name
        storage_key = "%s-000" % self.hashid

        if self.arg_value('output') is not None:
            canonical_output = self.arg_value('output')
        else:
            canonical_output = len(self.filter_aliases) == 0

        self.initial_data = dexy.data.Data.create_instance(
                self.data_class_alias(),
                self.name,
                self.ext,
                canonical_name,
                storage_key,
                {},
                None,
                canonical_output,
                self.wrapper
                )

        self.initial_data.setup_storage()
        self.doc_changed = self.check_doc_changed()

        if self.name in self.wrapper.filemap:
            # This is a real file on the file system.
            self.initial_data.copy_from_file(self.name)
        else:
            is_dummy = self.initial_data.is_cached() and self.get_contents() == 'dummy contents'
            if is_dummy:
                self.initial_data.load_data()
            else:
                self.initial_data.set_data(self.get_contents())

    def check_doc_changed(self):
        if self.name in self.wrapper.filemap:
            live_stat = self.wrapper.filemap[self.name]['stat']
            cache_stat = self.initial_data.storage.stat()
            if cache_stat:
                # we have a file in the cache, compare its mtime to filemap
                # to determine whether it has changed
                cache_mtime = cache_stat[stat.ST_MTIME]
                live_mtime = live_stat[stat.ST_MTIME]
                msg = "cache mtime %s live mtime %s now %s changed (live gt cache) %s"
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

    def get_contents(self):
        contents = self.args.get('contents')
        return contents

    def run(self):
        self.start_time = time.time()
        for f in self.filters:
            f.process()
        self.finish_time = time.time()
        self.elapsed_time = self.finish_time - self.start_time
        self.wrapper.batch.add_doc(self)
        self.save_runtime_args()
        self.save_additional_docs()

    def output_data(self):
        if self.filters:
            return self.filters[-1].output_data
        else:
            return self.initial_data

    def batch_info(self):
        return {
                'title' : self.output_data().title(),
                'input-data' : self.initial_data.args_to_data_init(),
                'output-data' : self.output_data().args_to_data_init(),
                'filters-data' : [f.output_data.args_to_data_init() for f in self.filters],
                'start_time' : self.start_time,
                'finish_time' : self.finish_time,
                'elapsed' : self.elapsed_time
                }

    def setup(self):
        self.name = self.key.split("|")[0]
        self.ext = os.path.splitext(self.name)[1]
        self.filter_aliases = self.key.split("|")[1:]
        self.filters = []
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
