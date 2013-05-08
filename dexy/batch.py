import uuid
import os
import dexy.data

class Batch(object):
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.docs = {}
        self.docs_by_storage_key = {}
        self.uuid = str(uuid.uuid4())
        self.filters_used = []
        self.filter_elapsed_time = 0.0

    def __repr__(self):
        return "Batch(%s)" % self.uuid

    def __iter__(self):
        for doc_key in self.docs:
            yield self.doc_output_data(doc_key)

    def add_doc(self, doc):
        if hasattr(doc, 'batch_info'):
            doc_info = doc.batch_info()
            self.docs[doc.key_with_class()] = doc_info
            self.docs_by_storage_key[doc.output_data().storage_key] = doc_info

            self.filters_used.extend(doc.filter_aliases)

    def doc_filter_data(self, doc_key, filter_index):
        if not doc_key in self.docs:
            msg = "can't find doc key '%s' in docs" % doc_key
            raise dexy.exceptions.InternalDexyProblem(msg)
        doc_info = self.docs[doc_key]["filters-data"][filter_index]
        args = []
        args.extend(doc_info)
        args.append(self.wrapper)
        data = dexy.data.Data.create_instance(*args)
        data.setup_storage()
        return data

    def data_for_doc_info(self, doc_info):
        args = []
        args.extend(doc_info)
        args.append(self.wrapper)
        data = dexy.data.Data.create_instance(*args)
        data.setup_storage()
        if hasattr(data.storage, 'connect'):
            data.storage.connect()
        return data

    def data_for_storage_key(self, storage_key, input_or_output='output'):
        doc_info = self.docs_by_storage_key[storage_key]["%s-data" % input_or_output]
        return self.data_for_doc_info(doc_info)

    def doc_data(self, doc_key, input_or_output='output'):
        doc_info = self.docs[doc_key]["%s-data" % input_or_output]
        return self.data_for_doc_info(doc_info)

    def doc_output_data(self, doc_key):
        return self.doc_data(doc_key, 'output')

    def doc_input_data(self, doc_key):
        return self.doc_data(doc_key, 'input')

    def elapsed(self):
        return self.end_time - self.start_time

    def filename(self):
        return "%s.pickle" % self.uuid

    def filepath(self):
        return os.path.join(self.batch_dir(), self.filename())

    def most_recent_filename(self):
        return os.path.join(self.batch_dir(), 'most-recent-batch.txt')

    def batch_dir(self):
        return os.path.join(self.wrapper.artifacts_dir, 'batches')

    def to_dict(self):
        attr_names = ['docs', 'docs_by_storage_key', 'uuid', 'filters_used']
        return dict((k, getattr(self, k),) for k in attr_names)

    def save_to_file(self):
        try:
            os.makedirs(self.batch_dir())
        except OSError:
            pass

        with open(self.filepath(), 'w') as f:
            pickle = dexy.utils.pickle_lib(self.wrapper)
            pickle.dump(self.to_dict(), f)

        with open(self.most_recent_filename(), 'w') as f:
            f.write(self.uuid)

    def load_from_file(self):
        pickle = dexy.utils.pickle_lib(self.wrapper)
        with open(self.filepath(), 'r') as f:
            d = pickle.load(f)
            for k, v in d.iteritems():
                setattr(self, k, v)

    @classmethod
    def load_most_recent(klass, wrapper):
        """
        Retuns a batch instance representing the most recent batch as indicated
        by the UUID stored in most-recent-batch.txt.
        """
        batch = Batch(wrapper)
        try:
            with open(batch.most_recent_filename(), 'r') as f:
                most_recent_uuid = f.read()

            batch.uuid = most_recent_uuid
            batch.load_from_file()
            return batch
        except IOError:
            pass
