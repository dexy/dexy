from dexy.filters.process import SubprocessExtToFormatFilter
import os

class Asciidoctor(SubprocessExtToFormatFilter):
    """
    Uses asciidoctor command line tool to convert asciidoc input to output formats.
    """
    aliases = ['asciidoctor']
    _settings = {
            'tags' : ['asciidoc', 'html'],
            'output' : True,
            'version-command' : "asciidoctor --version",
            'executable' : 'asciidoctor',
            'input-extensions' : ['.*'],
            'output-extensions': ['.html', '.xml', '.tex'],
            'stylesheet' : ("Custom asciidoctor stylesheet to use.", None),
            'format-specifier': '-b ',
            'ext-to-format' : {
                '.html' : 'html5',
                '.xml': 'docbook45',
                '.tex' : 'latex'
                },
            'command-string': '%(prog)s %(format)s %(args)s %(ss)s -o %(output_file)s %(script_file)s'
            }

    def command_string_args(self):
        args = super(Asciidoctor, self).command_string_args()

        stylesheet = self.setting('stylesheet')
        if stylesheet:
            stylesdir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'asciidoctor'))
            args['ss'] = "-a stylesheet=%s -a stylesdir=%s" % (stylesheet, stylesdir)
        else:
            args['ss'] = ''
        return args
