from dexy.reporter import Reporter
from jinja2 import Environment
from jinja2 import FileSystemLoader
import datetime
import os
import shutil
import this_report_is_deprecated_until_it_gets_updated

class SiteReporter(Reporter):
    def setup_template(self):
        env = Environment()
        env.loader = FileSystemLoader(os.path.dirname(__file__))
        self.template = env.get_template('site_reporter_template.html')

    def setup_final_artifacts(self):
        self.artifacts = []

        for doc in self.controller.docs:
            artifact = doc.final_artifact()

            if artifact.final:
                self.artifacts.append(artifact)

            for k, a in artifact._inputs.items():
                if not a:
                    print "no artifact exists for key", k
                else:
                    if a.additional and a.final:
                        if not a.is_complete():
                            a.state = 'complete'
                            a.save()
                        self.artifacts.append(artifact)

    def setup_dirs(self):
        """Return a dict of directories and the artifacts in each directory."""
        self.dirs = {}
        for artifact in self.artifacts:
            dirname = os.path.dirname(artifact.canonical_filename())
            if self.dirs.has_key(dirname):
                if not artifact.key in [a.key for a in self.dirs[dirname]]:
                    self.dirs[dirname].append(artifact)
            else:
                self.dirs[dirname] = [artifact]

        self.html_filenames = {}
        self.artifact_filenames = {}
        for d in self.dirs.keys():
            self.html_filenames[d] = {}
            self.artifact_filenames[d] = {}

    def write_html_page_and_artifact(self, artifact):
        """Write artifact and maybe a HTML display page."""

        artifact_fn = artifact.canonical_filename()
        html_page_fn = "%s.html" % artifact_fn
        if artifact.ext == '.html':
            if not "|hd" in artifact.key: # TODO more robust test of whether full or fragment HTML
                artifact_fn = False
            elif os.path.basename(artifact_fn) == 'index.html':
                # we need index.html to be the html page
                html_page_fn = artifact_fn
                artifact_fn = artifact.long_canonical_filename()

        if artifact_fn:
            artifact.write_to_file(os.path.join(self.report_dir, artifact_fn))

        if artifact.ext in ['.html']:
            content = artifact.output_text()
        elif artifact.ext in ['.txt']:
            content = """<pre>\n%s\n</pre>""" % artifact.output_text()
        elif artifact.ext in ['.png', '.jpg', '.gif']:
            content = """<a href="%s"><img src="%s" /></a>""" % (artifact_fn, artifact_fn)
        elif artifact.ext in ['', '.pdf', '.css', '.rb', '.py', '.swf', '.R']:
            content = """<a href="%s">%s</a>""" % (artifact_fn, artifact_fn)
        else:
            self.log.debug("site reporter using default handling for extension %s" % artifact.ext)
            content = """<a href="%s">%s</a>""" % (artifact_fn, artifact_fn)

        env_data = {
            'a' : artifact,
            'title' : artifact.key,
            'content' : content,
            'directory' : os.path.dirname(html_page_fn),
            'dirs' : self.dirs.keys(),
            'pretty_site_name' : self.pretty_site_name,
            'relpath' : os.path.relpath,
            'basename' : os.path.basename,
            'site_name' : self.site_name,
            'artifact_fn' : artifact_fn,
            'html_page_fn' : html_page_fn
        }
        html_page_parent_dir = os.path.dirname(os.path.join(self.report_dir, html_page_fn))
        if not os.path.exists(html_page_parent_dir):
                os.makedirs(html_page_parent_dir)
        self.template.stream(env_data).dump(os.path.join(self.report_dir, html_page_fn))

    def run(self):
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        self.report_dir = os.path.join(self.controller.logs_dir, "site-%s" % self.timestamp)
        self.latest_report_dir = os.path.join(self.controller.logs_dir, "site-latest")
        self.site_name = os.path.split(os.path.abspath(os.curdir))[1]
        self.pretty_site_name = " ".join([n.capitalize() for n in self.site_name.split("-")])

        # This shouldn't matter unless dexy gets run twice in 1 second
        shutil.rmtree(self.report_dir, ignore_errors=True)
        os.mkdir(self.report_dir)
        self.setup_template()
        self.setup_final_artifacts()
        self.setup_dirs()

        for artifact in self.artifacts:
            self.write_html_page_and_artifact(artifact)

        def write_index(directory, children):
            # create an index page for each directory
            index_filename = os.path.join(self.report_dir, directory, 'index.html')
            env_data = {
                'children' : children,
                'directory' : directory,
                'content' : '',
                'dirs' : self.dirs.keys(),
                'pretty_site_name' : self.pretty_site_name,
                'relpath' : os.path.relpath,
                'basename' : os.path.basename,
                'site_name' : self.site_name
            }
            self.template.stream(env_data).dump(index_filename)


        for dirname, children in self.dirs.iteritems():
            write_index(dirname, children)

        shutil.rmtree(self.latest_report_dir, ignore_errors=True)
        shutil.copytree(self.report_dir, self.latest_report_dir)
