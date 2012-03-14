from dexy.dexy_filter import DexyFilter
import markdown

class MarkdownFilter(DexyFilter):
    INPUT_EXTENSIONS = ['.*']
    OUTPUT_EXTENSIONS = ['.html']
    ALIASES = ['markdown']

    def process_text(self, input_text):
        extensions = ['toc']
        extension_configs = {'toc' : { "anchorlink" : True }}

        md = markdown.Markdown(
                extensions=extensions,
                extension_configs=extension_configs
                )
        return md.convert(input_text)


