from ordereddict import OrderedDict
from dexy.common import Common
import dexy.introspect
import hashlib
import os
import shutil

class Opuscule(Common):
    def __init__(self, key, *children, **kw):
        self.key = key
        self.children = list(children)
        self.pre = kw.get('pre', self.pre)
        self.post = kw.get('post', self.post)
        self.args = kw
        self.data = None
        self.hashstring = ""
        self.visited = []

        self.artifacts_dir = 'artifacts' # TODO don't hard code
        self.controller_args = {
                'ignore' : False
                }

        self.process_key()
        self.additional_setup()

    def process_key(self):
        pass

    def additional_setup(self):
        pass

    def pre(self, *args, **kw):
        pass

    def post(self, *args, **kw):
        pass

    def __iter__(self):
        def next_task():
            yield self.pre
            yield self
            yield self.post

        return next_task()

    def __call__(self, tree, *args, **kw):
        self.tree = tree
        self.log = tree.log

        for child in self.children:
            for task in child:
                task(tree, *args, **kw)

        if kw.get('dry', False):
            self.dry_run(*args, **kw)
        else:
            self.run(*args, **kw)

    def dry_run(self, *args, **kw):
        print "DRY RUN", self.key, args, kw

    def run(self, *args, **kw):
        pass

class Artifact(Opuscule):
    def create_temp_dir(self, populate=False):
        tempdir = self.temp_dir()
        shutil.rmtree(tempdir, ignore_errors=True)
        os.mkdir(tempdir)

        if populate:
            for opus in self.tree.visited:
                if isinstance(opus, Artifact):
                    filename = os.path.join(tempdir, opus.canonical_filename())
                    if os.path.exists(opus.filepath()):
                        opus.write_to_file(filename)

            previous = self.previous_artifact_filepath
            workfile = os.path.join(tempdir, self.previous_canonical_filename)
            if not os.path.exists(os.path.dirname(workfile)):
                os.makedirs(os.path.dirname(workfile))
            self.log.debug("Copying %s to %s" % (previous, workfile))
            shutil.copyfile(previous, workfile)

    def write_to_file(self, filename):
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname) and not dirname == '':
            os.makedirs(dirname)
        shutil.copyfile(self.filepath(), filename)

    def run(self, *args, **kw):
        self.set_hashstring()

        if hasattr(self, 'prior'):
            self.previous_artifact_filepath = self.prior.filepath()

        if self.is_cached():
            self.load_from_cache()
        else:
            self.generate()
            self.persist_to_cache()

        self.tree.visited.append(self)

    def process_key(self):
        self.name = self.key.split("|")[0]
        self.ext = os.path.splitext(self.name)[1]
        self.filters = self.key.split("|")[1:]

    def additional_setup(self):
        self.prior = self.args.get('prior')
        self.previous_canonical_filename = self.prior.canonical_filename()

    def hash_data(self):
        hash_data = OrderedDict()
        hash_data['prior'] = self.prior.hashstring
        hash_data['key'] = self.key
        return hash_data

    def set_hashstring(self):
        self.hashstring = self.compute_hash(str(self.hash_data()))
        self.tree.hashstring = self.compute_hash(self.tree.hashstring + self.hashstring)

    def compute_hash(self, text):
        return hashlib.md5(text).hexdigest()

    def persist_to_cache(self):
        with open(self.filepath(), "wb") as f:
            f.write(self.data)

    def load_from_cache(self):
        with open(self.filepath(), "rb") as f:
            self.data = f.read()

    def cache_file(self):
        return "artifacts/%s.cache" % self.hashstring

    def is_cached(self):
        return os.path.exists(self.cache_file())

    def generate(self, *args, **kw):
        filter_class = self.get_filter()
        filter_instance = filter_class()
        filter_instance.artifact = self
        filter_instance.log = self.log
        filter_instance.process()

    def get_filter(self):
        alias = self.filters[-1]

        if not hasattr(self.__class__, "filter_list"):
            self.__class__.filter_list = dexy.introspect.filters()

        return dexy.introspect.get_filter_for_alias(alias, self.__class__.filter_list)

    def filter_args(self):
        # TODO implement properly
        return self.args

class InitialArtifact(Artifact):
    def hash_data(self):
        hash_data = OrderedDict()
        hash_data['input'] = self.input_data
        hash_data['key'] = self.key
        hash_data['tree'] = self.tree.hashstring
        return hash_data

    def additional_setup(self):
        if os.path.exists(self.name):
            with open(self.name, "rb") as f:
                self.input_data = f.read()
        else:
            self.input_data = None

    def generate(self, *args, **kw):
        self.data = self.input_data

class Doc(Opuscule):
    """
    A single file + 0 or more filters applied to that file.
    """
    def process_key(self):
        self.name = self.key.split("|")[0]
        self.ext = os.path.splitext(self.name)[1]
        self.filters = self.key.split("|")[1:]

        initial = InitialArtifact(self.name)
        self.children.append(initial)
        prior = initial
        for i in range(0,len(self.filters)):
            key = "%s|%s" % (self.name, "|".join(self.filters[0:i+1]))
            fragment = Artifact(key, prior=prior)
            self.children.append(fragment)
            prior = fragment

class GlobDoc(Opuscule):
    """
    An Opuscule for handling glob patterns. Creates a FileOpuscule for each matched glob.
    """
    pass

class DexyJsonDoc(Opuscule):
    """
    An Opuscule which converts a .dexy file.
    """
    pass
