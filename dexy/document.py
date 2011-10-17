from dexy.sizeof import asizeof
from dexy.constants import Constants
from dexy.utils import profile_memory
import StringIO
import dexy.controller
import dexy.introspect
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

    def __init__(self):
        # we use the filter_list a lot, cache it once.
        if not hasattr(self.__class__, 'filter_list'):
            # TODO log this
            self.__class__.filter_list = dexy.introspect.filters()

        # initialize attributes
        self.inputs = []
        self.input_keys = []
        self.artifacts = []
        self.use_all_inputs = False
        self.priority = 10
        self.log = Constants.NULL_LOGGER # proper logging set up after we know our name
        self.logstream = StringIO.StringIO()

    def document_info(self):
        return {
            "artifacts" : [a.hashstring for a in self.artifacts],
            "log" : self.logstream.getvalue(),
            "args" : self.args,
            "inputs" : [doc.key() for doc in self.inputs]
        }

    def set_controller(self, controller):
        self.controller = controller

        # Set convenient attrs for info we use a lot.
        self.artifacts_dir = controller.args['artifactsdir']
        self.logsdir = controller.args['logsdir']
        self.artifact_class = controller.artifact_class
        self.db = controller.db
        self.batch_id = controller.batch_id
        self.profmem = controller.args['profmem']

    def setup_log(self):
        self.log = logging.getLogger(self.key())
        self.log.setLevel(logging.DEBUG) # TODO Allow this to be changed.
        self.log.propagate = 0 # Stops logs being written to STDOUT if another library redirects root logger.
        handler = logging.StreamHandler(self.logstream)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

        try:
            self.log.addHandler(logging.getLogger('dexy').handlers[0])
        except IndexError:
            pass

    def set_name_and_filters(self, name_or_key, filters=[]):
        self.name = name_or_key.split("|")[0]
        self.ext = os.path.splitext(self.name)[1]
        self.filters = name_or_key.split("|")[1:]
        self.filters += filters

    def get_filter_for_alias(self, alias):
        """
        Given a filter alias, return the corresponding filter class.
        """
        return dexy.introspect.get_filter_for_alias(alias, self.__class__.filter_list)

    def final_artifact(self):
        return self.last_artifact

    def key(self):
        return "%s|%s" % (self.name, "|".join(self.filters))

    def add_input_key(self, input_key):
        if not input_key in self.input_keys:
            self.input_keys.append(input_key)

    def finalize_inputs(self, members_dict):
        """
        Called during setup, this method resolves which other docs this doc
        will depend on (have as inputs).
        """
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

                relpath = os.path.relpath(rel1, rel2)

                in_parent_dir = not (".." in relpath) and not (relpath == ".")

                higher_priority = (self.priority > doc.priority)
                equal_priority = (self.priority == doc.priority)

                if specified or higher_priority or (equal_priority and in_parent_dir) or not also_all_inputs:
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
            return self.get_filter_for_alias(alias)

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
        # put *safe* methods at top of list
        # check for safe methods first in controller
        # all other methods assumed to be dangerous and require 'danger' flag
        if self.args.has_key('contents'):
            data = self.args['contents']

        # potentially dangerous methods ...
        elif self.args.has_key('url'):
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

            if self.controller.args['locals'] and os.path.exists(filename):
                f = open(filename, "r")
                data = f.read()
                f.close()
            else:
                if self.controller.args['locals']:
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

            try:
                blob = tree[self.args['path']]
                data = blob.data_stream.read()
            except KeyError as e:
                print "error processing virtual file", self.key(), "can't find path", self.args['path'], "in", repo_url
                raise e

        elif self.virtual:
            data = None

        else:
            # Normal local file, just read the contents.
            f = open(self.name, "r")
            data = f.read()
            f.close()

        return data

    def create_initial_artifact(self):
        artifact = self.artifact_class.setup(self, self.name)
        artifact.save()
        return artifact

    def run(self):
        self.step = 0

        artifact = self.create_initial_artifact()
        self.artifacts.append(artifact)

        artifact_key = artifact.key
        self.log.info("(step %s) [run] %s -> %s" % \
                 (self.step, artifact_key, artifact.filename()))

        if self.profmem:
            profile_memory(self.controller, "document-%s-step-%s" % (self.key(), self.step))
            print
            print "size of controller", asizeof(self.controller)
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

            FilterClass = self.get_filter_for_alias(f)
            artifact = self.artifact_class.setup(self, artifact_key, FilterClass, previous_artifact)

            self.log.info("(step %s) [run] %s -> %s" % \
                     (self.step, artifact_key, artifact.filename()))

            artifact.run()

            self.last_artifact = artifact
            self.artifacts.append(artifact)

            if self.profmem:
                if artifact.data_dict:
                    print "size of text of", artifact.key, "in", self.key(), ":", asizeof(artifact.output_text())
          	    profile_memory(self.controller, "document-%s-step-%s" % (self.key(), self.step))

        self.last_artifact.is_last = True
        self.last_artifact.save_meta()

        # Make sure all additional inputs are saved.
        for k, a in artifact._inputs.iteritems():
            if not a.is_complete():
                a.state = 'complete'
                a.save()

        return self
