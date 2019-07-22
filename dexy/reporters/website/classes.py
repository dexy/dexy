from dexy.commands.utils import print_indented
from dexy.reporters.output import Output
from dexy.utils import file_exists
from dexy.utils import iter_paths
from dexy.utils import reverse_iter_paths
from functools import partial
from jinja2 import Environment
from jinja2 import FileSystemLoader
import dexy.data
import dexy.exceptions
import dexy.filters.templating_plugins
import inspect
import jinja2
import os
import posixpath
import urllib

class Website(Output):
    """
    Applies a template to create a website from your dexy output.

    Templates are applied to all files with .html extension which don't already
    contain "<head" or "<body" tags.
    """
    aliases = ['ws']
    _other_class_settings = {
        'doc' : {
            'apply-ws-to-content' : ("""
                If you want to put website-related content (like the link()
                function) in your content, set this to True so your content
                gets put through the jinja filter for the website reporter.
                """,
                False
            ),
            'apply-ws-to-content-var-start-string' : ("""
                Provide a custom jinja var-start-string to avoid clashes.
                """,
                None
            ),
            'apply-ws-to-content-var-end-string' : ("""
                Provide a custom jinja var-end-string to avoid clashes.
                """,
                None
                ),
            'ws-template' : (
                """
                Key of the template to apply for rendering in website.
                Setting of 'None' will use default template, 'False' will
                force no template to be used.
                """,
                None)
            },
        'data' : {
            'ws-template' : (
                """
                Key of the template to apply for rendering in website.
                Setting of 'None' will use default template, 'False' will
                force no template to be used.
                """,
                None)
            }
        }

    _settings = {
        "dir" : "output-site",
        "default-template" : ("Path to the default template to apply.", "_template.html"),
        "default" : False
    }

    def run(self, wrapper):
        self.wrapper=wrapper

        self.remove_reports_dir(self.wrapper, keep_empty_dir=True)
        self.create_reports_dir()

        self.setup()

        if self.wrapper.target:
            msg = "Not running website reporter because a target has been specified."
            self.log_warn(msg)
            return

        for doc in list(wrapper.nodes.values()):
            if self.should_process(doc):
                self.process_doc(doc)

        self.log_debug("finished")

    def setup(self):
        self.keys_to_outfiles = []
        self.locations = {}
        self.create_reports_dir()
        self.setup_navobj()

    def setup_navobj(self):
        self._navobj = self.create_navobj()

    def should_process(self, doc):
        if not doc.key_with_class() in self.wrapper.batch.docs:
            return False
        elif not doc.state in ('ran', 'consolidated'):
            return False
        elif not hasattr(doc, 'output_data'):
            return False
        elif not doc.output_data().output_name():
            return False
        elif not doc.output_data().is_canonical_output():
            msg = "skipping %s - not canonical"
            self.log_debug(msg % doc.key)
            return False
        else:
            return True

    def process_doc(self, doc):
        self.log_debug("processing %s" % doc.key)

        output_ext = doc.output_data().ext

        if output_ext == ".html":
            self.process_html(doc)

        elif isinstance(doc.output_data(), dexy.data.Sectioned):
            assert output_ext == ".json"
            self.apply_and_render_template(doc)

        else:
            self.write_canonical_data(doc)

    def process_html(self, doc):
        if doc.setting('ws-template') == False:
            self.log_debug("  ws-template is False for %s" % doc.key)
            self.write_canonical_data(doc)

        elif self.detect_html_header(doc) and not doc.setting('ws-template'):
            self.log_debug("  found html tag in output of %s" % doc.key)
            self.write_canonical_data(doc)

        else:
            self.apply_and_render_template(doc)

    def detect_html_header(self, doc):
        fragments = ('<html', '<body', '<head')
        return any(html_fragment
                      in str(doc.output_data())
                      for html_fragment in fragments)

    def create_navobj(self):
        navobj = Navigation()
        navobj.populate_lookup_table(self.wrapper.batch)
        navobj.walk()
        return navobj

    def template_file_and_path(self, doc):
        ws_template = doc.setting('ws-template')
        if ws_template and not isinstance(ws_template, bool):
            template_file = ws_template
        else:
            template_file = self.setting('default-template')

        template_path = None
        for subpath in reverse_iter_paths(doc.name):
            template_path = os.path.join(subpath, template_file)
            if file_exists(template_path):
                break

        if not template_path:
            msg = "no template path for %s" % doc.key
            raise dexy.exceptions.UserFeedback(msg)
        else:
            msg = "  using template %s for %s"
            msgargs = (template_path, doc.key)
            self.log_debug(msg % msgargs)

        return (template_file, template_path,)

    def jinja_environment(self, template_path, additional_args=None):
        """
        Returns jinja Environment object.
        """
        args = {
                'undefined' : jinja2.StrictUndefined
                }

        if additional_args:
            args.update(additional_args)

        env = Environment(**args)

        dirs = [".", os.path.dirname(__file__), os.path.dirname(template_path)]
        env.loader = FileSystemLoader(dirs)

        return env

    def apply_jinja_to_page_content(self, doc, env_data):
        args = {
                'undefined' : jinja2.StrictUndefined
                }

        keys = ['variable_start_string', 'variable_end_string',
                'block_start_string', 'block_end_string']


        for k in keys:
            setting_name = "apply-ws-to-content-%s" % k.replace("_", "-")
            if doc.safe_setting(setting_name):
                args[k] = doc.setting(setting_name)

        env = Environment(**args)

        self.log_debug("Applying jinja to doc content %s" % doc.key)
        try:
            content_template = env.from_string(str(doc.output_data()))
            return content_template.render(env_data)
        except Exception:
            self.log_debug("Template:\n%s" % str(doc.output_data()))
            self.log_debug("Env args:\n%s" % args)
            raise

    def template_environment(self, doc, template_path):
        raw_env_data = self.run_plugins()
        raw_env_data.update(self.website_specific_template_environment(doc.output_data(), {
            'template_source' : ("The directory containing the template file used.",
                template_path)
            }))

        env_data = dict((k, v[1]) for k, v in raw_env_data.items())

        if doc.safe_setting('apply-ws-to-content'):
            env_data['content'] = self.apply_jinja_to_page_content(doc, env_data)
        else:
            env_data['content'] = doc.output_data()

        return env_data

    def fix_ext(self, filename):
        basename, ext = os.path.splitext(filename)
        return "%s.html" % basename

    def apply_and_render_template(self, doc):
        template_info = self.template_file_and_path(doc)
        template_file, template_path = template_info
        env_data = self.template_environment(doc, template_path)

        self.log_debug("  creating jinja environment")
        env = self.jinja_environment(template_path)

        self.log_debug("  loading jinja template at %s" % template_path)
        template = env.get_template(template_path)
       
        output_file = self.fix_ext(doc.output_data().output_name())
        output_path = os.path.join(self.setting('dir'), output_file)

        try:
            os.makedirs(os.path.dirname(output_path))
        except os.error:
            pass

        self.log_debug("  writing to %s" % (output_path))
        template.stream(env_data).dump(output_path, encoding="utf-8")

    def help(self, data):
        nodoc = ('navobj', 'navigation',)
        print_indented("Website Template Environment Variables:", 4)
        print('')
        print_indented("Navigation and Content Related:", 6)
        env = self.website_specific_template_environment(data)
        for k in sorted(env):
            if k in nodoc:
                continue
            docs, value = env[k]
            print_indented("%s: %s" % (k, docs), 8)

        print('')
        navobj = env['navobj'][1]
        root = navobj.nodes['/']
        members = [(name, obj) for name, obj in inspect.getmembers(root)
                if not name.startswith('__')]

        print_indented("navobj Node attributes (using root node):", 6)
        print('')
        for member_name, member_obj in members:
            if not inspect.ismethod(member_obj):
                print_indented("%s: %r" % (member_name, member_obj), 8)
       
        print('')

        print_indented("navobj Node methods (using root node):", 6)
        print('')
        for member_name, member_obj in members:
            if inspect.ismethod(member_obj):
                print_indented("%s()" % (member_name), 8)
                print_indented("%s" % inspect.getdoc(member_obj), 10)
                print_indented("%s" % member_obj(), 10)
                print('')

        print('')
        print_indented("Variables From Plugins:", 6)
        env = self.run_plugins()
        for k in sorted(env):
            docs, value = env[k]
            print_indented("%s: %s" % (k, docs), 8)

        print('')
        print_indented("navobj Nodes:", 4)
        print_indented(navobj.debug(), 6)

    def website_specific_template_environment(self, data, initial_args=None):
        env_data = {}

        if initial_args:
            env_data.update(initial_args)

        current_dir = posixpath.dirname(data.output_name())
        parent_dir = os.path.split(current_dir)[0]

        env_data.update({
                'link' : ("Function to create link to other page.",
                    partial(self.link, data)),
                'section' : ("Function to create link to section on any page.",
                    partial(self.section, data)),
                'navigation' : ("DEPRECATED. 'navigation' object.",
                    {}),
                'nav' : ("The node for the current document's directory.",
                    self._navobj.nodes["/%s" % current_dir]),
                'root' : ("The root node of the navigation tree.",
                    self._navobj.nodes["/"]),
                'navobj' : ("DEPRECATED. Same as 'navtree'.",
                    self._navobj),
                'navtree' : ("The complete navigation tree for the website.",
                    self._navobj),
                'page_title' : ("Title of the current page.",
                    data.title()),
                'title' : ("Title of the current page.",
                    data.title()),
                'parent_dir' : ("The directory one level up from the document being processed.",
                    parent_dir),
                'current_dir' : ("The directory containing the document being processed.",
                    current_dir),
                's' : ("'%s' type data object representing the current doc." % data.alias,
                    data),
                'd' : ("'%s' type data object representing the current doc." % data.alias,
                    data),
                'source' : ("Output name of current doc.",
                    data.output_name()),
                'wrapper' : ("The current wrapper object.",
                    self.wrapper)
                })

        return env_data

    def section(self, data, section_name=None, url_base=None, link_text = None):
        """
        Returns an HTML link to section without needing to specify which
        document it is in (section name must be globally unique).
        """
        matching_nodes = self.wrapper.lookup_sections.get(section_name)

        if not matching_nodes:
            msg = "Trying to create a link in %s but no section found matching '%s'"
            msgargs = (data.key, section_name,)
            raise dexy.exceptions.UserFeedback(msg % msgargs)
        elif len(matching_nodes) > 1:
            # TODO make it an option to select a default where there is
            # more than one option
            msg = "Trying to create a link in %s to '%s' but multiple docs match."
            msgargs = (data.key, section_name,)
            raise dexy.exceptions.UserFeedback(msg % msgargs)

        assert len(matching_nodes) == 1
        link_to_data = matching_nodes[0]
        section = link_to_data[section_name]
        anchor = section['id']
        if not link_text:
            link_text = section_name

        return self.link_for(url_base, data.relative_path_to(link_to_data.output_name()), link_text, anchor)

    def link(self, data, doc_key, section_name=None, url_base=None, link_text = None, description=False):
        """
        Returns an HTML link to document, optionally with an anchor linking to section.
        """
        matching_nodes = self.wrapper.lookup_nodes.get(doc_key)

        if not matching_nodes:
            msg = "Trying to create a link in %s but no doc found matching '%s'"
            msgargs = (data.key, doc_key,)
            raise dexy.exceptions.UserFeedback(msg % msgargs)
        elif len(matching_nodes) > 1:
            # TODO make it an option to select a default where there is
            # more than one option
            msg = "Trying to create a link to '%s' but multiple docs match."
            msgargs = (doc_key,)
            raise dexy.exceptions.UserFeedback(msg % msgargs)

        assert len(matching_nodes) == 1
        link_to_data = matching_nodes[0]
        anchor = None

        if section_name:
            if section_name in list(link_to_data.keys()):
                section = link_to_data[section_name]
                anchor = section['id']
                if not link_text:
                    link_text = section_name
            else:
                msg = "Did not find section named '%s' in '%s'"
                msgargs = (section_name, doc_key)
                raise dexy.exceptions.UserFeedback(msg % msgargs)
        else:
            if not link_text:
                link_text = link_to_data.title()


        relative_link_to = data.relative_path_to(link_to_data.output_name())

        link_html = self.link_for(url_base, relative_link_to, link_text, anchor)

        if description and link_to_data.safe_setting('description'):
            return "%s\n<p>%s</p>" % (link_html, link_to_data.setting('description'))
        else:
            return link_html

    def link_for(self, url_base, link, link_text, anchor=None):
        if url_base:
            url = urllib.parse.urljoin(url_base, link)
        else:
            url = link
        if anchor:
            return """<a href="%s#%s">%s</a>""" % (url, anchor, link_text)
        else:
            return """<a href="%s">%s</a>""" % (url, link_text)

class Navigation(object):
    def __init__(self):
        self.lookup_table = {}
        self.nodes = {}
        self.root = None

    def populate_lookup_table(self, batch):
        for data in batch:
            if not data.output_name():
                continue

            parent_dir = "/" + os.path.dirname(data.output_name())
            if not parent_dir in self.lookup_table:
                self.lookup_table[parent_dir] = {'docs' : []}

            if data.is_canonical_output():
                self.lookup_table[parent_dir]['docs'].append(data)

            if data.is_index_page():
                self.lookup_table[parent_dir]['index-page'] = data

    def walk(self):
        """
        Build nodes dict from already-populated lookup table.
        """
        for path, info in self.lookup_table.items():
            parent = None
            ancestors = []
            level = 0
            for parent_path in iter_paths(path):
                if not parent_path in self.nodes:
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
            if 'index-page' in info:
                parent.index_page = info['index-page']

    def debug(self):
        """
        Returns a dump of useful information.
        """
        info = []
        for path in sorted(self.nodes):
            node = self.nodes[path]

            info.append('')
            info.append("node: %s" % path)

            if node.index_page:
                info.append("  index-page:")
                info.append("    %s" % node.index_page.key)
                info.append('')
            else:
                info.append("  no index page.")
                info.append('')

            if node.docs:
                info.append("  docs:")
            for child in node.docs:
                info.append("    %s" % child.key)
            info.append('')

            if node.children:
                info.append("  children:")

            for child in node.children:
                info.append("    %s" % child.location)
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

    def __lt__(self, other):
        return self.location < other.location

    def __repr__(self):
        return "Node(%s)" % self.location

    def has_children_with_index_pages(self):
        """
        Boolean value.
        """
        return any(node.index_page for node in self.children)

    def breadcrumbs(self, divider = " &gt; "):
        """
        Navigation breadcrumbs showing each parent directory.
        """
        return divider.join("""<a href="%s">%s</a>""" % (node.location, node.index_page.title()) for node in self.ancestors if node.index_page)
