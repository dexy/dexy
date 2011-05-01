from dexy.handler import DexyHandler
import textile

class TextileHandler(DexyHandler):
    INPUT_EXTENSIONS = ['.txt', '.textile']
    OUTPUT_EXTENSIONS = ['.html']
    ALIASES = ['pytextile']

    def process_text(self, input_text):
        return textile.textile(input_text)

