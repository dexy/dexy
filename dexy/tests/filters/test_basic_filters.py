from dexy.dexy_filter import DexyFilter
from dexy.document import Document
from dexy.tests.utils import run_dexy
from dexy.tests.utils import set_filter_list
from ordereddict import OrderedDict
import dexy.introspect

CONFIG = {
    "." : {
        "@test.txt|basic" : {"contents" : None },
        "@test.txt|basicb" : {"contents" : None }
    }
}

DATA = "this is the data!"

class BasicFilter(DexyFilter):
    ALIASES = ['basic']
    def process(self):
        self.artifact.data_dict['1'] = DATA

class BasicBinaryFilter(DexyFilter):
    ALIASES = ['basicb']
    BINARY = True
    def process(self):
        with open(self.artifact.filepath(), "wb") as f:
            f.write(DATA)

def test_basic_filter():
    set_filter_list([BasicFilter, BasicBinaryFilter])
    for doc in run_dexy(CONFIG):
        doc.run()
        assert doc.output() == DATA
