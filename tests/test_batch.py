from tests.utils import tempdir
from dexy.wrapper import Wrapper
import dexy.batch
import os

def test_batch():
    with tempdir():
        wrapper = Wrapper()
        wrapper.create_dexy_dirs()

        wrapper = Wrapper()
        batch = dexy.batch.Batch(wrapper)
        os.makedirs(batch.batch_dir())

        batch.save_to_file()
        assert batch.filename() in os.listdir(".dexy/batches")

        wrapper = Wrapper()
        batch = dexy.batch.Batch.load_most_recent(wrapper)

def test_batch_with_docs():
    with tempdir():
        wrapper = Wrapper(log_level='DEBUG', debug=True)
        wrapper.create_dexy_dirs()

        with open("hello.txt", "w") as f:
            f.write("hello")

        with open("dexy.yaml", "w") as f:
            f.write("hello.txt")

        wrapper = Wrapper()
        wrapper.run_from_new()

        batch = dexy.batch.Batch.load_most_recent(wrapper)
        assert batch

        for doc_key in batch.docs:
            assert batch.input_data(doc_key)
            assert batch.output_data(doc_key)
