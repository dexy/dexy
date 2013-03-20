from dexy.common import OrderedDict
import dexy.exceptions
import dexy.filter
import dexy.node
import os
import time
import posixpath

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

        self.initial_data = dexy.data.Data.create_instance(
                self.data_class_alias(),
                self.name,
                self.ext,
                canonical_name,
                storage_key,
                {},
                None,
                self.wrapper
                )

        self.initial_data.setup_storage()
        self.doc_changed = self.check_doc_changed()

        if self.name in self.wrapper.filemap:
            # This is a real file on the file system.
            self.initial_data.copy_from_file(self.name)
        else:
            self.initial_data.set_data(self.get_contents())

    def check_doc_changed(self):
        if self.name in self.wrapper.filemap:
            live_stat = self.wrapper.filemap[self.name]['stat']
            cache_stat = self.initial_data.storage.stat()
            if cache_stat:
                # we have a file in the cache, compare its mtime to filemap
                # to determine whether it has changed
                import stat
                cache_mtime = cache_stat[stat.ST_MTIME]
                live_mtime = live_stat[stat.ST_MTIME]
                return live_mtime != cache_mtime
            else:
                # there is no file in the cache, therefore it has 'changed'
                return True
        else:
            # virtual
            # TODO check hash of contents
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
        self.run_start_time = time.time()

        for f in self.filters:
            f.process()

        self.run_finish_time = time.time()
        self.append_to_batch()

    def output_data(self):
        if self.filters:
            return self.filters[-1].output_data
        else:
            return self.initial_data

    def batch_info(self):
        return {
                'input-data' : self.initial_data.args_to_data_init(),
                'output-data' : self.output_data().args_to_data_init(),
                'start_time' : self.run_start_time,
                'finish_time' : self.run_finish_time,
                'elapsed' : self.run_finish_time - self.run_start_time
                }

    def append_to_batch(self):
        self.wrapper.batch.docs[self.key_with_class()] = self.batch_info()
        self.wrapper.batch.filters_used.extend(self.filter_aliases)

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
