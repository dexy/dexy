from dexy.dexy_filter import DexyFilter
from dexy.document import Document
from dexy.tests.utils import run_dexy
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

def set_filter_list(additional_filters):
    filters = dexy.introspect.filters()
    for filter_class in additional_filters:
        for a in filter_class.ALIASES:
            filters[a] = filter_class
    Document.filter_list = filters

def test_basic_filter():
    set_filter_list([BasicFilter, BasicBinaryFilter])
    for doc in run_dexy(CONFIG):
        doc.run()
        assert doc.output() == DATA
