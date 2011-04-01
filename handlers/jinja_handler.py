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
        inputs = self.artifact.additional_inputs

        for k, a in self.artifact.input_artifacts.items():
            if k.endswith("|dexy"):
                datafiles[a.canonical_filename()] = a

            # collect additional inputs from all input artifacts
            for ak, av in a.additional_inputs.items():
                inputs[ak] = av

        # TODO this should not match more than two dashes
        for m in re.finditer("dexy--(.+)\.([a-z]+)", input_text):
            key = m.groups()[0]
            ext = m.groups()[1]
            key_with_ext = "%s.%s" % (key, ext)

            if key in inputs.keys():
                artifact = inputs[key]
                self.log.debug("existing key %s in artifact %s links to file %s" %
                          (key, self.artifact.key, artifact.filename()))
            elif key_with_ext in datafiles.keys():
                artifact = datafiles[key_with_ext]
            else:
                artifact = self.artifact.__class__(key_with_ext)
                artifact.ext = ".%s" % ext
                artifact.final = True
                artifact.set_binary_from_ext()
                artifact.artifacts_dir = self.artifact.artifacts_dir

                artifact.hashstring = str(uuid.uuid4())
                self.artifact.additional_inputs[key] = artifact
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


class JinjaHelper:
    def read_file(self, filename):
        f = open(filename, "r")
        return f.read()

class JinjaHandler(DexyHandler):
    """
    Runs the Jinja templating engine on your document. The primary way to
    incorporate dynamic content into your documents.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['jinja']
    FINAL = True

    def process_text(self, input_text):
        document_data = {}
        document_data['filenames'] = {}
        document_data['sections'] = {}
        document_data['a'] = {}

        # TODO move to separate 'index' handler for websites
        # create a list of subdirectories of this directory
        doc_dir = os.path.dirname(self.artifact.doc.name)
        if doc_dir == "":
            doc_dir = "."
        children = [f for f in os.listdir(doc_dir) \
                    if os.path.isdir(os.path.join(doc_dir, f))]
        document_data['children'] = sorted(children)
        document_data['json'] = OrderedDict()

        short_names = {}

        for k, a in self.artifact.input_artifacts.items():
            if a.is_cached():
                a.load() # reload
            document_data['filenames'][k] = a.filename()
            document_data['sections'][k] = a.data_dict
            document_data[k] = a.output_text()

            # Add relative paths
            common_prefix = os.path.commonprefix([self.doc.name, k])
            common_path = os.path.dirname(common_prefix)
            relpath = os.path.relpath(k, common_path)
            if not "/" in relpath:
                document_data['filenames'][relpath] = a.filename()
                document_data['sections'][relpath] = a.data_dict
                document_data[relpath] = a.output_text()

            short_names[a.canonical_filename()] = {}
            for s in a.data_dict.keys():
                short_names[a.canonical_filename()][s] = a.data_dict[s]

            if a.filename().endswith('.json'):
                self.log.debug("loading JSON for %s" % (k))
                path_to_file = os.path.join(self.artifact.artifacts_dir(), a.filename())
                unsorted_json = json.load(open(path_to_file), "r")

                def sort_dict(d):
                    od = OrderedDict()
                    for k in sorted(d.keys()):
                        v = d[k]
                        if isinstance(v, dict):
                            od[k] = sort_dict(v)
                        else:
                            od[k] = v
                    return od

                document_data['json'][k] = sort_dict(unsorted_json)

            for ak, av in a.additional_inputs.items():
                document_data['filenames'][ak] = av.filename()
                if not av.binary:
                    document_data['a'][ak] = av.output_text()
                if av.ext == '.json' and os.path.exists(av.filepath()):
                    self.log.debug("loading JSON for %s" % av.filepath())
                    document_data[ak] = json.load(open(av.filepath(), "r"))

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


        # TODO test that we are in textile or other format where this makes sense
        if re.search("latex", self.artifact.doc.key()):
            is_latex = True
        else:
            is_latex = False

        # Wrap HTML content in <notextile> tags if requested
        notextile = self.artifact.args.has_key('notextile') and self.artifact.args['notextile']
        next_handler_textile = hasattr(self.artifact, 'next_handler_name') and self.artifact.next_handler_name == 'RedclothHandler'
        if notextile and next_handler_textile:
            if document_data.has_key('nose'):
                for k, v in document_data['nose'].items():
                    document_data['nose'][k] = "\n<notextile>\n%s\n</notextile>\n" % v.rstrip()

            if document_data.has_key('source'):
                for k, d in document_data['source'].items():
                    for k2, v in document_data['source'][k].items():
                        document_data['source'][k][k2] = "\n<notextile>\n%s\n</notextile>\n" % v.rstrip()

            for k, v in document_data.items():
                if k.find("|") > 0:
                    if document_data['filenames'][k].endswith(".html") and not "<notextile>" in v:
                        document_data[k] = "\n<notextile>\n%s\n</notextile>\n" % v.rstrip()

            for k, v in short_names.items():
                # TODO does this work? Does it detect <span in dict?
                if (k.endswith(".html") or "<span" in v) and not "<notextile>" in v:
                    for s, d in v.items():
                        short_names[k][s] = "\n<notextile>\n%s\n</notextile>\n" % d.rstrip()

            for file_key, data_hash in document_data['sections'].items():
                if document_data['filenames'][file_key].endswith(".html"):
                    for k, v in data_hash.items():
                        if not "<notextile>" in v:
                            document_data['sections'][file_key][k] = "\n<notextile>\n%s\n</notextile>\n" % v.rstrip()

        document_data['filename'] = document_data['filenames']
        template_hash = {
            'd' : document_data,
            'filenames' : document_data['filenames'],
            'dk' : sorted(document_data.keys()),
            'a' : self.artifact,
            'h' : JinjaHelper(),
            's' : short_names,
            'is_latex' : is_latex
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
