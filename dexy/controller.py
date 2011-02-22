try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from dexy.document import Document
from dexy.handler import DexyHandler
from dexy.logger import log
from dexy.topological_sort import topological_sort
from inspect import isclass
import csv
import fnmatch
import glob
import os
import re
import json
import sys

class Controller(object):
    def __init__(self, logs_dir='logs'):
        self.handler_dirs = None
        self.time_log_filename = os.path.join(logs_dir, "times.csv")
        self.init_time_logger()

### @export "init-time-logger"
    def init_time_logger(self):
        write_header = not os.path.exists(self.time_log_filename)
        self.time_log_file = open(self.time_log_filename, "a")
        self.csv_writer = csv.writer(self.time_log_file)
        if write_header:
            self.csv_writer.writerow([
                "artifact_key",
                "hashstring",
                "doc_key",
                "handler_class",
                "method",
                "start",
                "finish",
                "elapsed"
            ])

### @export "close-logger"
    def close_logger(self):
        self.time_log_file.close()

### @export "log"
    def log_time(self, row):
        self.csv_writer.writerow(row)

### @export "init-handler-dirs"
    def init_handler_dirs(self):
        install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cur_dir = os.curdir
        sys.path.append(cur_dir)
        
        self.handler_dirs = []
        # Need to give local directory (in which we place custom per-project filters)
        # a different name or else Python can't see modules in that dir.
        # This handler/filter switching is confusing, should be improved.
        h1 = os.path.abspath(os.path.join(install_dir, 'handlers'))
        h2 = os.path.abspath(os.path.join(cur_dir, 'filters'))

        for h in [h1, h2]:
            if os.path.exists(h) and not h in self.handler_dirs:
                self.handler_dirs.append(h)

### @export "find-handlers"
    def find_handlers(self):
        if not self.handler_dirs:
            self.init_handler_dirs()

        log.info("Automatically loading all filters found in %s" % ", ".join(self.handler_dirs))
        
        handlers = {}

        for a in DexyHandler.ALIASES:
            handlers[a] = DexyHandler

        for d in self.handler_dirs:
            for f in os.listdir(d):
                if f.endswith(".py") and f not in ["base.py", "__init__.py"]:
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
                        log.warn("filters defined in %s are not available: %s" % (module, e))
                    
                    if not sys.modules.has_key(module):
                        continue

                    mod = sys.modules[module]

                    for k in dir(mod):
                        klass = mod.__dict__[k]
                        if isclass(klass) and not (klass == DexyHandler) and issubclass(klass, DexyHandler) and klass.ALIASES:
                            for a in klass.ALIASES:
                                if handlers.has_key(a):
                                    raise Exception("duplicate key %s called from %s" % (a, k))
                                handlers[a] = klass
                                log.info("registered alias %s for class %s" % (a, k))
        return handlers

### @export "register-handlers"
    def register_handlers(self):
        self.handlers = self.find_handlers()

### @export "load-config"
    def load_config(self, path_to_dir, rel_to=os.curdir):
        relative_path = os.path.relpath(path_to_dir, rel_to)
        path_elements = relative_path.split(os.sep)
        config_dict = {}
        for i in range(0,len(path_elements)+1):
            config_file_path_elements = [rel_to] + path_elements[0:i] + [self.config_file]
            config_filename = os.path.join(*config_file_path_elements)
            if os.path.exists(config_filename):
                log.info("loading config %s" % config_filename)
                config_file = open(config_filename, "r")
                try:
                    json_dict = json.load(config_file)
                except ValueError as e:
                    raise Exception("""Your config file %s has invalid JSON. Details: %s""" %
                                    (config_filename, e.message))
                config_dict.update(json_dict)
                log.info("config dict %s" % config_dict)
        self.json_dict = config_dict
        self.path = path_to_dir

### @export "process-config"
    def process_config(self):
        def parse_doc(input_directive, args = {}):
            # If a specification is nested in a dependency, then input_directive
            # may be a dict. If so, split it into parts before continuing.
            try:
                a, b = input_directive.popitem()
                input_directive = a
                args = b
            except AttributeError:
                pass
            
            tokens = input_directive.split("|")
            glob_string = os.path.join(self.path, tokens[0])
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
            in_proj_root = (self.path == '.')
            not_wildcard = glob_string.find("*") < 0

            if nofiles and virtual:
                files = [glob_string]
            
            for f in files:
                create = True

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
                        for doc in parse_doc(i):
                            inputs.append(doc.key())
                m = matcher.match(f)
                if m and len(m.groups()) > 0:
                    rootname = matcher.match(f).group(1)
                
                # The 'ifinput' directive says that if an input exists matching
                # the specified pattern, we should create this document and it
                # will depend on the specified input.
                if args.has_key('ifinput'):
                    log.debug(f)
                    if isinstance(args['ifinput'], str) or isinstance(args['ifinput'], unicode):
                        ifinputs = [args['ifinput']]
                    else:
                        log.debug("treating input %s as iterable. class: %s" % (
                            args['ifinput'], args['ifinput'].__class__.__name__))
                        ifinputs = args['ifinput']
                    
                    for s in ifinputs:
                        log.debug("evaluating ifinput %s" % s)
                        ifinput = s.replace("%", rootname)
                        log.debug("evaluating ifinput %s" % ifinput)
                        input_docs = parse_doc(ifinput, {})
                        for input_doc in input_docs:
                            log.debug(input_doc.key())
                            inputs.append(input_doc.key())

                    if len(input_docs) == 0:
                        create = False

                if args.has_key('ifnoinput'):
                    ifinput = args['ifnoinput'].replace("%", rootname)
                    input_docs = parse_doc(ifinput, {})

                    if len(input_docs) > 0:
                        create = False
                
                if args.has_key('except'):
                    if re.search(args['except'], f):
                        create = False
                
                if create:
                    # Filters can either be included in the name...
                    doc = Document(f, filters)
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

                    is_partial = os.path.basename(doc.name).startswith("_")
                    if args.has_key('allinputs') and not is_partial:
                        doc.use_all_inputs = True
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
        for k, v in self.json_dict.items():
            parse_doc(k, v)
        
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

### @export "run"
    def run(self):
        return [doc.run(self) for doc in self.members.values()]

### @export "setup-and-run"
    def setup_and_run(self, path_to_dir):
        if not hasattr(self, 'artifacts_dir'):
            self.artifacts_dir = 'artifacts'
        if not hasattr(self, 'config_file'):
            self.config_file = '.dexy'
        self.register_handlers()
        self.load_config(path_to_dir)
        self.process_config()
        docs = self.run()
        self.close_logger()
        return docs
