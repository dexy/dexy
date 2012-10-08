from dexy.plugin import PluginMeta
import dexy.doc
import inspect
import json
import os
import re
import yaml

class Parser:
    """
    Parse various types of config file.
    """
    ALIASES = []

    __metaclass__ = PluginMeta

    @classmethod
    def is_active(klass):
        return True

    def __init__(self, wrapper=None):
        self.wrapper = wrapper

class OriginalDexyParser(Parser):
    ALIASES = [".dexy", "docs.json"]

    def parse(self, input_text):
        info = json.loads(input_text)

        tuples = [(k, v) for k, v in info.iteritems()]

        def sort_key(x):
            k, v = x

            if v.get('inputs'):
                raise Exception("have not implemented support for 'inputs' yet")

            allinputs = v.get('allinputs') and 1 or 0
            priority = v.get('priority') or 0
            return "%s:%s:%s" % (allinputs, priority, k)

        for i, t in enumerate(sorted(tuples, key=sort_key)):
            pattern, args = t

            if args.has_key('allinputs'):
                args['depends'] = args['allinputs']
                del args['allinputs']

            doc = self.wrapper.create_doc_from_arg(pattern, **args)
            doc.wrapper = self.wrapper
            doc.setup()
            self.wrapper.docs_to_run.append(doc)

class YamlFileParser(Parser):
    ALIASES = ["docs.yaml"]

    def process_pattern_yaml(self, pattern, *bundles, **args):
        if pattern.startswith("."):
            if not os.path.exists(pattern):
                pattern = "*%s" % pattern

        if (not "." in pattern) and (not ":" in pattern):
            pattern = "bundle:%s" % pattern

        return self.wrapper.create_doc_from_arg(pattern, *bundles, **args)

    def parse(self, input_text):
        try:
            data = yaml.load(input_text)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
            msg = inspect.cleandoc("""Was unable to parse the YAML in your config file.
            Here is information from the YAML parser:""")
            msg += "\n"
            msg += str(e)
            raise dexy.exceptions.UserFeedback(msg)

        refs = dict((k, self.process_pattern_yaml(k)) for k in data.keys())

        for name, directives in data.iteritems():
            # List of docs we have created in this section.
            docs = []

            # List of doc directives we will create in this sectoin.
            doc_directives = []

            # List of bundles which docs in this section depend on.
            bundles = []

            for element in directives:
                if isinstance(element, str) or isinstance(element, unicode):
                    if element in refs:
                        bundles.append(refs[element])
                    else:
                        doc_directives.append(element)
                else:
                    doc_directives.append(element)

            for directive in doc_directives:
                if isinstance(directive, dict):
                    # Create a doc with extra args.
                    assert len(directive) == 1
                    for pattern, args in directive.iteritems():
                        doc = self.process_pattern_yaml(pattern, **args)
                else:
                    # Create a doc with no special args.
                    doc = self.process_pattern_yaml(directive)

                docs.append(doc)

            # Assign our docs to our own bundle.
            bundle = refs[name]
            bundle.children.extend(bundles)
            bundle.children.extend(docs)

        for bundle in refs.values():
            if not any(bundle in b.children for b in refs.values()):
                self.wrapper.docs_to_run.append(bundle)
                bundle.wrapper = self.wrapper
                bundle.setup()

class TextFileParser(Parser):
    ALIASES = ["docs.txt"]

    def parse(self, input_text):
        for line in input_text.splitlines():
            line = line.strip()
            if not (line == "" or re.match("\s*#", line)):
                if " " in line:
                    pattern, raw_args = line.split(" ", 1)
                    try:
                        args = json.loads(raw_args)
                    except ValueError as e:
                        msg = inspect.cleandoc("""Was unable to parse the json in your config file.
                        Here is information from the json parser:""")
                        msg += "\n"
                        msg += str(e)
                        raise dexy.exceptions.UserFeedback(msg)
                else:
                    pattern = line
                    args = {}

                args['depends'] = True
                doc = self.wrapper.create_doc_from_arg(pattern, **args)
                doc.wrapper = self.wrapper
                doc.setup()
                self.wrapper.docs_to_run.append(doc)
