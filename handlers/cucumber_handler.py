from dexy.handler import DexyHandler
from dexy.utils import ansi_output_to_html

import pexpect

class CucumberHandler(DexyHandler):
    INPUT_EXTENSIONS = [".feature"]
    OUTPUT_EXTENSIONS = [".html", ".txt"]
    ALIASES = ["cuke"]

    def process(self):
        self.artifact.load_input_artifacts()
        keys = self.artifact.input_artifacts_dict.keys() 
        rb_file = self.artifact.doc.name.replace(".feature", ".rb")
        matches = [k for k in keys if rb_file.find(k)]
        
        if len(matches) == 0:
            err_msg = "no file matching %s was found in %s" % (rb_file, keys)
            raise Exception(err_msg)
        if len(matches) > 1:
            err_msg = "too many files matching %s were found in %s: %s" % (rb_file, keys, matches)
            raise Exception(err_msg)
        
        key = matches[0]
        rf = self.artifact.input_artifacts_dict[key]['fn']

        self.artifact.generate_workfile()
        wf = self.artifact.work_filename()
        # TODO should chdir to artifacts?
        command = "/usr/bin/env cucumber -r artifacts/%s %s" % (rf, wf)
        self.log.debug(command)
        output = pexpect.run(command)
        # TODO detect output extension and convert appropriately
        html = ansi_output_to_html(output)
        self.artifact.data_dict['1'] = html

