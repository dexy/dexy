from dexy.dexy_filter import DexyFilter
import textile

class TextileFilter(DexyFilter):
    INPUT_EXTENSIONS = ['.txt', '.textile']
    OUTPUT_EXTENSIONS = ['.html']
    ALIASES = ['pytextile']

    def process_text(self, input_text):
        return textile.textile(input_text)

