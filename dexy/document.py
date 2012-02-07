from dexy.constants import Constants
import StringIO
import codecs
import dexy.controller
import dexy.introspect
import fnmatch
import hashlib
import json
import logging
import os
import re
import shutil
import time
import urllib2

try:
    import git
    USE_GIT = True
except ImportError:
    USE_GIT = False

class Document(object):

    def __init__(self):
        # initialize attributes
        self.args = {}
        self.artifacts = []
        self.elapsed = 0
        self.input_args = []
        self.input_keys = []
        self.inputs = []
        self.log = Constants.NULL_LOGGER # proper logging set up after we know our name
        self.logstream = StringIO.StringIO()
        self.priority = 10
        self.timing = []
        self.use_all_inputs = False

    def document_info(self):
        return {
            "artifacts" : [[a.hashstring, a.source, a.elapsed] for a in self.artifacts],
            "log" : self.logstream.getvalue(),
            "args" : self.args,
            "inputs" : [doc.key() for doc in self.inputs],
            "elapsed" : self.elapsed,
            "timing" : self.timing
        }

    def set_controller(self, controller):
        self.controller = controller

        # Set convenient attrs for info we use a lot.
        self.artifacts_dir = controller.args['artifactsdir']
        self.logsdir = controller.args['logsdir']
        self.artifact_class = controller.artifact_class
        self.db = controller.db
        self.batch_id = controller.batch_id

    def setup_log(self):
        self.log = logging.getLogger(self.key())
        self.log.setLevel(logging.DEBUG) # TODO Allow this to be changed.
        self.log.propagate = 0 # Stops logs being written to STDOUT if another library redirects root logger.
        handler = logging.StreamHandler(self.logstream)
        formatter = logging.Formatter(Constants.DEFAULT_LOGFORMAT)
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
        return "|".join([self.name] + self.filters)

    def add_input_key(self, input_key):
        if not input_key in self.input_keys:
            self.input_keys.append(input_key)

    def finalize_inputs(self, members_dict):
        """
        Called during setup, this method resolves which other docs this doc
        will depend on (have as inputs).
        """
        start = time.time()
        if len(self.input_args) > 0 or len(self.input_keys) > 0 or self.use_all_inputs:
            for doc in members_dict.values():
                if doc.key() in self.input_keys:
                    self.inputs.append(doc)
                else:
                    # Work out relative paths
                    dir1 = os.path.dirname(doc.name)
                    dir2 = os.path.dirname(self.name)
                    if dir1 == '':
                        dir1 = "."
                    if dir2 == "":
                        dir2 = "."

                    relpath = os.path.relpath(dir1, dir2)
                    relpath2 = os.path.relpath(dir2, dir1)

                    # Whether the document is in parent dir of input
                    in_parent_dir = not (".." in relpath) and not (relpath == ".")
                    in_same_dir = (relpath == ".") and (relpath2 == ".")
                    in_parent_or_child = (relpath == ".") or ((not ".." in relpath) ^ (not ".." in relpath2))

                    # See if input matches an item in inputs
                    specified = False
                    for input_glob in self.input_args:
                        # The full doc key is specified
                        is_exact_absolute_match = (input_glob == doc.key())

                        # The relative path doc key is specified
                        is_exact_relative_match = (os.path.join(relpath2, input_glob) == doc.key())

                        is_exact_match_in_parent_or_child_dir = (in_parent_or_child and input_glob == os.path.basename(doc.key()))

                        # A glob matches in any child dir
                        is_glob_match_in_child_dir = (in_parent_dir or in_same_dir) and fnmatch.fnmatch(os.path.basename(doc.key()), input_glob)

                        specified = (is_exact_absolute_match or is_exact_relative_match or is_exact_match_in_parent_or_child_dir or is_glob_match_in_child_dir)

                        if specified:
                           break

                    if self.args.has_key('exact-inputs'):
                        for exact_input in self.args['exact-inputs']:
                            if not specified:
                                specified = exact_input == doc.key()

                    # Work out relative priority
                    higher_priority = (self.priority > doc.priority)
                    equal_priority = (self.priority == doc.priority)

                    use_all_inputs = self.use_all_inputs
                    also_all_inputs = doc.use_all_inputs

                    all_inputs_and_qualified = use_all_inputs and (higher_priority or (equal_priority and in_parent_dir) or not also_all_inputs)
                    disqualified_by_strictinherit = self.controller.args['strictinherit'] and not (in_parent_or_child)

                    if specified or (all_inputs_and_qualified and not disqualified_by_strictinherit):
                        self.inputs.append(doc)

        elapsed = time.time() - start
        self.timing.append(("finalize-inputs", elapsed))

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

            local_filename = re.sub('[^\w\s-]', '', url).strip().lower()
            local_filename = re.sub('[-\s]+', '-', local_filename)
            filename = os.path.join(self.artifacts_dir, local_filename)
            header_filename = "%s.headers" % filename

            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            header_dict = {}
            if os.path.exists(header_filename):
                header_file = codecs.open(header_filename, "r", encoding="utf-8")
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

            if self.controller.args['uselocals'] and os.path.exists(filename):
                f = codecs.open(filename, "r", encoding="utf-8")
                data = f.read()
                f.close()
            else:
                if self.controller.args['uselocals']:
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
                    json.dump(header_dict, codecs.open(header_filename, "w", encoding="utf-8"))

                    data = url_contents
                except (urllib2.HTTPError, urllib2.URLError) as err:
                    if not hasattr(err, 'code'):
                        print "Trying to fetch %s for %s" % (url, self.name)
                        raise err

                    elif err.code == 304:
                        if os.path.exists(filename):
                            print "received NOT MODIFIED (304) from server, so using contents of %s" % (filename)
                            f = codecs.open(filename, "r", encoding="utf-8")
                            data = f.read()
                            f.close()
                        else:
                            raise err

                    elif err.code == 404:
                        raise Exception("url %s NOT FOUND (404) (for virtual file %s)" % (url, self.name))

                    else:
                        print "Trying to fetch %s for %s" % (url, self.name)
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
            f = open(self.name, "rb")
            data = f.read()
            f.close()

        return data

    def create_initial_artifact(self):
        artifact = self.artifact_class.setup(self, self.name)
        if len(self.filters) == 0:
            artifact.is_last = True
            if artifact.final is None:
                artifact.final = True
        artifact.save()
        if artifact.binary_output:
            if artifact.doc.virtual:
                # make a fake file
                with open(artifact.filepath(), "wb") as f:
                    f.write("virtual file")
            else:
                shutil.copyfile(artifact.name, artifact.filepath())
        return artifact

    def run(self):
        self.step = 0
        start = time.time()
        time_start = start


        artifact = self.create_initial_artifact()
        self.artifacts.append(artifact)
        self.last_artifact = artifact
        artifact_key = artifact.key
        self.timing.append(("create-initial-artifact", time.time() - start))
        start = time.time()
        self.log.info("(step %s) [run] %s -> %s" % \
                 (self.step, artifact_key, artifact.filename()))

        for f in self.filters:
            previous_artifact = artifact
            artifact_key += "|%s" % f
            self.step += 1

            FilterClass = self.get_filter_for_alias(f)
            artifact = self.artifact_class.setup(self, artifact_key, FilterClass, previous_artifact)
            self.timing.append(("setup-step-%s" % self.step, time.time() - start))
            start=time.time()

            self.log.info("(starting step %s) [run] %s -> %s" % \
                     (self.step, artifact_key, artifact.filename()))

            artifact.run()
            self.timing.append(("run-step-%s" % self.step, time.time() - start))
            start = time.time()

            self.last_artifact = artifact
            self.artifacts.append(artifact)
            self.timing.append(("append-step-%s" % self.step, time.time() - start))
            start = time.time()

        self.last_artifact.is_last = True
        self.last_artifact.save_meta()
        self.db.append_artifacts(self.artifacts)
        self.timing.append(("append-artifacts", time.time() - start))
        start = time.time()

        # Make sure all additional inputs are saved.
        for k, a in artifact.inputs().iteritems():
            if not a.is_complete():
                if not a.additional:
                    # should only get here if this is an additional artifact
                    raise Exception("artifact %s should already be complete" % a.key)

                # set to complete and save
                a.state = 'complete'
                try:
                    a.save()
                    self.db.update_artifact(a)
                except IOError:
                    # no file was created, something went wrong in the script that should have
                    # generated this artifact
                    raise Exception("""You requested an additional file named %s
                    but its artifact file (%s) does not exist. Something may have gone wrong
                    in one of the filters of %s""" % (a.key, a.filepath(), a.created_by))

        self.timing.append(("save-additional-inputs", time.time() - start))
        self.elapsed = time.time() - time_start
        return self
