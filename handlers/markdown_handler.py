from dexy.handler import DexyHandler
import markdown

class MarkdownHandler(DexyHandler):
    INPUT_EXTENSIONS = ['.*']
    OUTPUT_EXTENSIONS = ['.html']
    ALIASES = ['markdown']

    def process_text(self, input_text):
        return markdown.markdown(input_text)


