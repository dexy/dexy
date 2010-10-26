from dexy.handler import DexyHandler
import shutil

class CopyHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['cp']
    
    # Just copy the file without trying to read the contents.
    def process(self):
        self.artifact.auto_write_artifact = False
        shutil.copyfile(self.doc.name, self.artifact.filename())

class FooterHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['ft', 'footer']

    def process_text(self, input_text):
        self.artifact.load_input_artifacts()
        footer_key = "_footer%s|jinja" % self.artifact.ext
        footer_keys = [k for k in self.artifact.input_artifacts_dict.keys() if k.find(footer_key) > 0]
        if len(footer_keys) > 0:
            footer_key = footer_keys[0]
            footer_text = self.artifact.input_artifacts_dict[footer_key]['data']
        else:
            raise Exception("No file matching %s was found to work as a footer." % footer_key)
                            
        return "%s\n%s" % (footer_text, input_text)

class HeaderHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['hd', 'header']

    def process_text(self, input_text):
        self.artifact.load_input_artifacts()
        header_key = "_header%s|jinja" % self.artifact.ext
        header_keys = [k for k in self.artifact.input_artifacts_dict.keys() if k.find(header_key) > 0]
        if len(header_keys) > 0:
            header_key = header_keys[0]
            header_text = self.artifact.input_artifacts_dict[header_key]['data']
        else:
            raise Exception("No file matchine %s was found to work as a header." % header_key)
                            
        return "%s\n%s" % (header_text, input_text)


class HeadHandler(DexyHandler):
    ALIASES = ['head']
    def process_text(self, input_text):
        return "\n".join(input_text.split("\n")[0:10]) + "\n"

