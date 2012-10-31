from dexy.filter import DexyFilter
import dexy.exceptions
import logging
import json

try:
    import markdown
    AVAILABLE = True
except ImportError as e:
    AVAILABLE = False

class MarkdownFilter(DexyFilter):
    """
    Runs a Markdown processor to convert markdown to HTML.

    Markdown extensions can be enabled in your config:
    http://packages.python.org/Markdown/extensions/index.html
    """
    INPUT_EXTENSIONS = ['.*']
    OUTPUT_EXTENSIONS = ['.html']
    ALIASES = ['markdown']
    DEFAULT_EXTENSIONS = {'toc' : {}}

    @classmethod
    def is_active(klass):
        return AVAILABLE

    def process_text(self, input_text):
        markdown_logger = logging.getLogger('MARKDOWN')
        markdown_logger.addHandler(self.log.handlers[-1])

        if len(self.args()) > 0:
            extensions = self.args().keys()
            extension_configs = self.args()
        else:
            extensions = self.DEFAULT_EXTENSIONS.keys()
            extension_configs = self.DEFAULT_EXTENSIONS

        dbg = "Initializing Markdown with extensions: %s and extension configs: %s"
        self.log.debug(dbg % (json.dumps(extensions), json.dumps(extension_configs)))

        try:
            md = markdown.Markdown(
                    extensions=extensions,
                    extension_configs=extension_configs)
        except ValueError as e:
            self.log.debug(e.message)
            if "markdown.Extension" in e.message:
                raise dexy.exceptions.UserFeedback("There's a problem with the markdown extensions you specified.")
            else:
                raise e
        except KeyError as e:
            raise dexy.exceptions.UserFeedback("Couldn't find a markdown extension option matching '%s'" % e.message)

        return md.convert(input_text)
