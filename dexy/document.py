from dexy.sizeof import asizeof
from dexy.utils import profile_memory
import StringIO
import dexy.controller
import hashlib
import json
import logging
import os
import urllib2

try:
    import git
    USE_GIT = True
except ImportError:
    USE_GIT = False

class Document(object):
    def __init__(self, artifact_class, name_or_key, filters = []):
        self.artifact_class = artifact_class
        self.name = name_or_key.split("|")[0]
        self.ext = os.path.splitext(self.name)[1]
        self.filters = name_or_key.split("|")[1:]
        self.filters += filters
        self.inputs = []
        self.input_keys = []
        self.artifacts = []
        self.use_all_inputs = False

        # Set up document log.
        self.logstream = StringIO.StringIO()
        self.log = logging.getLogger(self.key())
        self.log.setLevel(logging.DEBUG) # TODO Allow this to be changed.
        self.log.propagate = 0 # Stops logs being written to STDOUT if another library redirects root logger.
        handler = logging.StreamHandler(self.logstream)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

        # Log all document log messages to main dexy log.
        try:
            self.log.addHandler(logging.getLogger('dexy').handlers[0])
        except IndexError:
            pass


    def final_artifact(self):
        return self.last_artifact

    def key(self):
        return "%s|%s" % (self.name, "|".join(self.filters))

    def add_input_key(self, input_key):
        if not input_key in self.input_keys:
            self.input_keys.append(input_key)

    def finalize_inputs(self, members_dict):
        if self.use_all_inputs:
            for doc in members_dict.values():
                also_all_inputs = doc.use_all_inputs
                specified = doc.key() in self.input_keys

                rel1 = os.path.dirname(doc.name)
                rel2 = os.path.dirname(self.name)
                if rel1 == '':
                    rel1 = "."
                if rel2 == "":
                    rel2 = "."

                in_subdir = (".." in os.path.relpath(rel2, rel1))

                if specified or in_subdir or not also_all_inputs:
                    self.inputs.append(doc)
        else:
            inputs = []
            for k in self.input_keys:
                # k is a filename, not a glob
                for x in members_dict.keys():
                    if x == k:
                        inputs.append(x)

            self.inputs = [members_dict[k] for k in self.input_keys]
        self.log.debug("Setting inputs for %s to: %s" % (self.key(), [i.key() for i in self.inputs]))

    def next_filter_alias(self):
        if self.at_last_step():
            return None
        else:
            return self.filters[self.step]

    def next_filter_class(self):
        alias = self.next_filter_alias()
        if alias:
            return dexy.controller.Controller.get_handler_for_alias(alias)

    def at_last_step(self):
        return (len(self.filters) == self.step)

    def input_artifacts(self):
        input_artifacts = {}
        for i in self.inputs:
            k = i.key()
            a = i.final_artifact()
            if not a:
                raise Exception("No final artifact for document %s" % i.key())
            input_artifacts[k] = a
        return input_artifacts

    def initial_artifact_data(self):
        if self.args.has_key('url'):
            url = self.args['url']
            filename = os.path.join(self.artifacts_dir, self.name)
            header_filename = "%s.headers" % filename

            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            header_dict = {}
            if os.path.exists(header_filename):
                header_file = open(header_filename, "r")
                header_dict = json.load(header_file)
                header_file.close()

            request = urllib2.Request(url)

            # TODO add an md5 of the file to the header dict so we can check
            # that the etag/last-modified header is the corresponding one
            # TODO invalidate the hash if URL has changed
            # TODO get modification time of file via ftplib
            # TODO implement handlers for version control systems
            # TODO use FileHandler for default case?

            # Add any custom headers...
            # note that headers are ignored by anything other than http
            if header_dict.has_key('ETag') and os.path.exists(filename):
                request.add_header('If-None-Match', header_dict['ETag'])
            elif header_dict.has_key('Last-Modified') and os.path.exists(filename):
                request.add_header('If-Modifed-Since', header_dict['Last-Modified'])

            if self.use_local_files and os.path.exists(filename):
                f = open(filename, "r")
                data = f.read()
                f.close()
            else:
                if self.use_local_files:
                    print "local file %s not found, fetching remote url" % filename

                try:
                    u = urllib2.urlopen(request)
                    print "downloading contents of %s" % url
                    url_contents = u.read()

                    # Save the contents in our local cache
                    f = open(filename, "wb")
                    f.write(url_contents)
                    f.close()

                    # Save header info in our local cache
                    header_dict = {}
                    for s in u.info().headers:
                        a = s.partition(":")
                        header_dict[a[0]] = a[2].strip()
                    json.dump(header_dict, open(header_filename, "w"))

                    data = url_contents
                except urllib2.URLError as err:
                    if os.path.exists(filename):
                        print "unable to fetch remote url %s because %s\nusing contents of %s" % (url, err, filename)
                    else:
                        raise Exception("unable to fetch remote url %s because %s\nno cache found in %s" % (url, err, filename))

                    f = open(filename, "r")
                    data = f.read()
                    f.close()
                except urllib2.HTTPError as err:
                    if err.code == 304:
                        print "received http status code %s, using contents of %s" % (err.code, filename)
                        f = open(filename, "r")
                        data = f.read()
                        f.close()
                    elif err.code == 404:
                        raise Exception("""received http status code %s while trying to fetch %s for %s""" % 
                                        (err.code, url, self.name))
                    else:
                        # Some other http error, we want to know about it.
                        print url
                        raise err

        elif self.args.has_key('repo') and self.args.has_key('path'):
            if not USE_GIT:
                raise Exception("you can't use repo/path unless you install GitPython")
            repo_url = self.args['repo']
            digest = hashlib.md5(repo_url).hexdigest()
            local_repo_dir = os.path.join(self.artifacts_dir, "repository-%s" % digest)

            if os.path.exists(local_repo_dir):
                repo = git.Repo(local_repo_dir)
                o = repo.remotes.origin
                assert o.url == repo_url, "local repo exists but url %s does not match requested url %s" % (o.url, repo_url)
                o.pull() # TODO remember last pulled time so that don't do this too often? what if network unavailable?
            else:
                repo = git.Repo.clone_from(repo_url, local_repo_dir)

            if self.args.has_key('commit'):
                commit = self.args['commit']
                tree = repo.commit(commit).tree
            else:
                tree = repo.heads.master.commit.tree

            blob = tree[self.args['path']]
            data = blob.data_stream.read()

        elif self.args.has_key('contents'):
            data = self.args['contents']

        elif self.virtual:
            data = None

        else:
            # Normal local file, just read the contents.
            f = open(self.name, "r")
            data = f.read()
            f.close()

        return data

    def create_initial_artifact(self):
        # Create and set up the new artifact.
        artifact = self.artifact_class.setup(self, self.name)
        artifact.elapsed = 0
        artifact.document_key = self.key()
        artifact.controller_args = self.controller_args
        artifact.save()

        # Add the new artifact to the document's list of artifacts.
        self.artifacts.append(artifact)

        return artifact

    def run(self, controller):
        self.step = 0
        self.use_local_files = controller.use_local_files
        self.artifacts_dir = controller.artifacts_dir
        self.db = controller.db
        self.batch_id = controller.batch_id

        artifact = self.create_initial_artifact()

        artifact_key = artifact.key
        self.log.info("(step %s) [run] %s -> %s" % \
                 (self.step, artifact_key, artifact.filename()))

        if self.controller_args.profile_memory:
            profile_memory(controller, "document-%s-step-%s" % (self.key(), self.step))
            print
            print "size of controller", asizeof(controller)
            print "size of text of", artifact.key, ":", asizeof(artifact.output_text())
            print "size of document", asizeof(self)
            tot = 0
            for x in sorted(self.__dict__.keys()):
                y = self.__dict__[x]
                tot += asizeof(y)
                print x, asizeof(y)
            print "tot", tot

        self.last_artifact = artifact

        for f in self.filters:
            previous_artifact = artifact
            artifact_key += "|%s" % f
            self.step += 1

            FilterClass = controller.get_handler_for_alias(f)
            artifact = self.artifact_class.setup(self, artifact_key, FilterClass, previous_artifact)

            self.log.info("(step %s) [run] %s -> %s" % \
                     (self.step, artifact_key, artifact.filename()))

            artifact.run()

            self.last_artifact = artifact
            self.artifacts.append(artifact)

            if self.controller_args.profile_memory:
                if artifact.data_dict:
                    print "size of text of", artifact.key, "in", self.key(), ":", asizeof(artifact.output_text())
          	    profile_memory(controller, "document-%s-step-%s" % (self.key(), self.step))

        # Make sure all additional inputs are saved.
        for k, a in artifact._inputs.iteritems():
            if not a.is_complete():
                a.state = 'complete'
                a.save()

        return self
