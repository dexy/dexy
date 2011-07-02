from dexy.dexy_filter import DexyFilter

class PicasaFilter(DexyFilter):
    INPUT_EXTENSIONS = ['.png', '.jpg']
    OUTPUT_EXTENSIONS = ['.txt', '.html']
    ALIASES = ['picasa']

    def process(self):
        pass
