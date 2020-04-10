from dexy.filter import DexyFilter
import base64
import dexy.exceptions
import json
import urllib

try:
    import nbformat
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class IPythonBase(DexyFilter):
    """
    Base class for IPython filters which work by loading notebooks into memory.
    """
    aliases = []

    def is_active(self):
        return AVAILABLE

    def load_notebook(self):
        nb = None
        with open(self.input_data.storage.data_file(), "r") as f:
            nb = nbformat.read(f, as_version=4)
        return nb

    def enumerate_cells(self, nb=None):
        if not nb:
            nb = self.load_notebook()
        for j, cell in enumerate(nb.cells):
            yield(j, cell)

class IPythonExport(IPythonBase):
    """
    Generates a static file based on an IPython notebook.
    """
    aliases = ['ipynbx']

    _settings = {
            'added-in-version' : "0.9.9.6",
            'input-extensions' : ['.ipynb'],
            'output' : True,
            'output-extensions' : ['.md', '.html'], # TODO add other formats
            }

    def process_html(self):
        self.load_notebook()

    def process_md(self):
        output = ""
        for j, cell in self.enumerate_cells():
            cell_type = cell['cell_type']
            if cell_type == 'heading':
                output += "## %s\n" % cell['source']
            elif cell_type == 'markdown':
                output += "\n%s\n" % cell['source']
            elif cell_type == 'code':
                for k, cell_output in enumerate(cell['outputs']):
                    cell_output_type = cell_output['output_type']
                    del cell_output['output_type']
                    if cell_output_type == 'stream':
                        output += cell_output['text']
                    elif cell_output_type in ('pyout', 'pyerr',):
                        pass
                    elif cell_output_type == 'display_data':
                        for fmt, contents in cell_output.items():
                            if fmt == "png":
                                cell_output_image_file = "cell-%s-output-%s.%s" % (j, k, fmt)
                                self.add_doc(cell_output_image_file, base64.decodestring(contents))
                                output += "\n![Description](%s)\n" % urllib.quote(cell_output_image_file)
                            elif fmt in ('metadata','text',):
                                pass
                            else:
                                raise dexy.exceptions.InternalDexyProblem(fmt)
                    else:
                        raise dexy.exceptions.InternalDexyProblem("unexpected cell output type %s" % cell_output_type)
            else:
                raise dexy.exceptions.InternalDexyProblem("Unexpected cell type %s" % cell_type)

        return output

    def process(self):
        if self.ext == '.html':
            output = self.process_html()
        elif self.ext == '.md':
            output = self.process_md()
        else:
            raise dexy.exceptions.InternalDexyProblem("Shouldn't get ext %s" % self.ext)

        self.output_data.set_data(output)

class IPythonNotebook(IPythonBase):
    """
    Get data out of an IPython notebook.
    """
    aliases = ['ipynb']

    _settings = {
            'added-in-version' : "0.9.9.6",
            'examples' : ['ipynb'],
            'input-extensions' : ['.ipynb', '.json', '.py'],
            'output-extensions' : ['.json'],
            }

    def process(self):
        output = {}
        nb = self.load_notebook()

        nb_fmt_string = "%s.%s" % (nb['nbformat'], nb['nbformat_minor']) # 3.0 currently
        output['nbformat'] = nb_fmt_string

        cells = []
        documents = []

        for j, cell in self.enumerate_cells(nb):
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

                d = self.add_doc("%s-input%s" % (cell_key, ext), cell['input'], {'output': False })
                documents.append(d.key)

                # Add pygments syntax highlighting in HTML and LaTeX formats.
                self.add_doc("%s-input%s|pyg|h" % (cell_key, ext), cell['input'], { 'output' : False })
                self.add_doc("%s-input%s|pyg|l" % (cell_key, ext), cell['input'], { 'output' : False })

                # process each output
                for k, cell_output in enumerate(cell['outputs']):
                    cell_output_type = cell_output['output_type']
                    del cell_output['output_type']

                    if cell_output_type == 'stream':
                        assert sorted(cell_output.keys()) == ["stream", "text"], "stream output keys"
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
                        for fmt, contents in cell_output.items():
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
        for k, v in nb['metadata'].items():
            output[k] = v

        self.output_data.set_data(json.dumps(output))
