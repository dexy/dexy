from dexy.document import Document
from dexy.handler import DexyHandler
from dexy.reporter import Reporter
from dexy.topological_sort import topological_sort
from inspect import isclass
from ordereddict import OrderedDict
import fnmatch
import glob
import json
import logging
import os
import re
import sre_constants
import sys

class Controller(object):
    def __init__(self):
        self.config = {}
        self.install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if not hasattr(self, 'log'):
            self.log = logging.getLogger('dexy')

    def find_reporters(self):
        d1 = os.path.abspath(os.path.join(self.install_dir, 'reporters'))
        d2 = os.path.abspath(os.path.join(os.curdir, 'reporters'))

        if d1 == d2:
            reporter_dirs = [d1]
        else:
            reporter_dirs = [d1,d2]

        reporters = []

        for d in reporter_dirs:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.endswith(".py") and f not in ["base.py", "__init__.py"]:
                        self.log.info("Loading reporters in %s" % os.path.join(d, f))
                        basename = f.replace(".py", "")
                        module = "reporters.%s" % basename

                        try:
                            __import__(module)
                        except ImportError as e:
                            self.log.warn("reporters defined in %s are not available: %s" % (module, e))

                        if not sys.modules.has_key(module):
                            continue

                        mod = sys.modules[module]

                        for k in dir(mod):
                            klass = mod.__dict__[k]
                            if isclass(klass) and not (klass == Reporter) and issubclass(klass, Reporter):
                                reporters.append(klass)
        self.reports_dirs = [r.REPORTS_DIR for r in reporters]
        return reporters

    def find_handlers(self):
        sys.path.append(os.curdir)

        handler_dirs = []
        # Need to give local directory (in which we place custom per-project filters)
        # a different name or else Python can't see modules in that dir.
        # This handler/filter switching is confusing, should be improved.
        h1 = os.path.abspath(os.path.join(self.install_dir, 'handlers'))
        h2 = os.path.abspath(os.path.join(os.curdir, 'filters'))

        for h in [h1, h2]:
            if os.path.exists(h) and not h in handler_dirs:
                handler_dirs.append(h)

        handlers = {}

        for a in DexyHandler.ALIASES:
            handlers[a] = DexyHandler

        for d in handler_dirs:
            self.log.info("Automatically loading all filters found in %s" % d)
            for f in os.listdir(d):
                if f.endswith(".py") and f not in ["base.py", "__init__.py"]:
                    self.log.info("Loading filters in %s" % os.path.join(d, f))
                    basename = f.replace(".py", "")
                    if d.endswith('handlers'):
                        module = "handlers.%s" % basename
                    elif d.endswith('filters'):
                        module = "filters.%s" % basename
                    else:
                        raise Exception(d)

                    try:
                        __import__(module)
                    except ImportError as e:
                        self.log.warn("filters defined in %s are not available: %s" % (module, e))

                    if not sys.modules.has_key(module):
                        continue

                    mod = sys.modules[module]

                    for k in dir(mod):
                        klass = mod.__dict__[k]
                        if isclass(klass) and not (klass == DexyHandler) and issubclass(klass, DexyHandler) and klass.ALIASES:
                            for a in klass.ALIASES:
                                if handlers.has_key(a):
                                    raise Exception("duplicate key %s called from %s in %s" % (a, k, f))
                                handlers[a] = klass
                                self.log.info("registered alias %s for class %s" % (a, k))
            self.log.info("...finished loading filters from %s" % d)
        return handlers

    def register_handlers(self):
        self.handlers = self.find_handlers()

    def register_reporters(self):
        self.reporters = self.find_reporters()

    def load_config(self, path_to_dir, rel_to=os.curdir):
        # This looks in every parent directory for a config file and combines them.
        relative_path = os.path.relpath(path_to_dir, rel_to)
        path_elements = relative_path.split(os.sep)
        config_dict = {}
        for i in range(0,len(path_elements)+1):
            config_file_path_elements = [rel_to] + path_elements[0:i] + [self.config_file]
            config_filename = os.path.join(*config_file_path_elements)
            if os.path.exists(config_filename):
                self.log.info("loading config %s" % config_filename)
                config_file = open(config_filename, "r")
                try:
                    json_dict = json.load(config_file)
                except ValueError as e:
                    raise Exception("""Your config file %s has invalid JSON. Details: %s""" %
                                    (config_filename, e.message))
                config_dict.update(json_dict)
        self.config[path_to_dir] = config_dict

    def process_config(self):
        def parse_doc(path, input_directive, args = {}):
            # If a specification is nested in a dependency, then input_directive
            # may be a dict. If so, split it into parts before continuing.
            try:
                a, b = input_directive.popitem()
                input_directive = a
                args = b
            except AttributeError:
                pass

            tokens = input_directive.split("|")
            if "/" in tokens[0]:
                raise Exception("paths not allowed in tokens: %s" % tokens[0])
            if path == '.':
                glob_string = tokens[0]
            else:
                glob_string = os.path.join(re.sub("^\./", "", path), tokens[0])
            filters = tokens[1:]

            docs = []

            # virtual document
            if re.search("@", glob_string):
                # TODO some virtual files are local, not remote. test on
                # presence of 'url' or something more appropriate.
                virtual = True
                if not self.allow_remote:
                    raise Exception("""You are attempting to access a remote file.
                                    You must enable --dangerous mode to do this.
                                    Please check Dexy help and call the dexy
                                    command again.""")
                glob_string = glob_string.replace("@", "")
            else:
                virtual = False

            regex = fnmatch.translate(glob_string).replace(".*", "(.*)")
            matcher = re.compile(regex)

            files = glob.glob(glob_string)

            nofiles = len(files) == 0

            if nofiles and virtual:
                files = [glob_string]

            for f in files:
                create = True
                if not virtual:
                    if os.path.isdir(f):
                        create = False

                if args.has_key('disabled'):
                    if args['disabled']:
                        create = False
                        print "document %s disabled" % f

                inputs = []
                if args.has_key('inputs'):
                    if isinstance(args['inputs'], str):
                        raise Exception("""this input should be an array,
                                        not a string: %s""" % args['inputs'])
                    for i in args['inputs']:
                        for doc in parse_doc(path, i):
                            inputs.append(doc.key())
                m = matcher.match(f)
                if m and len(m.groups()) > 0:
                    rootname = matcher.match(f).group(1)

                # The 'ifinput' directive says that if an input exists matching
                # the specified pattern, we should create this document and it
                # will depend on the specified input.
                if args.has_key('ifinput'):
                    self.log.debug(f)
                    if isinstance(args['ifinput'], str) or isinstance(args['ifinput'], unicode):
                        ifinputs = [args['ifinput']]
                    else:
                        self.log.debug("treating input %s as iterable. class: %s" % (
                            args['ifinput'], args['ifinput'].__class__.__name__))
                        ifinputs = args['ifinput']

                    for s in ifinputs:
                        self.log.debug("evaluating ifinput %s" % s)
                        ifinput = s.replace("%", rootname)
                        self.log.debug("evaluating ifinput %s" % ifinput)
                        input_docs = parse_doc(path, ifinput, {})
                        for input_doc in input_docs:
                            self.log.debug(input_doc.key())
                            inputs.append(input_doc.key())

                    if len(input_docs) == 0:
                        create = False

                if args.has_key('ifnoinput'):
                    ifinput = args['ifnoinput'].replace("%", rootname)
                    input_docs = parse_doc(path, ifinput, {})

                    if len(input_docs) > 0:
                        create = False

                if args.has_key('except'):
                    try:
                        except_re = re.compile(args['except'])
                    except sre_constants.error as e:
                        raise Exception("""You passed 'except' value of %s.
Please pass a valid Python-style regular expression for
'except', NOT a glob-style matcher. Error message from
re.compile: %s""" % (args['except'], e))
                    if re.match(except_re, f):
                        print "skipping %s as it matches except pattern %s" % (f, args['except'])
                        create = False

                if create:
                    # Filters can either be included in the name...
                    doc = Document(self.artifact_class, f, filters)
                    doc.args = args
                    # ...or they may be listed explicitly.
                    if args.has_key('filters'):
                        doc.filters += args['filters']

                    # Here we are assuming that if we get a key with blank args
                    # this should not override a previous key. A key which does
                    # have args should override any previous key.
                    key = doc.key()
                    if len(args) == 0:
                        if self.members.has_key(key):
                            doc = self.members[key]
                        else:
                            self.members[key] = doc
                    else:
                        self.members[key] = doc

                    doc.use_all_inputs = args.has_key('allinputs')
                    for i in inputs:
                        doc.add_input_key(i)


                    docs.append(doc)
            return docs

        def get_pos(member):
            key = member.key()
            return self.members.keys().index(key)

        def depend(parent, child):
            self.depends.append((get_pos(child), get_pos(parent)))

        self.members = OrderedDict()
        self.depends = []

        # Create Document objects for all docs.
        self.log.debug("About to process config\n")
        self.log.debug(self.config)
        for path, config in self.config.items():
            for k, v in config.items():
                parse_doc(path, k, v)

        # Determine dependencies
        for doc in self.members.values():
            doc.finalize_inputs(self.members)
            for input_doc in doc.inputs:
                depend(doc, input_doc)

        ordering = topological_sort(range(len(self.members)), self.depends)
        ordered_members = OrderedDict()
        for i in ordering:
            key = self.members.keys()[i]
            ordered_members[key] = self.members[key]
        self.members = ordered_members

    def run(self):
        return [doc.run(self) for doc in self.members.values()]

    def setup_and_run(self):
        if not hasattr(self, 'config_file'):
            self.config_file = '.dexy'
        self.register_handlers()
        self.register_reporters()
        self.process_config()
        self.docs = self.run()
        return self.docs
