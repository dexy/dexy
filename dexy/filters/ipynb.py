from dexy.filter import DexyFilter
import dexy.exceptions
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
            'output-data-type' : 'keyvalue',
            'output-extensions' : ['.sqlite3', '.json']
            }

    def is_active(self):
        return AVAILABLE

    def process(self):
        assert self.output_data.state == 'ready'

        nb = None

        # load the notebook into memory
        with open(self.input_data.storage.data_file(), "r") as f:
            nb_fmt = self.input_data.ext.replace(".","")
            nb = IPython.nbformat.current.read(f, nb_fmt)

        nb_fmt_string = "%s.%s" % (nb['nbformat'], nb['nbformat_minor'])
        tested_notebook_formats = ('3.0',)
        worksheets = []

        try:
            # generate new dexy documents for each worksheet, and each cell in each worksheet
            for i, worksheet in enumerate(nb['worksheets']):
                worksheet_key = "%s--ws-%s" % (self.input_data.name, i)
                cells = []
                documents = []

                for j, cell in enumerate(worksheet['cells']):
                    cell_key = "%s-cell-%s" % (worksheet_key, j)
                    cells.append(cell_key)

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
                                assert sorted(cell_output.keys()) == [u"stream", u"text"]
                                d = self.add_doc(
                                        "%s-output-%s.txt" % (cell_key, k),
                                        cell_output['text'],
                                        {'output' : False}
                                        )
                                documents.append(d.key)

                            elif cell_output_type == 'pyout':
                                # [u'html', u'prompt_number', u'text']
                                # print cell_output['text'].data
                                # print cell_output['html'].data
                                pass

                            elif cell_output_type == 'display_data':
                                assert len(cell_output) == 1, cell_output.keys()
                                output_format = cell_output.keys()[0]
                                if output_format == 'png':
                                    d = self.add_doc(
                                            "%s-output-%s.%s" % (cell_key, k, output_format),
                                            cell_output[output_format]
                                            )
                                    documents.append(d.key)
                                else:
                                    raise Exception("unexpected output format %s" % output_format)
                            else:
                                raise Exception("unexpected output type %s" % cell_output_type)
                    else:
                        raise Exception("unexpected cell type '%s'" % cell_type)

                worksheets.append((worksheet_key, cells, documents,))

        except Exception as e:
            # TODO clean up and test error handling, don't capture Exception, that always ends badly.
            print "ERROR:", e
            print "error type:", type(e)

            if nb_fmt_string in tested_notebook_formats:
                raise e
            else:
                msg = "Error occurred trying to process untested IPython notebook format version %s"
                msgargs = (nb_fmt_string,)
                raise dexy.exceptions.UserFeedback(msg % msgargs)

        self.output_data.append("nbformat", nb_fmt_string)
        self.output_data.append("worksheets", json.dumps(worksheets))
        for k, v in nb['metadata'].iteritems():
            self.output_data.append(k, v)
        self.output_data.save()
