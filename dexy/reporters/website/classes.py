from datetime import datetime
from dexy.filters.templating_plugins import TemplatePlugin
from dexy.reporters.output import OutputReporter
from dexy.utils import iter_paths
from dexy.utils import reverse_iter_paths
from jinja2 import Environment
from jinja2 import FileSystemLoader
import dexy.exceptions
import jinja2
import operator
import os

class Navigation(object):
    def __init__(self):
        # Lookup table for first pass of gathering info.
        self.lookup_table = {}

        self.nodes = {}
        self.root = None

    def populate_lookup_table(self, docs):
        for doc in docs:
            if doc.is_canonical_output():
                parent_dir = "/" + os.path.dirname(doc.name)
                if not self.lookup_table.has_key(parent_dir):
                    self.lookup_table[parent_dir] = {'docs' : []}
    
                self.lookup_table[parent_dir]['docs'].append(doc)

            if doc.is_index_page():
                self.lookup_table[parent_dir]['index-page'] = doc

    def walk(self):
        """
        Build nodes dict from already-populated lookup table.
        """
        for path, info in self.lookup_table.iteritems():
            parent = None
            ancestors = []
            level = 0
            for parent_path in iter_paths(path):
                if not self.nodes.has_key(parent_path):
                    node = Node(parent_path, parent, [])
                    node.level = level
                    self.nodes[parent_path] = node
                    if parent:
                        parent.children.append(node)

                    if not self.root and parent_path == '/':
                        self.root = node

                parent = self.nodes[parent_path]
                ancestors.append(parent)
                level += 1

            assert parent.location == path
            parent.ancestors = ancestors
            parent.docs = info['docs']
            if info.has_key('index-page'):
                parent.index_page = info['index-page']

    def debug(self):
        """
        Returns a dump of useful information.
        """
        info = []
        for path, node in self.nodes.iteritems():
            info.append('')
            info.append(path)

            if node.index_page:
                info.append("index-page:")
                info.append(node.index_page.key_with_class())
                info.append('')

            info.append("docs:")
            for child in node.docs:
                info.append(child.key_with_class())
            info.append('')

            info.append("children:")
            for child in node.children:
                info.append(child.location)
            info.append('')
        return "\n".join(info)

class Node(object):
    """
    Wrapper class for a location in the site hierarchy.
    """
    def __init__(self, location, parent, children):
        if parent:
            assert isinstance(parent, Node)
        if children:
            assert isinstance(children[0], Node)
        self.location = location
        self.parent = parent
        self.children = children
        self.ancestors = []
        self.docs = []
        self.index_page = None

    def __repr__(self):
        return "Node(%s)" % self.location

    def has_children_with_index_pages(self):
        return any(node.index_page for node in self.children)

    def breadcrumbs(self, divider = " &gt; "):
        return divider.join("""<a href="%s">%s</a>""" % (node.location, node.index_page.title()) for node in self.ancestors if node.index_page)

class WebsiteReporter(OutputReporter):
    """
    Applies a template to create a website from your dexy output.

    Templates are applied to all files with .html extension which don't already
    contain "<head" or "<body" tags.
    """
    ALIASES = ['ws']
    _SETTINGS = {
            "dir" : "output-site",
            "default-template" : ("Path to the default template to apply.", "_template.html"),
            "plugins" : (
                    "List of TemplatingPlugins to make available in environment.",
                    ["inflection", "builtins"]
                ),
            "default" : False
            }

    def apply_and_render_template(self, doc):
        # Figure out which template to use.
        ws_template = doc.arg_value('ws-template')
        if ws_template and not isinstance(ws_template, bool):
            template_file = ws_template
        else:
            template_file = self.setting('default-template')

        # Look for a file named template_file in nearest parent dir to document.
        template_path = None
        for subpath in reverse_iter_paths(doc.output().name):
            template_path = os.path.join(subpath, template_file)
            if os.path.exists(template_path):
                break

        if not template_path:
            raise dexy.exceptions.UserFeedback("no template path for %s" % doc.key)
        else:
            self.log.debug("  using template %s for %s" % (template_path, doc.key))

        # Populate template environment
        env = Environment(undefined=jinja2.StrictUndefined)

        dirs = [".", os.path.dirname(__file__), os.path.dirname(template_path)]
        env.loader = FileSystemLoader(dirs)

        self.log.debug("  loading template at %s" % template_path)
        template = env.get_template(template_path)

        if doc.output().ext == '.html':
            content = unicode(doc.output())
        else:
            content = doc.output()
            
        current_dir = doc.output().parent_dir()
        parent_dir = os.path.split(current_dir)[0]

        env_data = {}

        for alias in self.setting('plugins'):
            plugin = TemplatePlugin.create_instance(alias)
            env_data.update(plugin.run())

        navigation = {
                }

        env_data.update({
                'attrgetter' : operator.attrgetter,
                'itemgetter' : operator.itemgetter,
                'content' : content,
                'locals' : locals,
                'navigation' : navigation,
                'nav' : self._navobj.nodes["/%s" % current_dir],
                'root' : self._navobj.nodes["/"],
                'navobj' : self._navobj,
                'page_title' : doc.title(),
                'parent_dir' : parent_dir,
                'current_dir' : current_dir,
                'source' : doc.name,
                'template_source' : template_path,
                'wrapper' : self.wrapper,
                'year' : datetime.now().year
                })

        env_data.update(self.wrapper.parse_globals())

        fp = os.path.join(self.setting('dir'), doc.output().name).replace(".json", ".html")

        parent_dir = os.path.dirname(fp)
        if not os.path.exists(parent_dir):
            os.makedirs(os.path.dirname(fp))

        self.log.debug("  writing to %s" % (fp))
        template.stream(env_data).dump(fp, encoding="utf-8")

    def run(self, wrapper):
        self.wrapper=wrapper
        self.set_log()
        self.keys_to_outfiles = []

        self._navobj = Navigation()
        self._navobj.populate_lookup_table(self.wrapper.batch.docs())
        self._navobj.walk()

        self.create_reports_dir()

        for doc in wrapper.batch.docs():
            self.log.debug("processing doc %s" % doc.key_with_class())
            if doc.is_canonical_output():
                if doc.final_artifact.ext == ".html":
                    fragments = ('<html', '<body', '<head')
                    has_html_header = any(html_fragment in unicode(doc.output()) for html_fragment in fragments)

                    if has_html_header and not doc.arg_value('ws-template'):
                        self.log.debug("  found html tag in output of %s" % doc.key)
                        self.write_canonical_doc(doc)
                    else:
                        self.apply_and_render_template(doc)
                elif doc.final_artifact.ext == '.json' and 'htmlsections' in doc.filters:
                    self.apply_and_render_template(doc)
                else:
                    self.write_canonical_doc(doc)

        self.log.debug("finished")
