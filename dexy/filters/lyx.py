from dexy.filter import DexyFilter

class LyxJinjaFilter(DexyFilter):
    """
    Filter which converts dexy:foo.txt|bar into << d['foo.txt|bar'] >> so you
    can compose documents with lyx and process them in dexy. This expects you
    to do doc.lyx|lyx|lyxjinja|jinja|latex
    """
    aliases = ['lyxjinja']
    _settings = {
            'input-extensions' : ['.tex'],
            'output-extensions' : ['.tex'],
            }

    def process_text(self, input_text):
        lines = []
        for line in input_text.splitlines():
            if line.startswith("dexy:"):
                _, clean_line = line.split("dexy:")
                if ":" in clean_line:
                    doc, section = clean_line.split(":")
                    lines.append("<< d['%s']['%s'] >>" % (doc, section,))
                else:
                    lines.append("<< d['%s'] >>" % clean_line)
            else:
                lines.append(line)
        return "\n".join(lines)
