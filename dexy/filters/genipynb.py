from dexy.filter import DexyFilter
import json
import re

class MarkdownJupyterFilter(DexyFilter):
    """
    Converts a Markdown script with embedded source code to an IPython
    notebook.
    """
    aliases = ['mdipynb', 'mdjup']
    _settings = {
            "input-extensions" : [".md"],
            "output-extensions" : [".ipynb"],
            "output" : True,
            "nbformat" : ("Setting to use for IPython nbformat setting", 3),
            "nbformat_minor" : ("Setting to use for IPython nbformat_minor setting.", 0),
            "name" : ("Name of notebook.", None),
            "pprint"  : ("Whether to pretty print JSON.", True),
            "language" : ("Default programming language for code blocks.", "python"),
            "collapsed" : ("Whether to collapse code blocks by default.", False),
            'extensions' : ("Which Markdown extensions to enable.", {})
            }
    
    def code_cell(self, source, language, metadata=None):
        if language is None:
            raise Exception("no language specified")
        return {
                "cell_type" : "code",
                "collapsed" : self.setting('collapsed'),
                "metadata" : metadata or {},
                "language" : language,
                "input" : source,
                "outputs" : [],
                "prompt_number" : None
                }

    def heading_cell(self, level, text, metadata = None):
        return {
                "cell_type" : "heading",
                "level" : level,
                "metadata" : metadata or {},
                "source" : [text]
                }

    def markdown_cell(self, source):
        return {
                "cell_type" : "markdown",
                "metadata" : {},
                "source" : [
                    "\n".join(source)
                    ]
                }

    def process_text(self, input_text):
        cells = []
        proseblock = []
        codeblock = None
        language = None
        state = "md"
        workbook_name = self.setting("name")

        for line in input_text.splitlines():
            print state, line
            if state == "md" and line.lstrip().startswith("```"):
                # save exististing prose block, if any
                if proseblock:
                    cell = self.markdown_cell(proseblock)
                    cells.append(cell)
                    proseblock = []

                # start new code block, skipping current line
                state = "code"

                # Detect lexer, if specified
                match_lexer = re.match("```([A-Za-z-]+)", line)
                if match_lexer:
                    language = match_lexer.groups()[0]
                else:
                    language = self.setting('language')

                codeblock = []
            elif state == "code" and line.lstrip().startswith("```"):
                cell = self.code_cell(codeblock, language)
                cells.append(cell)

                state = "md"
            elif state == "code":
                codeblock.append(line)
            elif state == "md":
                m = re.match("^(#+)(\s*)(.*)$", line)
                if m:
                    if proseblock:
                        cell = self.markdown_cell(proseblock)
                        cells.append(cell)
                        proseblock = []

                    level = len(m.groups()[0])
                    cell = self.heading_cell(level, m.groups()[2])
                    cells.append(cell)
                else:
                    proseblock.append(line)

        notebook = {
            "nbformat" : self.setting('nbformat'),
            "nbformat_minor" : self.setting('nbformat-minor'),
            "metadata" : {
                "name" : workbook_name
                },
            "worksheets" : [{
                "cells" : cells
                }]
            }

        if self.setting('pprint'):
            return json.dumps(notebook, indent=4, sort_keys=True)
        else:
            return json.dumps(notebook)
