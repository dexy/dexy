from dexy.dexy_filter import DexyFilter
import markdown

class MarkdownFilter(DexyFilter):
    INPUT_EXTENSIONS = ['.*']
    OUTPUT_EXTENSIONS = ['.html']
    ALIASES = ['markdown']

    def process_text(self, input_text):
        return markdown.markdown(input_text)


