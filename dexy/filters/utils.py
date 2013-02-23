# Extra Pygments Lexers - will be submitted to Pygments and removed from here
# when available in a Pygments release

from pygments.lexers.templates import DjangoLexer
from pygments.lexer import DelegatingLexer
from pygments.lexers.text import RstLexer

class RstDjangoLexer(DelegatingLexer):
    """
    Subclass of the `DjangoLexer` that highlights unlexed data with the
    `RstLexer`.
    """

    name = 'ReStructuredText+Django/Jinja'
    aliases = ['rst+django', 'rst+jinja']
    filenames = ['*.rst']

    def __init__(self, **options):
        super(RstDjangoLexer, self).__init__(RstLexer, DjangoLexer, **options)

    def analyse_text(text):
        rv = DjangoLexer.analyse_text(text) - 0.01
        # TODO count how many times ".. " is in text
        if ".. " in text:
            rv += 0.4
        return rv
