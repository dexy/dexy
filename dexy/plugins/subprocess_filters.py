from dexy.plugins.process_filters import SubprocessFilter
import os

class PandocFilter(SubprocessFilter):
    EXECUTABLE = "pandoc"
    VERSION_COMMAND = "pandoc --version"
    ALIASES = ['pandoc']
    OUTPUT_EXTENSIONS = ['.html', '.txt', '.tex', '.pdf', '.rtf', '.json', '.docx']

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'script_file' : os.path.basename(self.prior().name),
            'output_file' : os.path.basename(self.result().name)
        }
        return "%(prog)s %(args)s %(script_file)s -o %(output_file)s" % args
