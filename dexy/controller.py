from dexy.constants import Constants
from dexy.topological_sort import topological_sort
from dexy.utils import get_log
from dexy.utils import save_batch_info
from ordereddict import OrderedDict
import dexy
import dexy.document
import dexy.introspect
import fnmatch
import glob
import json
import os
import pprint
import re
import sre_constants

class Controller(object):
    def __init__(self, args={}):
        self.args = args # arguments from command line
        self.config = {} # config to be processed from .dexy files
        self.docs = []

        # Set up logging
        if args.has_key("logsdir") and args.has_key("logfile"):
            self.log = get_log("dexy.controller", args['logsdir'], args['logfile'])
        else:
            self.log = Constants.NULL_LOGGER

        # Set up db
        if args.has_key('dbclass') and args.has_key("logsdir") and args.has_key("dbfile"):
            self.db = dexy.utils.get_db(self.args['dbclass'], logsdir=self.args['logsdir'], dbfile=args['dbfile'])
        else:
            self.db = {}

        # List of directories that reporters use, these will not be processed by dexy
        self.reports_dirs = dexy.introspect.reports_dirs(self.log)

        # list of artifact classes - if nothing else uses this then move
        # it into the if statement below and don't cache it

        self.artifact_classes = dexy.introspect.artifact_classes(self.log)
        if args.has_key('artifactclass'):
            self.artifact_class = self.artifact_classes[args['artifactclass']]

    def run(self):
        """
        This does all the work.
        """
        self.load_config()
        self.process_config()
        self.docs = [doc.run() for doc in self.members.values()]
        self.persist()

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
            "config" : self.config,
            "args" : self.args,
            "docs" : dict((doc.key(), doc.document_info()) for doc in self.docs)
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
                        if k.startswith("@") and not json_dict.has_key(k):
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
            self.log.debug("project root excluded directories %s" % ",".join(exclude_at_root))

            exclude_everywhere = Constants.EXCLUDE_DIRS_ALL_LEVELS
            self.log.debug("directories excluded at all levels %s" % ",".join(exclude_everywhere))

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
                    for d in dirnames:
                        # ...remove all child dirs from processing...
                        dirnames.remove(d)
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
                        print "document %s|%s disabled" % (f, "|".join(filters))

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
                        print "skipping %s for %s as it matches except pattern %s" % (
                                f,
                                input_directive,
                                args['except']
                                )
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

                    # Here we are assuming that if we get a key with blank args
                    # this should not override a previous key. A key which does
                    # have args should override any previous key.
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

                    if len(args) > 0:
                        self.log.debug("args: %s" % args)
                        doc.args = args
                        doc.use_all_inputs = args.has_key('allinputs')
                        for i in inputs:
                            doc.add_input_key(i)

                    if not hasattr(doc, 'args'):
                        doc.args = args

                    self.members[key] = doc
                    docs.append(doc) # just a local list

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

        self.log.debug("About to process config")
        for l in pprint.pformat(self.config).split():
            self.log.debug(l)

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
        for doc in self.members.values():
            doc.finalize_inputs(self.members)
            for input_doc in doc.inputs:
                depend(doc, input_doc)

        ordering, leftover_graph_items = topological_sort(range(len(self.members)), self.depends)
        if leftover_graph_items and not ordering:
            # circular references! print debugging help before stopping
            for doc, depends_on in leftover_graph_items:
                print self.members.values()[doc].key(), "depends on"
                for i in depends_on:
                    print "   ", self.members.values()[i].key()
                print
            print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
            print "The above dependencies were not able to be resolved.\n\n"
            raise Exception("There are circular references, can't do topological sort!")

        ordered_members = OrderedDict()
        for i in ordering:
            key = self.members.keys()[i]
            ordered_members[key] = self.members[key]
        self.members = ordered_members
