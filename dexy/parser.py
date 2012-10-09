from dexy.plugin import PluginMeta
from dexy.utils import parse_yaml
import dexy.exceptions
import dexy.doc
import inspect
import json
import re

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

    def parse(self, input_text):
        config = parse_yaml(input_text)
        print "raw config", config

        def parse_key_mapping(mapping):
            docs = []
            for k, v in mapping.iteritems():
                # k is a document key
                # v is a sequence of children or kwargs
                children = []
                kwargs = {}
                for element in v:
                    if hasattr(element, 'keys'):
                        assert len(element) == 1, "WTF why does '%s' have len > 1?!" % element
                        for kk, vv in element.iteritems():
                            if isinstance(vv, list):
                                # This is a sequence, probably a child doc but
                                # if starts with 'args' then is nested complex
                                # keyword args.
                                if kk == "args":
                                    kwargs.update(vv[0])

                                else:
                                    children.append(*parse_key_mapping(element))

                            else:
                                # This is a key:value argument
                                kwargs.update(element)

                    else:
                        # This is a child doc with no args
                        assert isinstance(element, basestring), "WTF why isn't '%s' a string?!" % element
                        children.append(parse_single_key(element))

                docs.append(parse_single_key(k, *children, **kwargs))

            return docs

        def parse_single_key(key, *children, **kwargs):
            task_class, pattern = dexy.task.Task.task_class_from_arg(key)
            qual_arg = "%s:%s" % (task_class.__name__, pattern)
            if qual_arg in self.wrapper.tasks.keys():
                return self.wrapper.tasks[qual_arg]
            else:
                return dexy.task.Task.create_from_arg(key, *children, wrapper=self.wrapper, **kwargs)

        def parse_keys(data):
            # The next thing we parse must be a single key or a mapping
            # with one or more keys
            if hasattr(data, 'keys'):
                return parse_key_mapping(data)
            elif isinstance(data, basestring):
                return parse_single_key(data)
            elif isinstance(data, list):
                docs = []
                for element in data:
                    docs.append(*parse_keys(element))
                return docs
            else:
                raise Exception("invalid input %s" % data)

        keys = parse_keys(config)

        if isinstance(keys, dexy.task.Task):
            return [keys]
        else:
            return keys

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
