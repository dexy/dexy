from dexy.filter import Filter
import markdown
import json

class MarkdownFilter(Filter):
    """
    Runs a Markdown processor to convert markdown to HTML.

    Markdown extensions can be enabled in your config:
    http://packages.python.org/Markdown/extensions/index.html
    """
    INPUT_EXTENSIONS = ['.*']
    OUTPUT_EXTENSIONS = ['.html']
    ALIASES = ['markdown']

    def process_text(self, input_text):
        extensions = self.args().keys()
        extension_configs = self.args()

        dbg = "Initializing Markdown with extensions: %s and extension configs: %s"
        self.log.debug(dbg % (json.dumps(extensions), json.dumps(extension_configs)))

        md = markdown.Markdown(
                extensions=extensions,
                extension_configs=extension_configs)

        return md.convert(input_text)
