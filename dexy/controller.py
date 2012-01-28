from dexy.constants import Constants
from dexy.topsort import CycleError
from dexy.topsort import topsort
from dexy.utils import get_log
from dexy.utils import save_batch_info
from ordereddict import OrderedDict
import copy
import dexy
import dexy.document
import dexy.introspect
import fnmatch
import glob
import json
import os
import re
import sre_constants
import time

class Controller(object):
    def __init__(self, args={}):
        self.args = args # arguments from command line
        self.config = {} # config to be processed from .dexy files
        self.docs = []
        self.timing = []

        self.batch_start_time = None
        self.batch_finish_time = None
        self.batch_elapsed_time = None

        # Set up logging
        if args.has_key("logsdir") and args.has_key("logfile"):
            self.log = get_log("dexy.controller", args['logsdir'], args['logfile'])
        else:
            self.log = Constants.NULL_LOGGER

        # Set up db
        if args.has_key('dbclass') and args.has_key("logsdir") and args.has_key("dbfile"):
            self.db = dexy.utils.get_db(self.args['dbclass'], logsdir=self.args['logsdir'], dbfile=args['dbfile'])
        else:
            self.db = None

        # List of directories that reporters use, these will not be processed by dexy
        self.reports_dirs = dexy.introspect.reports_dirs(self.log)

        # list of artifact classes - if nothing else uses this then move
        # it into the if statement below and don't cache it

        self.artifact_classes = dexy.introspect.artifact_classes(self.log)
        if args.has_key('artifactclass'):
            if self.artifact_classes.has_key(args['artifactclass']):
                self.artifact_class = self.artifact_classes[args['artifactclass']]
            else:
                raise Exception("Artifact class name %s not found in %s" % (args['artifactclass'], ",".join(self.artifact_classes.keys())))

    def run(self):
        """
        This does all the work.
        """
        self.batch_start_time = time.time()
        start = self.batch_start_time

        self.log.debug("populating Document class filter list")
        dexy.document.Document.filter_list = dexy.introspect.filters(self.log)
        self.timing.append(("populate-filter-list", time.time() - start))
        start = time.time()

        self.log.debug("loading config...")
        self.load_config()
        self.log.debug("finished loading config.")
        self.timing.append(("load-config", time.time() - start))
        start = time.time()

        self.log.debug("processing config, populating document list...")
        self.process_config()
        self.log.debug("finished processing config.")
        self.timing.append(("process-config", time.time() - start))
        start = time.time()

        if not self.args['dryrun']:
            self.docs = [doc.run() for doc in self.docs]
        self.timing.append(("run-docs", time.time() - start))

        self.batch_finish_time = time.time()
        self.batch_elapsed_time = self.batch_finish_time - self.batch_start_time

        self.log.debug("persisting batch info...")
        self.persist()
        self.log.debug("finished persisting.")
        self.log.debug("finished processing. elapsed time %s" % self.batch_elapsed_time)

    def persist(self):
        """
        Persists the database. Saves some information about this batch in a
        JSON file (for use by reporters or for debugging).
        """
        self.db.persist()
        save_batch_info(self.batch_id, self.batch_info(), self.args['logsdir'])

    def batch_info(self):
        """
        Dict of info to save
        """
        return {
            "id" : self.batch_id,
            "config" : self.config,
            "args" : self.args,
            "docs" : dict((doc.key(), doc.document_info()) for doc in self.docs),
            "start_time" : self.batch_start_time,
            "finish_time" : self.batch_finish_time,
            "elapsed" : self.batch_elapsed_time,
            "timing" : self.timing
            }

    def config_for_directory(self, path):
        """
        Determine the config applicable within a directory by looking in every
        parent directory (up as far as the dexy project root) for config files
        and combining them, such that subdirectories override parents.
        """
        global_args = {}
        config_dict = {}
        config_file = self.args['config']

        path_elements = path.split(os.sep)

        for i in range(0,len(path_elements)+1):
            config_path = os.path.join(*(path_elements[0:i] + [config_file]))
            config_files = glob.glob(config_path)

            for f in config_files:
                self.log.info("loading config file %s" % f)

                with open(f, "r") as cf:
                    try:
                        json_dict = json.load(cf)
                    except ValueError as e:
                        msg = "Your config file %s has invalid JSON\n%s" % (f, e.message)
                        raise Exception(msg)

                if json_dict.has_key("$reset"):
                    # Reset the config, i.e. ignore everything from parent
                    # directories, just use this directory's config in json_dict
                    config_dict = json_dict
                else:
                    for k in config_dict.keys():
                        propagate_virtual = config_dict[k].has_key('propagate') and config_dict[k]['propagate']
                        if k.startswith("@") and not json_dict.has_key(k) and not propagate_virtual:
                            # don't propagate virtual files
                            del config_dict[k]

                    # Combine any config in this dir with parent dir config.
                    config_dict.update(json_dict)

                if json_dict.has_key("$globals"):
                    global_args.update(json_dict["$globals"])

        config_dict['$globals'] = global_args
        return config_dict

    def load_config(self):
        """
        This method determines which subdirectories will be included in the
        dexy batch and populates the config dict for each of them.
        """
        if self.args['recurse']:

            # Figure out which directories need to be skipped
            exclude_at_root = Constants.EXCLUDE_DIRS_ROOT + self.reports_dirs + [self.args['artifactsdir'], self.args['logsdir']]
            self.log.debug("project root excluded directories %s" % ", ".join(exclude_at_root))

            exclude_everywhere = Constants.EXCLUDE_DIRS_ALL_LEVELS
            self.log.debug("directories excluded at all levels %s" % ", ".join(exclude_everywhere))

            for dirpath, dirnames, filenames in os.walk(self.args['directory']):
                # Figure out if we should process this directory and recurse
                # into its children. Start with process_dir = True
                process_dir = True

                # Remove any children we don't want to recurse into.
                if dirpath == ".":
                    for x in exclude_at_root:
                        if x in dirnames:
                            dirnames.remove(x)
                for x in exclude_everywhere:
                    if x in dirnames:
                        dirnames.remove(x)

                # Look for a .nodexy file
                if os.path.isfile(os.path.join(dirpath, '.nodexy')):
                    # If we find one...
                    self.log.info(".nodexy file found in %s" % dirpath)

                    # ...remove all child dirs from processing...
                    for i in xrange(len(dirnames)):
                        dirnames.pop()

                    # ...and skip this directory.
                    process_dir = False

                # Check if we match any excludes specified on the command line
                args_exclude = self.args['exclude']
                if isinstance(args_exclude, str):
                    args_exclude = args_exclude.split()
                for pattern in args_exclude:
                    for d in dirnames:
                        m1 = re.match(pattern, d)
                        m2 = re.match("./%s" % pattern, d)
                        m3 = re.match("%s/" % pattern, d)
                        m4 = re.match("./%s/" % pattern, d)
                        if m1 or m2 or m3 or m4:
                            dirnames.remove(d)

                if process_dir:
                    self.config[dirpath] = self.config_for_directory(dirpath)
            else:
                # Not recursing
                dirpath = self.args['directory']
                self.config[dirpath] = self.config_for_directory(dirpath)

    def process_config(self):
        """
        Processes a populated config dict, identifies files to be processed,
        creates Document objects for each, links dependencies and finally does
        topological sort to establish order of batch run.
        """

        # Define the parse_doc nested function which we will call recursively.
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
                virtual = True

                dangerous = not args.has_key('contents')
                if dangerous and not self.args['danger']:
                    raise Exception("""
                    You are attempting to access a remote file %s.
                    You must enable --danger flag to do this.""" % glob_string)
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
                        self.log.warn("document %s|%s disabled" % (f, "|".join(filters)))

                inputs = []
                if args.has_key('inputs'):
                    if isinstance(args['inputs'], str):
                        raise Exception("inputs for %s should be an array" % f)
                    for i in args['inputs']:
                        # Create document objects for input patterns (just in this directory)
                        for doc in parse_doc(path, i):
                            inputs.append(doc.key())


                m = matcher.match(f)
                if m and len(m.groups()) > 0:
                    rootname = matcher.match(f).group(1)

                # The 'ifinput' directive says that if an input exists matching
                # the specified pattern, we should create this document and it
                # will depend on the specified input.
                if args.has_key('ifinput'):
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
                        self.log.warn("skipping %s for %s as it matches except pattern %s" % (
                                f,
                                input_directive,
                                args['except']
                                ))
                        create = False

                if create:
                    doc = dexy.document.Document()
                    doc.set_controller(self)

                    # Filters can either be included in the name...
                    doc.set_name_and_filters(f, filters)
                    # ...or they may be listed explicitly.
                    if args.has_key('filters'):
                        doc.filters += args['filters']

                    doc.setup_log() # After name has been set
                    doc.virtual = virtual

                    key = doc.key()
                    self.log.debug("creating doc %s for glob %s" % (key, glob_string))

                    if self.members.has_key(key):
                        self.log.debug("found existing key %s" % key)
                        doc = self.members[key]
                    else:
                        self.log.debug("no existing key %s" % key)

                    if args.has_key('priority'):
                        doc.priority = args['priority']
                        del args['priority']

                    doc.args.update(args)

                    if args.has_key('allinputs'):
                        doc.use_all_inputs = args['allinputs']

                    if args.has_key('inputs'):
                        doc.input_args = copy.copy(args['inputs'])
                        doc.input_keys = []

                    for i in inputs:
                        doc.add_input_key(i)

                    self.members[key] = doc
                    docs.append(doc) # docs is a local list of docs

            return docs # end of parse_doc nested function

        def get_pos(member):
            key = member.key()
            return self.members.keys().index(key)

        def depend(parent, child):
            self.depends.append((get_pos(child), get_pos(parent)))

        # The real processing starts here.
        self.members = OrderedDict()
        self.depends = []

        self.batch_id = self.db.next_batch_id()
        print "batch id is", self.batch_id

        for path, config in self.config.iteritems():
            ### @export "features-global-args-1"
            if config.has_key("$globals"):
                global_args = config["$globals"]
            else:
                global_args = {}

            if self.args.has_key('globals'):
                global_args.update(self.args['globals'])

            for k, v in config.iteritems():
                local_args = global_args.copy()
                local_args.update(v)
                for kg in global_args.keys():
                    if local_args.has_key(kg):
                        if isinstance(local_args[kg], dict):
                            local_args[kg].update(global_args[kg])
                parse_doc(path, k, local_args)
            ### @end

        # Determine dependencies
        total_dependencies = 0
        for doc in self.members.values():
            doc.finalize_inputs(self.members)
            total_dependencies += len(doc.inputs)
            for input_doc in doc.inputs:
                depend(doc, input_doc)

        if len(self.args['run']) > 0:
            # Only run the specified document, and its dependencies.
            new_members = OrderedDict()
            new_depends = []

            def new_get_pos(member):
                key = member.key()
                return new_members.keys().index(key)

            def new_depend(parent, child):
                new_depends.append((new_get_pos(child), new_get_pos(parent)))

            def parse_new_document(d):
                new_members[d.key()] = d
                for input_doc in d.inputs:
                    if not input_doc.key() in new_members.keys():
                        new_members[input_doc.key()] = input_doc
                    new_depend(d, input_doc)
                    parse_new_document(input_doc)

            run_key = self.args['run']
            doc = self.members[run_key]
            parse_new_document(doc)

            print "limiting members list to %s and its dependencies, %s/%s documents will be run" % (doc.key(), len(new_members), len(self.members))
            self.members = new_members
            self.depends = new_depends

        num_members = len(self.members)
        if num_members > 0:
            dep_ratio = float(total_dependencies)/num_members
        else:
            dep_ratio = None

        print "sorting %s documents into run order, there are %s total dependencies" % (num_members, total_dependencies)
        if dep_ratio:
            print "ratio of dependencies to documents is %0.1f" % (dep_ratio)
            if dep_ratio > 10:
                print "if you are experiencing performance problems:"
                print "call dexy with -dryrun and inspect logs/batch-XXXX.json to debug dependencies"
                print "consider using -strictinherit or reducing your use of 'allinputs' "

        try:
            self.log.debug("Beginning topological sort...")
            topsort_ordering = topsort(self.depends)
            self.log.debug("Topological sort completed successfully.")
        except CycleError as e:
            print "There are circular dependencies!"
            answer, num_parents, children = e.args
            for child, parents in children.items():
                for parent in parents:
                    print "%s depends on %s" % (self.members.keys()[parent], self.members.keys()[child])
            raise e

        docs_without_dependencies = frozenset(range(len(self.members))) - frozenset(topsort_ordering)
        self.ordering = topsort_ordering + list(docs_without_dependencies)

        for i in self.ordering:
            key = self.members.keys()[i]
            self.docs.append(self.members[key])
