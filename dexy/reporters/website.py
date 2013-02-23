from datetime import datetime
from dexy.reporters.output import OutputReporter
from dexy.filters.templating_plugins import TemplatePlugin
from jinja2 import Environment
from jinja2 import FileSystemLoader
import dexy.exceptions
import jinja2
import os

class WebsiteReporter(OutputReporter):
    """
    Applies a template to create a website from your dexy output.

    Templates are applied to all files with .html extension which don't already
    contain "<head" or "<body" tags.

    Templates must be named _template.html with no dexy filters applied (TODO relax this)
    """
    ALIASES = ['ws']
    _SETTINGS = {
            "dir" : "output-site",
            "plugins" : (
                    "List of TemplatingPlugins to make available in environment.",
                    ["inflection", "builtins"]
                ),
            "default" : False
            }

    def nav_directories(self):
        """
        Returns a dict whose keys are top-level directores containing an
        'index.html' page and whose values are a list with the 'doc' object
        for the 'index.html' page and a dict of subdirectories in same format.

        """
        nav = [None, {}]

        self.log.debug("In nav_directories")

        def populate(nav, keys, value):
            pointer = nav
            for k in keys:
                if not pointer[1]:
                    pointer[1] = {}
                if not pointer[1].has_key(k):
                    pointer[1][k] = [None, {}]
                pointer = pointer[1][k]
            pointer[0] = doc

        for doc in self.wrapper.batch.docs():
            doc_dir = doc.output().parent_dir()
            if doc.is_index_page():
                path_elements = doc_dir.split(os.path.sep)

                # Trim off empty leading path elements.
                while path_elements and path_elements[0] in ('', '.'):
                    path_elements = path_elements[1:]

                if not path_elements:
                    self.log.debug("  adding doc %s to nav at root level" % doc.key)
                    nav[0] = doc
                else:
                    self.log.debug("  adding doc %s to nav" % doc.key)
                    populate(nav, path_elements, doc)
            else:
                self.log.debug("  doc %s is not index page, skipping" % doc.key)

        return nav

    def apply_and_render_template(self, doc):
        ws_template = doc.arg_value('ws-template')
        self.log.debug("  ws template for doc %s is %s" % (doc.key_with_class(), ws_template))
        if ws_template and not isinstance(ws_template, bool):
            template_file = ws_template
        else:
            template_file = "_template.html"
        template_path = None

        path_elements = doc.output().parent_dir().split(os.sep)
        for i in range(len(path_elements), -1, -1):
            template_path = os.path.join(*(path_elements[0:i] + [template_file]))
            if os.path.exists(template_path):
                self.log.debug("  using template %s for %s" % (template_path, doc.key))
                break

        nav_children = self._nav_directories
        for p_elem in path_elements:
            if nav_children[1].has_key(p_elem):
                nav_children = nav_children[1][p_elem]

        nav_siblings = self._nav_directories
        for p_elem in path_elements[0:-1]:
            if nav_siblings[1].has_key(p_elem):
                nav_siblings = nav_siblings[1][p_elem]

        breadcrumbs = []
        for i in range(1, len(path_elements)+1):
            breadcrumbs.append(os.sep.join(path_elements[0:i]))

        if not template_path:
            raise dexy.exceptions.UserFeedback("  no template path for %s" % doc.key)

        env = Environment(undefined=jinja2.StrictUndefined)
        env.loader = FileSystemLoader([".", os.path.dirname(template_path)])
        self.log.debug("  loading template at %s" % template_path)
        template = env.get_template(template_path)

        if doc.is_index_page():
            nav_current_index = doc.output().parent_dir()
        else:
            nav_current_index = None

        if doc.final_artifact.ext == '.html':
            content = unicode(doc.output())
        else:
            content = doc.output()

        navigation = {
                'current_index' : nav_current_index,
                'directories' : self._nav_directories,
                'children' : nav_children,
                'siblings' : nav_siblings,
                'breadcrumbs' : breadcrumbs,
                'parent_dir' : "/".join(path_elements[0:-1]),
                'current_dir' : "/".join(path_elements)
                }

        env_data = {}

        for alias in self.setting('plugins'):
            plugin = TemplatePlugin.create_instance(alias)
            env_data.update(plugin.run())

        env_data.update({
                'content' : content,
                'locals' : locals,
                'navigation' : navigation,
                'page_title' : doc.title(),
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
        self._nav_directories = self.nav_directories()

        self.create_reports_dir()

        for doc in wrapper.batch.docs():
            self.log.debug("processing doc %s" % doc.key_with_class())
            if doc.is_canonical_output():
                if doc.final_artifact.ext == ".html":
                    fragments = ('<html', '<body', '<head')
                    has_html_header = any(html_fragment in unicode(doc.output()) for html_fragment in fragments)

                    if has_html_header and not doc.args.get('ws_template'):
                        self.log.debug("  found html tag in output of %s" % doc.key)
                        self.write_canonical_doc(doc)
                    else:
                        self.apply_and_render_template(doc)
                elif doc.final_artifact.ext == '.json' and 'htmlsections' in doc.filters:
                    self.apply_and_render_template(doc)
                else:
                    self.write_canonical_doc(doc)

        self.log.debug("finished")
