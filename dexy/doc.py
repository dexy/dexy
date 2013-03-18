from dexy.common import OrderedDict
import dexy.exceptions
import dexy.filter
import dexy.node
import os
import time

class Doc(dexy.node.Node):
    """
    Node representing a single doc.
    """
    aliases = ['doc']

    def setup_initial_data(self):
        canonical_name = self.key
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

        if self.name in self.wrapper.filemap:
            # This is a real file on the file system.
            self.initial_data.copy_from_file(self.name)
        else:
            self.initial_data.set_data(self.get_contents())

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
        print "appending info to batch for", self.key_with_class()
        self.wrapper.batch.docs[self.key_with_class()] = self.batch_info()

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

            f.setup(filter_key, storage_key, prev_filter, next_filter)
            f.update_settings(self.args.get(f.alias, {}))
            prev_filter = f
