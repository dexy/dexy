from dexy.artifact import Artifact
from dexy.constants import Constants
from dexy.filters.templating_filters import JinjaTextFilter
from dexy.filters.templating_filters import JinjaFilterException

def init_jinja_filter():
    artifact = Artifact()
    artifact.name = "" # None causes problems with os.stat

    f = JinjaTextFilter()
    f.artifact = artifact
    f.log = Constants.NULL_LOGGER
    return f

def test_jinja_filter():
    f = init_jinja_filter()
    assert f.process_text("hello") == "hello"

def test_jinja_filter_with_basic_tag():
    f = init_jinja_filter()
    assert f.process_text("1 + 1 = {{ 1+1 }}") == "1 + 1 = 2"

def test_undefined_exception():
    f = init_jinja_filter()
    text = "{{ hello }}"
    f.artifact.input_data_dict = { '1' : text }
    f.artifact.previous_artifact_filepath = "file"
    try:
        f.process_text(text)
        assert False, "should not get here"
    except JinjaFilterException as e:
        assert "'hello' is undefined" in e.message

def test_undefined_exception_in_latex():
    f = init_jinja_filter()
    text = "<< hello >>"
    f.artifact.ext = ".tex"
    f.artifact.input_data_dict = { '1' : text }
    f.artifact.previous_artifact_filepath = "file"
    try:
        print f.process_text(text)
        assert False, "should not get here"
    except JinjaFilterException as e:
        print e.message
        assert "'hello' is undefined" in e.message

def test_syntax_error():
    text = "{{ [ }}"
    f = init_jinja_filter()
    f.artifact.input_data_dict = { '1' : text }
    f.artifact.previous_artifact_filepath = "file"

    try:
        f.process_text(text)
        assert False, "should not get here"
    except JinjaFilterException as e:
        assert "line 1 of file" in e.message
        assert ">>> {{ [ }}" in e.message
        assert "unexpected '}', expected ']'" in e.message

def test_syntax_error_in_latex():
    text = "<< [ >>"
    f = init_jinja_filter()
    f.artifact.ext = ".tex"
    f.artifact.input_data_dict = { '1' : text }
    f.artifact.previous_artifact_filepath = "file"

    try:
        f.process_text(text)
        assert False, "should not get here"
    except JinjaFilterException as e:
        assert "line 1 of file" in e.message
        assert ">>> << [ >>" in e.message
        assert "unexpected '>'" in e.message
