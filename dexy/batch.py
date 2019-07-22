import uuid
import pickle
import os
import dexy.data

class Batch(object):
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.docs = {}
        self.doc_keys = {}
        self.filters_used = []
        self.uuid = str(uuid.uuid4())
        self.start_time = None
        self.end_time = None

    def __repr__(self):
        return "Batch(%s)" % self.uuid

    def __iter__(self):
        for doc_key in self.docs:
            if self.docs[doc_key]['state'] in ('uncached',):
                continue
            yield self.output_data(doc_key)

    def add_doc(self, doc):
        """
        Adds a new doc to the batch of docs.
        """
        if hasattr(doc, 'batch_info'):
            doc_key = doc.key_with_class()
            storage_key = doc.output_data().storage_key
            self.doc_keys[storage_key] = doc_key
            self.update_doc_info(doc)
            self.filters_used.extend(doc.filter_aliases)

    def update_doc_info(self, doc):
        self.docs[doc.key_with_class()] = doc.batch_info()

    def output_data(self, doc_key):
        return self.data(doc_key, 'output')

    def input_data(self, doc_key):
        return self.data(doc_key, 'input')

    def doc_info(self, doc_key):
        return self.docs[doc_key]
   
    def doc_key(self, storage_key):
        return self.doc_keys[storage_key]

    def data_for_storage_key(self, storage_key, input_or_output='output'):
        """
        Retrieves a data object given the storage key (based on the the
        md5sum), rather than the canonical doc key based on the doc name.
        """
        doc_key = self.doc_key(storage_key)
        return self.data(doc_key, input_or_output)

    def data(self, doc_key, input_or_output='output'):
        """
        Retrieves a data object given the doc key.
        """
        doc_info = self.doc_info(doc_key)["%s-data" % input_or_output]
        args = list(doc_info)
        args.append(self.wrapper)
        data = dexy.data.Data.create_instance(*args)
        data.setup_storage()
        if hasattr(data.storage, 'connect'):
            data.storage.connect()
        return data

    def elapsed(self):
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        else:
            return 0

    def filename(self):
        return "%s.pickle" % self.uuid

    def filepath(self):
        return os.path.join(self.batch_dir(), self.filename())

    def most_recent_filename(self):
        return os.path.join(self.batch_dir(), 'most-recent-batch.txt')

    def batch_dir(self):
        return os.path.join(self.wrapper.artifacts_dir, 'batches')

    def to_dict(self):
        attr_names = ['docs', 'doc_keys', 'filters_used', 'uuid']
        return dict((k, getattr(self, k),) for k in attr_names)

    def save_to_file(self):
        try:
            os.makedirs(self.batch_dir())
        except OSError:
            pass

        with open(self.filepath(), 'wb') as f:
            pickle.dump(self.to_dict(), f)

        with open(self.most_recent_filename(), 'w') as f:
            f.write(self.uuid)

    def load_from_file(self):
        with open(self.filepath(), 'rb') as f:
            d = pickle.load(f)
            for k, v in d.items():
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
