from dexy.filter import DexyFilter
from docutils import core
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser
from docutils.transforms import Transformer, frontmatter
from docutils.utils import new_document
import io
import dexy.exceptions
import docutils.writers
import os

def default_template(writer_name):
    """
    Set the default template correctly, in case there has been a change in working dir.
    """
    writer_class = docutils.writers.get_writer_class(writer_name)

    if os.path.isdir(writer_class.default_template_path):
        return os.path.abspath(os.path.join(writer_class.default_template_path, writer_class.default_template))
    else:
        return os.path.abspath(writer_class.default_template_path)

class RestructuredTextBase(DexyFilter):
    """ Base class for ReST filters using the docutils library.
    """
    aliases = []

    _settings = {
            "input-extensions" : [".rst", ".txt"],
            'output-extensions' : [".html", ".tex", ".xml", ".odt"],
            'output' : True,
            'writer' : ("Specify rst writer to use (not required: dexy will attempt to determine automatically from filename if not specified).", None),
            'stylesheet' : ("Stylesheet arg to pass to rst", None),
            'template' : ("Template arg to pass to rst", None),
            }

    def docutils_writer_name(self):
        if self.setting('writer'):
            return self.setting('writer')
        elif self.ext == ".html":
            return 'html'
        elif self.ext == ".tex":
            return 'latex2e'
        elif self.ext == ".xml":
            return 'docutils_xml'
        elif self.ext == ".odt":
            return 'odf_odt'
        else:
            raise Exception("unsupported extension %s" % self.ext)

class RestructuredText(RestructuredTextBase):
    """
    A 'native' ReST filter which uses the docutils library.

    Look for configuration options for writers here:
    http://docutils.sourceforge.net/docs/user/config.html
    """
    aliases = ['rst']
    skip_settings = 'settings-not-for-settings-overrides'
    _settings = {
            'allow-any-template-extension' : ("Whether to NOT raise an error if template extension does not match document extension.", False),
            skip_settings : (
                "Which of the settings should NOT be passed to settings_overrides.",
                ['writer']
                )
            }

    def process(self):
        def skip_setting(key):
            in_base_filter = key in DexyFilter._settings
            in_skip = key in self.setting(self.skip_settings) or key == self.skip_settings
            return in_base_filter or in_skip

        settings_overrides = dict((k.replace("-", "_"), v) for k, v in self.setting_values().items() if v and not skip_setting(k))
        writer_name = self.docutils_writer_name()

        warning_stream = io.StringIO()
        settings_overrides['warning_stream'] = warning_stream

        self.log_debug("settings for rst: %r" % settings_overrides)
        self.log_debug("rst writer: %s" % writer_name)

        # Check that template extension matches output.
        if 'template' in settings_overrides and not self.setting('allow-any-template-extension'):
            template = settings_overrides['template']
            template_ext = os.path.splitext(template)[1]
            if not template_ext == self.ext:
                msg = "You requested template '%s' with extension '%s' for %s, does not match document extension of '%s'"
                args = (template, template_ext, self.key, self.ext)
                raise dexy.exceptions.UserFeedback(msg % args)

        if not 'template' in settings_overrides:
            if hasattr(writer_name, 'default_template'):
                settings_overrides['template'] = default_template(writer_name)

        try:
            core.publish_file(
                    source_path = self.input_data.storage.data_file(),
                    destination_path = self.output_data.storage.data_file(),
                    writer_name=writer_name,
                    settings_overrides=settings_overrides
                    )
        except ValueError as e:
            if "Invalid placeholder in string" in e.message and 'template' in settings_overrides:
                self.log_warn("you are using template '%s'. is this correct?" % settings_overrides['template'])
            raise
        except Exception:
            self.log_warn("An error occurred while generating reStructuredText.")
            self.log_warn("source file %s" % (self.input_data.storage.data_file()))
            self.log_warn("settings for rst: %r" % settings_overrides)
            self.log_warn("rst writer: %s" % writer_name)
            raise

        self.log_debug("docutils warnings:\n%s\n" % warning_stream.getvalue())

class RstBody(RestructuredTextBase):
    """
    Returns just the body part of an ReST document.
    """
    aliases = ['rstbody']
    _settings = {
            'set-title' : ("Whether to set document title.", True),
            'output-extensions' : ['.html', '.tex']
            }

    def process_text(self, input_text):
        warning_stream = io.StringIO()
        settings_overrides = {}
        settings_overrides['warning_stream'] = warning_stream

        writer_name = self.docutils_writer_name()
        self.log_debug("about to call publish_parts with writer '%s'" % writer_name)

        if not 'template' in settings_overrides:
            settings_overrides['template'] = default_template(writer_name)

        try:
            parts = core.publish_parts(
                input_text,
                writer_name=writer_name,
                settings_overrides=settings_overrides
                )
        except AttributeError as e:
            raise dexy.exceptions.InternalDexyProblem(str(e))

        if self.setting('set-title') and ('title' in parts) and parts['title']:
            self.update_all_args({'title' : parts['title']})

        self.log_debug("docutils warnings:\n%s\n" % warning_stream.getvalue())

        return parts['body']

class RstMeta(RestructuredTextBase):
    """
    Extracts bibliographical metadata and makes this available to dexy.
    """
    aliases = ['rstmeta']
    _settings = {
            'output-extensions' : [".rst"]
            }

    def process_text(self, input_text):
        warning_stream = io.StringIO()
        settings_overrides = {}
        settings_overrides['warning_stream'] = warning_stream

        # Parse the input text using default settings
        settings = OptionParser(components=(Parser,)).get_default_values()
        parser = Parser()
        document = new_document('rstinfo', settings)
        parser.parse(input_text, document)

        # Transform the parse tree so that the bibliographic data is
        # is promoted from a mere field list to a `docinfo` node
        t = Transformer(document)
        t.add_transforms([frontmatter.DocTitle, frontmatter.DocInfo])
        t.apply_transforms()

        info = {}

        # Process individual nodes which are not part of docinfo.
        single_nodes = [
                docutils.nodes.title,
                docutils.nodes.subtitle,
                ]
        for node in single_nodes:
            for doc in document.traverse(node):
                if not len(doc.children) == 1:
                    msg = "Expected node %s to only have 1 child."
                    raise dexy.exceptions.InternalDexyProblem(msg % node)
                info[doc.tagname] = doc.children[0].astext()

        # Find the `docinfo` node and extract its children. Non-standard
        # bibliographic fields will have the `tagname` 'field' and two
        # children, the name and the value.  Standard fields simply keep
        # the name as the `tagname`.
        for doc in document.traverse(docutils.nodes.docinfo):
            for element in doc.children:
                if element.tagname == 'field':
                    name, value = element.children
                    name, value = name.astext(), value.astext()
                else:
                    name, value = element.tagname, element.astext()
                info[name] = value

        self.log_debug("found info:\n%s\n" % info)
        self.update_all_args(info)
        self.log_debug("docutils warnings:\n%s\n" % warning_stream.getvalue())

        return input_text

class RstDocParts(DexyFilter):
    """
    Returns key-value storage of document parts.
    """
    aliases = ['rstdocparts']
    _settings = {
            'input-extensions' : [".rst", ".txt"],
            'data-type' : 'keyvalue',
            'output-extensions' : ['.sqlite3', '.json'],
            'writer' : ("Specify rst writer to use.", 'html')
            }

    def process(self):
        input_text = str(self.input_data)

        warning_stream = io.StringIO()
        settings_overrides = {}
        settings_overrides['warning_stream'] = warning_stream

        writer_name = self.setting('writer')

        if not 'template' in settings_overrides:
            settings_overrides['template'] = default_template(writer_name)

        parts = core.publish_parts(
                input_text,
                writer_name=writer_name,
                settings_overrides=settings_overrides
                )

        self.log_debug("docutils warnings:\n%s\n" % warning_stream.getvalue())

        for k, v in parts.items():
            self.output_data.append(k, v)
        self.output_data.save()
