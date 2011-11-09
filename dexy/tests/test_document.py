from dexy.dexy_filter import DexyFilter
from dexy.document import Document
import dexy.filters.pygments_filters
import dexy.introspect

def test_get_filter_for_alias():
    Document.filter_list = dexy.introspect.filters()
    d = Document()
    for k, v in d.__class__.filter_list.iteritems():
        assert isinstance(k, str)
        assert issubclass(v, DexyFilter)

    assert d.get_filter_for_alias("pyg") == dexy.filters.pygments_filters.PygmentsFilter
    assert d.get_filter_for_alias("-") == DexyFilter
    assert d.get_filter_for_alias("-xxxalias") == DexyFilter

def test_document_set_name_and_filters():
    doc = Document()
    doc.set_name_and_filters("data/test.py|abc")
    assert doc.name == "data/test.py"
    assert doc.filters == ['abc']

    doc.filters += ['def', 'xyz']
    assert doc.filters == ['abc', 'def', 'xyz']

    assert doc.key() == "data/test.py|abc|def|xyz"
