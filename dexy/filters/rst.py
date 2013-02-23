from dexy.filter import DexyFilter

try:
    from docutils import core
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class RestructuredTextBase(DexyFilter):
    """
    Base class for ReST filters using the docutils library.
    """
    ALIASES = []

    _SETTINGS = {
            "input-extensions" : [".rst", ".txt"],
            'output-extensions' : [".html", ".tex", ".xml"],
            'output' : True,
            'writer' : ("Specify rst writer to use.", None),
            'stylesheet' : ("Stylesheet arg to pass to rst", None)
            }

    @classmethod
    def is_active(klass):
        return AVAILABLE

    def docutils_writer_name(self):
        if self.setting('writer'):
            return self.setting('writer')
        elif self.artifact.ext == ".html":
            return 'html'
        elif self.artifact.ext == ".tex":
            return 'latex2e'
        elif self.artifact.ext == ".xml":
            return 'docutils_xml'
        else:
            raise Exception("unsupported extension %s" % self.artifact.ext)

class RestructuredText(RestructuredTextBase):
    """
    A 'native' ReST filter which uses the docutils library.
    """
    ALIASES = ['rst']
    _SETTINGS = {
            'settings-for-settings-overrides' : (
                "Which of the settings should be passed to settings_overrides.",
                ['writer', 'stylesheet']
                )
            }

    def process(self):
        settings_overrides = dict((k, v) for k, v in self.setting_values().iteritems() if k in self.setting('settings-for-settings-overrides'))

        core.publish_file(
                source_path = self.input().storage.data_file(),
                destination_path = self.output().storage.data_file(),
                writer_name=self.docutils_writer_name(),
                settings_overrides=settings_overrides
                )

class RstBody(RestructuredTextBase):
    """
    Returns just the body part of an ReST document.
    """
    ALIASES = ['rstbody']

    def process_text(self, input_text):
        parts = core.publish_parts(
                input_text,
                writer_name=self.docutils_writer_name(),
                )
        if parts.has_key('title') and parts['title']:
            self.update_all_args({'title' : parts['title']})

        return parts['body']

class RstDocParts(DexyFilter):
    """
    Returns key-value storage of document parts.
    """
    ALIASES = ['rstdocparts']
    _SETTINGS = {
            'input-extensions' : [".rst", ".txt"],
            'output-data-type' : 'keyvalue',
            'output-extensions' : ['.sqlite3', '.json'],
            'writer' : ("Specify rst writer to use.", 'html')
            }

    def process(self):
        input_text = unicode(self.input())

        parts = core.publish_parts(
                input_text,
                writer_name = self.setting('writer')
                )

        for k, v in parts.iteritems():
            self.output().append(k, v)
        self.output().save()
