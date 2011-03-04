from dexy.artifact import Artifact
from dexy.logger import log
import glob
import json
import os
import urllib2

### @export "init"
class Document(object):
    def __init__(self, name_or_key, filters = []):
        self.name = name_or_key.split("|")[0]
        self.filters = name_or_key.split("|")[1:]
        self.filters += filters
        self.inputs = []
        self.input_keys = []
        self.artifacts = []
        self.use_all_inputs = False

### @export "key"
    def key(self):
        return "%s|%s" % (self.name, "|".join(self.filters))

### @export "inputs"
    def add_input_key(self, input_key):
        if not input_key in self.input_keys:
            self.input_keys.append(input_key)

    def finalize_inputs(self, members_dict):
        if self.use_all_inputs:
            for doc in members_dict.values():
                if not doc.use_all_inputs: # this would create mutual dependency
                    self.inputs.append(doc)
        else:
            self.inputs = [members_dict[k] for k in self.input_keys]

### @export "steps"
    def next_handler_name(self):
        if self.at_last_step():
            return 'None'
        else:
            return self.filters[self.step]
    
    def next_handler_class(self):
        if not self.at_last_step():
            return self.controller.handlers[self.next_handler_name()]

    def at_last_step(self):
        return (len(self.filters) == self.step)

### @export "input-artifacts"
    def input_artifacts(self):
        input_artifacts = {}
        for input_doc in self.inputs:
            artifact = input_doc.artifacts[-1]
            input_artifacts[input_doc.key()] = artifact.dj_filename()
        return input_artifacts

### @export "create-initial-artifact"
    def create_initial_artifact(self):
        artifact_key = self.name
        artifact = Artifact.setup(self, artifact_key, None)
        artifact.ext = os.path.splitext(self.name)[1]

        if artifact.doc.args.has_key('url'):
            url = artifact.doc.args['url']
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
                artifact.data = f.read()
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
    
                    artifact.data = url_contents
                except urllib2.URLError as err:
                    if os.path.exists(filename):
                        print "unable to fetch remote url %s because %s\nusing contents of %s" % (url, err, filename)
                    else:
                        raise Exception("unable to fetch remote url %s because %s\nno cache found in %s" % (url, err, filename))

                    f = open(filename, "r")
                    artifact.data = f.read()
                    f.close()
                except urllib2.HTTPError as err:
                    if err.code == 304:
                        print "received http status code %s, using contents of %s" % (err.code, filename)
                        f = open(filename, "r")
                        artifact.data = f.read()
                        f.close()
                    elif err.code == 404:
                        raise Exception("""received http status code %s while trying to fetch %s for %s""" % 
                                        (err.code, url, self.name))
                    else:
                        # Some other http error, we want to know about it.
                        print url
                        raise err

        elif artifact.doc.args.has_key('contents'):
            artifact.data = artifact.doc.args['contents']

        else:
            # Normal local file, just read the contents.
            f = open(self.name, "r")
            artifact.data = f.read()
            f.close()
        
        artifact.data_dict['1'] = artifact.data
        artifact.input_artifacts = self.input_artifacts()
        artifact.set_hashstring()
        artifact.generate()
        self.artifacts.append(artifact)
        return (artifact, artifact_key)

### @export "run"
    def run(self, controller):
        self.controller = controller
        self.step = 0
        
        artifact, artifact_key = self.create_initial_artifact()
        log.info("(step %s) %s -> %s" % \
                 (self.step, artifact_key, artifact.filename()))

        for f in self.filters:
            artifact_key += "|%s" % f
            self.step += 1
            
            if not self.controller.handlers.has_key(f):
                print sorted(self.controller.handlers.keys())
                raise Exception("""You requested filter alias '%s'
                                but this is not available.""" % f)
            HandlerClass = self.controller.handlers[f]
            h = HandlerClass.setup(
                self, 
                artifact_key,
                artifact, 
                self.next_handler_class()
            )

            try: 
                artifact = h.generate_artifact()
            except Exception as e:
                print "Error occurred while applying", f, "for", artifact_key
                if hasattr(h.artifact, 'hashstring'):
                    pattern = os.path.join(self.controller.artifacts_dir, h.artifact.hashstring)
                    files_matching = glob.glob(pattern)
                    if len(files_matching) > 0:
                        print "Here are working files which might have clues about this error:"
                        for f in files_matching:
                            print f
                raise e

            if not artifact:
                raise Exception("no artifact created!")
            self.artifacts.append(artifact)
            
            log.info("(step %s) %s -> %s" % \
                     (self.step, artifact_key, artifact.filename()))

        return self
