from dexy.utils import parse_json
from dexy.utils import parse_yaml
from dexy.utils import file_exists
from dexy.utils import defaults
import dexy.wrapper
import os

RENAME_PARAMS = {
        'artifactsdir' : 'artifacts_dir',
        'conf' : 'config_file',
        'dbalias' : 'db_alias',
        'dbfile' : 'db_file',
        'disabletests' : 'disable_tests',
        'dryrun' : 'dry_run',
        'excludealso' : 'exclude_also',
        'ignore' : 'ignore_nonzero_exit',
        'logfile' : 'log_file',
        'logformat' : 'log_format',
        'loglevel' : 'log_level',
        'logdir' : 'log_dir',
        'nocache' : 'dont_use_cache',
        'outputroot' : 'output_root'
        }

def default_config():
    wrapper = dexy.wrapper.Wrapper()
    conf = wrapper.__dict__.copy()

    for k in conf.keys():
        if not k in defaults.keys():
            del conf[k]

    reverse_rename = dict((v,k) for k, v in RENAME_PARAMS.iteritems())
    for k in conf.keys():
        renamed_key = reverse_rename.get(k, k)
        if renamed_key != k:
            conf[renamed_key] = conf[k]
            del conf[k]

    return conf

def rename_params(kwargs):
    renamed_args = {}
    for k, v in kwargs.iteritems():
        renamed_key = RENAME_PARAMS.get(k, k)
        renamed_args[renamed_key] = v
    return renamed_args

def skip_params(kwargs):
    ok_params = {}
    for k, v in kwargs.iteritems():
        if k in defaults.keys():
            ok_params[k] = v
    return ok_params

def config_args(modargs):
    cliargs = modargs.get("__cli_options", {})
    kwargs = modargs.copy()

    config_file = modargs.get('conf', dexy.utils.defaults['config_file'])

    # Update from config file
    if file_exists(config_file):
        with open(config_file, "rb") as f:
            if config_file.endswith(".conf"):
                try:
                    conf_args = parse_yaml(f.read())
                except dexy.exceptions.UserFeedback as yaml_exception:
                    try:
                        conf_args = parse_json(f.read())
                    except dexy.exceptions.UserFeedback as json_exception:
                        print "--------------------------------------------------"
                        print "Tried to parse YAML:"
                        print yaml_exception
                        print "--------------------------------------------------"
                        print "Tried to parse JSON:"
                        print json_exception
                        print "--------------------------------------------------"
                        raise dexy.exceptions.UserFeedback("Unable to parse config file '%s' as YAML or as JSON." % config_file)

            elif config_file.endswith(".yaml"):
                conf_args = parse_yaml(f.read())
            elif config_file.endswith(".json"):
                conf_args = parse_json(f.read())
            else:
                raise dexy.exceptions.UserFeedback("Don't know how to load config from '%s'" % config_file)

            kwargs.update(conf_args)

    if cliargs: # cliargs may be False
        for k in cliargs.keys(): kwargs[k] = modargs[k]

    # TODO allow updating from env variables, e.g. DEXY_ARTIFACTS_DIR

    return kwargs

def import_extra_plugins(kwargs):
    if kwargs.get('plugins'):
        for import_target in kwargs.get('plugins').split():
            print "loading plugin", import_target
            # TODO look for files
            try:
                __import__(import_target)
            except ImportError as e:
                # try looking for file
                if os.path.exists(import_target):
                    import imp
                    imp.load_source("custom_plugins", import_target)
                else:
                    raise e

def init_wrapper(modargs):
    kwargs = config_args(modargs)
    import_extra_plugins(kwargs)
    kwargs = rename_params(kwargs)
    kwargs = skip_params(kwargs)
    return dexy.wrapper.Wrapper(**kwargs)

def template_text(
        alias=None
    ):
    template = dexy.template.Template.aliases[alias]
    for batch in template.dexy():
        man_doc_key = 'doc:dexy.rst|jinja|rst2man'
        if man_doc_key in batch.lookup_table:
            man_doc = batch.nodes[man_doc_key].output_data().storage.data_file()

            command = "man %s" % man_doc
            import subprocess
            proc = subprocess.Popen(
                       command,
                       shell=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT
                   )
            stdout, stderr = proc.communicate()
            return stdout
        else:
            return "no example found"
