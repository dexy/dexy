from dexy.artifact import Artifact
from dexy.dexy_filter import DexyFilter
from dexy.reporter import Reporter
import dexy.introspect
import inspect

def test_list_artifact_classes():
    artifact_classes = dexy.introspect.artifact_classes()
    assert len(artifact_classes) > 1
    for k, v in artifact_classes.iteritems():
        assert isinstance(k, str)
        assert issubclass(v, Artifact)

def test_list_filters():
    filters = dexy.introspect.filters()
    assert len(filters) > 1
    for k, v in filters.iteritems():
        assert isinstance(k, str)
        assert issubclass(v, DexyFilter)

def test_list_reporters():
    reporters = dexy.introspect.reporters()
    assert len(reporters) > 1
    for name, klass in reporters.iteritems():
        assert inspect.isclass(klass)
        assert issubclass(klass, Reporter)

def test_list_reports_dirs():
    reports_dirs = dexy.introspect.reports_dirs()
    assert len(reports_dirs) > 1
    for d in reports_dirs:
        assert isinstance(d, str)

