from dexy.filters.process import SubprocessFilter
import dexy.exceptions

class OrgModeFilter(SubprocessFilter):
    """
    Convert .org files to other formats.
    """
    aliases = ['org']
    _settings = {
            'executable' : 'emacs',
            'output' : True,
            'input-extensions' : ['.org', '.txt'],
            'output-extensions' : ['.txt', '.html', '.tex', '.pdf', '.odt'],
            'command-string' : """%(prog)s --batch %(args)s --eval "(progn \\
(find-file \\"%(script_file)s\\") \\
(%(export_command)s 1) \\
(kill-buffer) \\
)"
"""
            }

    def command_string_args(self):
        if self.ext == '.txt':
            export_command = "org-export-as-ascii"
        elif self.ext == '.html':
            export_command = "org-export-as-html"
        elif self.ext == '.tex':
            export_command = "org-export-as-latex"
        elif self.ext == '.pdf':
            export_command = "org-export-as-pdf"
        elif self.ext == '.odt':
            export_command = "org-export-as-odt"
        else:
            msg = "unsupported extension %s"
            msgargs = (self.ext)
            raise dexy.exceptions.InternalDexyProblem(msg % msgargs)

        args = self.default_command_string_args()
        args['export_command'] = export_command
        return args
