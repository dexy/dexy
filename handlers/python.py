from dexy.handler import DexyHandler

class WebsiteHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['ws']

    def process_text(self, input_text):
        self.artifact.load_input_artifacts()
        
        header_keys = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith("_header.html|jinja")]
        if len(header_keys) > 0:
            header_key = header_keys[0]
            header_text = self.artifact.input_artifacts_dict[header_key]['data']
        else:
            header_text = "header not found"

        footer_keys = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith("_footer.html|jinja")]
        if len(footer_keys) > 0:
            footer_key = footer_keys[0]
            footer_text = self.artifact.input_artifacts_dict[footer_key]['data']
        else:
            footer_text = "footer not found"

        return "%s %s %s" % (header_text, input_text, footer_text)


class HeadHandler(DexyHandler):
    ALIASES = ['head']
    def process_text(self, input_text):
        return "\n".join(input_text.split("\n")[0:10]) + "\n"

