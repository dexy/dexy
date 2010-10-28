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
import pydot
import re
import simplejson as json
import sys

class Controller(object):
    def __init__(self):
        self.handler_dirs = None
        self.time_log_filename = "times.csv"
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
        
        self.handler_dirs = []
        for d in [install_dir, cur_dir]:
            h = os.path.abspath(os.path.join(d, 'handlers'))
            if os.path.exists(h) and not h in self.handler_dirs:
                self.handler_dirs.append(h)

### @export "find-handlers"
    def find_handlers(self):
        if not self.handler_dirs:
            self.init_handler_dirs()

        log.info("Automatically loading all handlers found in %s" % ", ".join(self.handler_dirs))
        
        handlers = {}

        for a in DexyHandler.ALIASES:
            handlers[a] = DexyHandler

        for d in self.handler_dirs:
            for f in os.listdir(d):
                if f.endswith(".py") and f not in ["base.py", "__init__.py"]:
                    basename = f.replace(".py", "")
                    module = "handlers.%s" % basename
                    try:
                        __import__(module)
                    except ImportError as e:
                        log.warn("handlers defined in %s will not be available: %s" % (module, e))
                    
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
            config_file_path_elements = [rel_to] + path_elements[0:i] + [".dexy"]
            config_filename = os.path.join(*config_file_path_elements)
            if os.path.exists(config_filename):
                log.info("loading config %s" % config_filename)
                config_file = open(config_filename, "r")
                json_dict = json.load(config_file)
                config_dict.update(json_dict)
                log.info("config dict %s" % config_dict)
        self.json_dict = config_dict
        self.path = path_to_dir

### @export "process-config"
    def process_config(self):
        def parse_doc(input_directive, args = {}):
            try:
                a, b = input_directive.popitem()
                input_directive = a
                args = b
            except AttributeError:
                # if we are here, input_directive is not a dict
                pass
            
            tokens = input_directive.split("|")
            glob_string = os.path.join(self.path, tokens[0])
            filters = tokens[1:]
            docs = []

            regex = fnmatch.translate(glob_string).replace(".*", "(.*)")
            matcher = re.compile(regex)

            for f in glob.glob(glob_string):
                if not os.path.isfile(f):
                    continue
                if f.endswith("__init__.py"):
                    continue
                
                create = True

                inputs = []
                if args.has_key('inputs'):
                    if isinstance(args['inputs'], str):
                        raise Exception("this input should be an array, not a string: %s" % args['inputs'])
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
                    if isinstance(args['ifinput'], str):
                        ifinputs = (args['ifinput'])
                    else:
                        ifinputs = args['ifinput']
                    
                    for s in ifinputs:
                        ifinput = s.replace("%", rootname)
                        input_docs = parse_doc(ifinput)
                        for input_doc in input_docs:
                            inputs.append(input_doc.key())

                    if len(input_docs) == 0:
                        create = False

                if args.has_key('ifnoinput'):
                    ifinput = args['ifnoinput'].replace("%", rootname)
                    input_docs = parse_doc(ifinput)

                    if len(input_docs) > 0:
                        create = False
                
                if args.has_key('except'):
                    if re.search(args['except'], f):
                        create = False

                if create:
                    # Filters can either be included in the name (separated by |)...
                    doc = Document(f, filters)
                    doc.args = args
                    # ...or they may be listed explicitly.
                    if args.has_key('filters'):
                        doc.filters += args['filters']

                    # Once all filters have been added, the key will be correct
                    # so the doc can be added to the members list.
                    doc = add_to_members_list(doc)
                    
                    is_partial = os.path.basename(doc.name).startswith("_")
                    if args.has_key('allinputs') and not is_partial:
                        doc.use_all_inputs = True
                    for i in inputs:
                        input_doc = self.members[i]
                        doc.add_input(input_doc)
                    
                    docs.append(doc)
            return docs

        def get_pos(member):
            key = member.key()
            return self.members.keys().index(key)

        def add_to_members_list(member):
            key = member.key()
            if not self.members.has_key(key):
                self.members[key] = member
            return self.members[key]

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
  
### @export "dot"
    def dot(self):
        log.info(self.depends)
        return pydot.graph_from_edges(self.depends)

### @export "run"
    def run(self):
        return [doc.run(self) for doc in self.members.values()]

### @export "setup-and-run"
    def setup_and_run(self, path_to_dir):
        if not hasattr(self, 'artifacts_dir'):
            self.artifacts_dir = 'artifacts'
        self.register_handlers()
        self.load_config(path_to_dir)
        self.process_config()
        docs = self.run()
        self.close_logger()
        return docs
