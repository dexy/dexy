from dexy.doc import Doc
from dexy.utils import char_diff
from dexy.tests.utils import wrap
from dexy.filter import DexyFilter

class PrePost(DexyFilter):
    ALIASES = ['prepost']

    def pre(self, *args, **kw):
        self.artifact.doc.pre_return = 42

    def post(self, *args, **kw):
        self.artifact.doc.post_return = 43

def test_pre_post():
    with wrap() as wrapper:
        child = Doc("child.txt|jinja",
                contents = CHILD_TEXT,
                wrapper=wrapper)

        parent = Doc("parent.txt|prepost",
                child,
                contents = "Hello",
                wrapper=wrapper)

        wrapper.run_docs(parent)

        assert child.output().as_text() == "Parent's pre return is 42\nParent's post return exists False"
        assert parent.pre_return == 42
        assert parent.post_return == 43

CHILD_TEXT = """\
Parent's pre return is {{ w.tasks['Doc:parent.txt|prepost'].pre_return }}
Parent's post return exists {{ hasattr(w.tasks['Doc:parent.txt|prepost'], 'post_return') }}"""
