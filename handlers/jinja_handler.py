from dexy.handler import DexyHandler
from jinja2 import Environment
from ordereddict import OrderedDict
import jinja2
import json
import os
import re
import uuid

class FilenameHandler(DexyHandler):
    """Generate random filenames to track provenance of data."""
    ALIASES = ['fn']
    def process_text(self, input_text):
        datafiles = {}
        for k, a in self.artifact.inputs().items():
            if k.endswith("|dexy"):
                datafiles[a.canonical_filename()] = a

        # TODO this should not match more than two dashes
        for m in re.finditer("dexy--(\S+)\.([a-z]+)", input_text):
            key = m.groups()[0]
            ext = m.groups()[1]
            key_with_ext = "%s.%s" % (key, ext)

            if key_with_ext in self.artifact.inputs().keys():
                artifact = self.artifact.inputs()[key_with_ext]
                self.log.debug("existing key %s in artifact %s links to file %s" %
                          (key, self.artifact.key, artifact.filename()))
            elif key_with_ext in datafiles.keys():
                artifact = datafiles[key_with_ext]
            else:
                artifact = self.artifact.__class__(key_with_ext)
                artifact.ext = ".%s" % ext
                artifact.final = True
                artifact.additional = True
                artifact.set_binary_from_ext()
                artifact.artifacts_dir = self.artifact.artifacts_dir

                artifact.hashstring = str(uuid.uuid4())
                self.artifact.add_input(key_with_ext, artifact)
                self.artifact.save()
                self.log.debug("added key %s to artifact %s ; links to file %s" %
                          (key, self.artifact.key, artifact.filename()))

            input_text = input_text.replace(m.group(), artifact.filename())

        # Hack to replace __ with -- in case we want to document how to use this
        # filter, we can't use -- because this will be acted upon.
        for m in re.finditer("dexy__(.+)\.([a-z]+)", input_text):
            key = m.groups()[0]
            ext = m.groups()[1]
            replacement_key = "dexy--%s.%s" % (key, ext)
            input_text = input_text.replace(m.group(), replacement_key)

        return input_text


class JinjaHandler(DexyHandler):
    """
    Runs the Jinja templating engine on your document to incorporate dynamic
    content.
    """
    ALIASES = ['jinja']
    FINAL = True

    def process_text(self, input_text):
        document_data = {}
        raw_data = {}

        notextile = self.artifact.args.has_key('notextile') and self.artifact.args['notextile']

        for key, artifact in self.artifact.inputs().items():
            if artifact.is_cached():
                artifact.load() # reload

            # Full path keys
            keys = [key, artifact.canonical_filename()]

            # Shortcut keys if in common directory
            if os.path.dirname(self.doc.name) == os.path.dirname(key) or not os.path.dirname(key):
                keys.append(os.path.basename(key))
                fn = artifact.canonical_filename()
                keys.append(os.path.basename(fn))
                keys.append(os.path.splitext(fn)[0]) # TODO deal with collisions

            # Do special handling of data
            if artifact.ext == '.json':
                path_to_file = os.path.join(self.artifact.artifacts_dir, artifact.filename())
                # TODO read this from memory rather than loading from file?
                unsorted_json = json.load(open(path_to_file), "r")

                def sort_dict(d):
                    od = OrderedDict()
                    for k in sorted(d.keys()):
                        v = d[k]
                        if isinstance(v, dict) or isinstance(v, OrderedDict):
                            od[k] = sort_dict(v)
                        else:
                            if notextile and "<span" in v and not "<notextile>" in v:
                                od[k] = "<notextile>\n%s\n</notextile>" % v
                            else:
                                od[k] = v
                    return od

                data = sort_dict(unsorted_json)

            elif notextile and artifact.ext == '.html':
                data = OrderedDict()
                for s, h in artifact.data_dict.items():
                    if "<notextile>" in h:
                        data[s] = h
                    else:
                        data[s] = "<notextile>\n%s\n</notextile>" % h
            else:
                data = artifact.data_dict

            for k in keys:
                raw_data[k] = artifact.output_text()
                if data.keys() == ['1']:
                    document_data[k] = data['1']
                else:
                    document_data[k] = data

        if self.artifact.ext == ".tex":
            self.log.debug("changing jinja tags to << >> etc. for %s" % self.artifact.key)
            env = Environment(
                block_start_string = '<%',
                block_end_string = '%>',
                variable_start_string = '<<',
                variable_end_string = '>>',
                comment_start_string = '<#',
                comment_end_string = '#>'
                )
        else:
            env = Environment()

        template_hash = {
            'a' : self.artifact._inputs,
            'd' : document_data,
            'dk' : sorted(document_data.keys()),
            'r' : raw_data
        }

        try:
            template = env.from_string(input_text)
            result = str(template.render(template_hash))
        except jinja2.exceptions.TemplateSyntaxError as e:
            print "jinja error occurred processing line", e.lineno
            raise e
        except Exception as e:
            print e.__class__.__name__
            raise e

        return result
