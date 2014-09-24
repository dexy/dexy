from dexy.filter import DexyFilter
import json
import re

class MarkdownSections(DexyFilter):
    """
    Base class for filters which divide markdown scripts into code/prose
    sections.
    """

    aliases = ['mdsections']
    _settings = {
            "input-extensions" : [".md"],
            "output-extensions" : [".json"],
            "output" : True,
            "language" : ("Default programming language for code blocks.", "python"),
            "pprint"  : ("Whether to pretty print JSON.", True),
            }


    def process_code(self, source, language, metadata=None):
        return {
                "type" : "source",
                "language" : language,
                "source" : source,
                "metadata" : metadata
                }

    def process_heading(self, level, text, metadata=None):
        return {
                "type" : "heading",
                "level" : level,
                "text" : text,
                "metadata" : metadata
                }

    def process_prose(self, source, metadata=None):
        return {
                "type" : "markdown",
                "text" : source,
                "metadata" : metadata
                }

    def process_sections(self, input_text):
        blocks = []

        proseblock = []
        codeblock = None

        language = None
        state = "md"

        for line in input_text.splitlines():
            if state == "md" and line.lstrip().startswith("```"):
                # save exististing prose block, if any
                if proseblock:
                    block = self.process_prose(proseblock)
                    blocks.append(block)
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
                block = self.process_code(codeblock, language)
                blocks.append(block)

                state = "md"
            elif state == "code":
                codeblock.append(line)
            elif state == "md":
                m = re.match("^(#+)(\s*)(.*)$", line)
                if m:
                    if proseblock:
                        block = self.process_prose(proseblock)
                        blocks.append(block)
                        proseblock = []

                    level = len(m.groups()[0])
                    block = self.process_heading(level, m.groups()[2])
                    blocks.append(block)
                else:
                    proseblock.append(line)

        return blocks
        
    def process_text(self, input_text):
        blocks = self.process_sections(input_text)

        if self.setting('pprint'):
            return json.dumps(blocks, indent=4, sort_keys=True)
        else:
            return json.dumps(blocks)


class MarkdownJupyter(MarkdownSections):
    """
    Generate a Jupyter (IPython) notebook from markdown with embedded code.
    """
    aliases = ['mdipynb', 'mdjup']
    _settings = {
            "output-extensions" : [".ipynb"],
            "nbformat" : ("Setting to use for IPython nbformat setting", 3),
            "nbformat_minor" : ("Setting to use for IPython nbformat_minor setting.", 0),
            "name" : ("Name of notebook.", None),
            "collapsed" : ("Whether to collapse code blocks by default.", False),
            }
    
    def process_code(self, source, language, metadata=None):
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

    def process_heading(self, level, text, metadata = None):
        return {
                "cell_type" : "heading",
                "level" : level,
                "metadata" : metadata or {},
                "source" : [text]
                }

    def process_prose(self, source):
        return {
                "cell_type" : "markdown",
                "metadata" : {},
                "source" : [
                    "\n".join(source)
                    ]
                }

    def process_text(self, input_text):
        workbook_name = self.setting("name")
        cells = self.process_sections(input_text)

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
