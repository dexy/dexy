from dexy.exceptions import InternalDexyProblem
from dexy.exceptions import UserFeedback
from dexy.filters.process import SubprocessExtToFormatFilter
from dexy.filters.process import SubprocessFilter
import os

class AsciidoctorFOPDF(SubprocessFilter):
    """
    Uses asciidoctor-fopdf to generate PDF.
    """
    aliases = ['fopdf']

    _settings = {
            'fopdf-dir' : ("Absolute path on file system to asciidoctor-fopdf dir.", None)
            }

    def process(self):
        # make copy of fopdf-dir (use hardlinks?)
        # copy working files including dependencies
        # run fopdf
        # copy generated PDF
        pass

class Asciidoctor(SubprocessExtToFormatFilter):
    """
    Runs `asciidoctor`.
    """
    aliases = ['asciidoctor']
    _settings = {
            'tags' : ['asciidoc', 'html'],
            'examples' : ['asciidoctor'],
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

            if not os.path.exists(stylesdir):
                msg = "Asciidoctor stylesheet directory not found at '%s'"
                raise InternalDexyProblem(msg % stylesdir)

            args['ss'] = "-a stylesheet=%s -a stylesdir=%s" % (stylesheet, stylesdir)

            if not os.path.exists(os.path.join(stylesdir, stylesheet)):
                msg = "No stylesheet file named '%s' was found in directory '%s'. Files found: %s"
                stylesheets = os.listdir(stylesdir)
                raise UserFeedback(msg % (stylesheet, stylesdir, ", ".join(stylesheets)))

        else:
            args['ss'] = ''
        return args
