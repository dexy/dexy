from dexy.filter import DexyFilter

try:
    import mistune
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class MistuneFilter(DexyFilter):
    """
    Runs mistune processor to convert markdown to HTML.

    """
    aliases = ['mistune']
    _settings = {
            'input-extensions' : ['.*'],
            'output-extensions' : ['.html'],
            'escape' : True,
            'hard_wrap' : False,
            'use_xhtml' : False,
            'parse_block_html' : False,
            'parse_inline_html' : False
            }

    def process_text(self, input_text):
        md = mistune.Markdown(
                escape = self.setting('escape'),
                hard_wrap = self.setting('hard_wrap'),
                use_xhtml = self.setting('use_xhtml'),
                parse_block_html = self.setting('parse_block_html'),
                parse_inline_html = self.setting('parse_inline_html')
                )
        return md(input_text)
