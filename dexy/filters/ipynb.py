from dexy.filter import DexyFilter
import base64
import json

try:
    import IPython.nbformat.current
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class IPythonNotebook(DexyFilter):
    """
    Get data out of an IPython notebook.
    """
    aliases = ['ipynb']

    _settings = {
            'input-extensions' : ['.ipynb', '.json', '.py'],
            'output-extensions' : ['.json'],
            }

    def is_active(self):
        return AVAILABLE

    def process(self):
        output = {}
        nb = None

        # load the notebook into memory
        with open(self.input_data.storage.data_file(), "r") as f:
            nb_fmt = self.input_data.ext.replace(".","")
            nb = IPython.nbformat.current.read(f, nb_fmt)

        nb_fmt_string = "%s.%s" % (nb['nbformat'], nb['nbformat_minor']) # 3.0 currently
        output['nbformat'] = nb_fmt_string

        worksheet = nb['worksheets'][0]

        cells = []
        documents = []

        for j, cell in enumerate(worksheet['cells']):
            # could also do: cell_key = "%s--%0.3d" % (self.input_data.rootname(), j)
            cell_key = "%s--%s" % (self.input_data.rootname(), j)
            cell_type = cell['cell_type']

            if cell_type == 'heading':
                # TODO implement
                # keys are [u'source', u'cell_type', u'level', u'metadata']
                pass

            elif cell_type == 'markdown':
                d = self.add_doc("%s.md" % cell_key, cell['source'], {'output':False})
                documents.append(d.key)
                d = self.add_doc("%s.md|pyg|h" % cell_key, cell['source'])
                d = self.add_doc("%s.md|pyg|l" % cell_key, cell['source'])

            elif cell_type == 'code':
                # keys are [u'cell_type', u'language', u'outputs', u'collapsed', u'prompt_number', u'input', u'metadata']

                # map languages to file extensions to create new doc(s) for each cell
                file_extensions = {
                    'python' : '.py'
                    }
                ext = file_extensions[cell['language']]

                d = self.add_doc("%s-input%s" % (cell_key, ext), cell['input'], {'output':False})
                documents.append(d.key)

                # Add pygments syntax highlighting in HTML and LaTeX formats.
                self.add_doc("%s-input%s|pyg|h" % (cell_key, ext), cell['input'])
                self.add_doc("%s-input%s|pyg|l" % (cell_key, ext), cell['input'])

                # process each output
                for k, cell_output in enumerate(cell['outputs']):
                    cell_output_type = cell_output['output_type']
                    del cell_output['output_type']

                    if cell_output_type == 'stream':
                        assert sorted(cell_output.keys()) == [u"stream", u"text"], "stream output keys"
                        d = self.add_doc(
                                "%s-output-%s.txt" % (cell_key, k),
                                cell_output['text'],
                                {'output' : False}
                                )
                        documents.append(d.key)

                    elif cell_output_type == 'pyout':
                        pass

                    elif cell_output_type == 'pyerr':
                        pass

                    elif cell_output_type == 'display_data':
                        for fmt, contents in cell_output.iteritems():
                            if fmt == "png":
                                d = self.add_doc(
                                        "%s-output-%s.%s" % (cell_key, k, fmt),
                                        base64.decodestring(contents)
                                        )
                                documents.append(d.key)
                                cell.outputs[k]['png'] = d.key
                            elif fmt == 'text':
                                pass
                            elif fmt == 'metadata':
                                pass
                            elif fmt == 'latex':
                                pass

                            else:
                                raise Exception("unexpected format in display_data %s" % fmt)

                    else:
                        raise Exception("unexpected output type %s" % cell_output_type)
            else:
                raise Exception("unexpected cell type '%s'" % cell_type)

            cells.append((cell_type, cell,))

        output["nbformat"] = nb_fmt_string
        output["cells"] = cells
        output["documents"] = documents
        for k, v in nb['metadata'].iteritems():
            output[k] = v

        self.output_data.set_data(json.dumps(output))
