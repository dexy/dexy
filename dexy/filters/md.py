from dexy.filter import DexyFilter
import dexy.exceptions
import json
import logging
import markdown

#safe_mode_docstring = """Whether to escape, remove or replace HTML blocks.
#
#Set to True or 'escape' to escape HTML, 'remove' to remove HTML, 'replace' to replace with replacement-text.
#"""
#            'safe-mode' : (safe_mode_docstring, False),
#            'replacement-text' : ("Text to replace HTML blocks if safe-mode is 'replace'.", None),

class MarkdownFilter(DexyFilter):
    """
    Runs a Markdown processor to convert markdown to HTML.

    Markdown extensions can be enabled in your config:
    http://packages.python.org/Markdown/extensions/index.html
    """
    aliases = ['markdown']
    _settings = {
            'examples' : ['markdown'],
            'input-extensions' : ['.*'],
            'output-extensions' : ['.html'],
            'extensions' : ("Which Markdown extensions to enable.", { 'toc' : {} }),
            }

    def capture_markdown_logger(self):
        markdown_logger = logging.getLogger('MARKDOWN')
        markdown_logger.addHandler(self.doc.wrapper.log.handlers[-1])

    def initialize_markdown(self):
        extension_configs = self.setting('extensions')
        extensions = extension_configs.keys()

        dbg = "Initializing Markdown with extensions: %s and extension configs: %s"
        self.log_debug(dbg % (json.dumps(extensions), json.dumps(extension_configs)))

        try:
            md = markdown.Markdown(
                    extensions=extensions,
                    extension_configs=extension_configs)
        except ValueError as e:
            self.log_debug(e.message)
            if "markdown.Extension" in e.message:
                raise dexy.exceptions.UserFeedback("There's a problem with the markdown extensions you specified.")
            else:
                raise
        except KeyError as e:
            raise dexy.exceptions.UserFeedback("Couldn't find a markdown extension option matching '%s'" % e.message)

        return md

    def process_text(self, input_text):
        self.capture_markdown_logger()
        md = self.initialize_markdown()
        return md.convert(input_text)

class MarkdownSlidesFilter(MarkdownFilter):
    """
    Converts paragraphs to HTML and wrap each slide in a header and footer.
    """
    aliases = ['slides']

    _settings = {
            'extensions' : { 'nl2br' : {} },
            'added-in-version': "0.9.9.6",
            'examples' : ['slides'],
            'split' : (
                "String to use to split slides.",
                "\n\n\n" # e.g. 2 blank lines.
                ),
            'slide-header' : (
                "Content to prepend to start of each slide.",
                """<section class="slide">"""
                ),
            'slide-footer' : (
                "Content to append to end of each slide.",
                """</section>"""
                ),
            }

    def process_text(self, input_text):
        self.capture_markdown_logger()
        md = self.initialize_markdown()

        slides = ""
        for counter, slide in enumerate(input_text.split(self.setting('split'))):
            html = md.convert(slide)

            # Variables to make available for string interpolation in header and footer.
            interp = {
                    'number' : (counter+1)
                    }

            header = self.setting('slide-header') % interp
            footer = self.setting('slide-footer')% interp

            slide_text = "\n%s\n%s\n%s\n" % (header, html, footer)
            slides += slide_text

        return slides
