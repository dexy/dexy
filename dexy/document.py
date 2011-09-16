from dexy.utils import profile_memory
import StringIO
import json
import logging
import os
import urllib2

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

        # Set up document log.
        self.logstream = StringIO.StringIO()
        self.log = logging.getLogger(self.key())
        self.log.setLevel(logging.DEBUG) # TODO Allow this to be changed.
        handler = logging.StreamHandler(self.logstream)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

        # Log all document log messages to main dexy log.
        try:
            self.log.addHandler(logging.getLogger('dexy').handlers[0])
        except IndexError:
            pass

        self.use_all_inputs = False

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
                if specified or not also_all_inputs:
                    self.inputs.append(doc)
        else:
            self.inputs = [members_dict[k] for k in self.input_keys]

    def next_filter_alias(self):
        if self.at_last_step():
            return None
        else:
            return self.filters[self.step]

    def next_filter_class(self):
        alias = self.next_filter_alias()
        if alias:
            return self.controller.get_handler_for_alias(alias)

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
            filename = os.path.join(self.controller.artifacts_dir, self.name)
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

            if self.controller.use_local_files and os.path.exists(filename):
                f = open(filename, "r")
                data = f.read()
                f.close()
            else:
                if self.controller.use_local_files:
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

        elif self.args.has_key('contents'):
            data = self.args['contents']

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

        # Add the new artifact to the document's list of artifacts.
        self.artifacts.append(artifact)

        return artifact

    def run(self, controller):
        self.controller = controller
        self.step = 0

        artifact = self.create_initial_artifact()
        artifact_key = artifact.key
        self.log.info("(step %s) [run] %s -> %s" % \
                 (self.step, artifact_key, artifact.filename()))
        profile_memory("document-%s-step-%s" % (self.key(), self.step))
        self.last_artifact = artifact
        for f in self.filters:
            previous_artifact = artifact
            artifact_key += "|%s" % f
            self.step += 1

            FilterClass = self.controller.get_handler_for_alias(f)
            artifact = self.artifact_class.setup(self, artifact_key, FilterClass, previous_artifact)

            self.log.info("(step %s) [run] %s -> %s" % \
                     (self.step, artifact_key, artifact.filename()))

            artifact.run()

            self.last_artifact = artifact
      	    profile_memory("document-%s-step-%s" % (self.key(), self.step))


        # Make sure all additional inputs are saved.
        for k, a in artifact._inputs.iteritems():
            if not a.is_complete():
                a.state = 'complete'
                a.save()

        profile_memory("document-%s-complete" % (self.key()))
        return self
