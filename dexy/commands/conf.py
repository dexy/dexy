from dexy.commands.utils import default_config
from dexy.utils import defaults
from dexy.utils import file_exists
import dexy.exceptions
import inspect
import json
import os
import yaml

def conf_command(
        conf=defaults['config_file'], # name of config file to write to
        p=False # whether to print to stdout rather than write to file
        ):
    """
    Write a config file containing dexy's defaults.
    """
    if file_exists(conf) and not p:
        print(inspect.cleandoc("""Config file %s already exists,
        will print conf to stdout instead...""" % conf))
        p = True

    config = default_config()

    # Can't specify config file name in config file.
    del config['conf']

    yaml_help = inspect.cleandoc("""# YAML config file for dexy.
        # You can delete any lines you don't wish to customize.
        # Options are same as command line options,
        # for more info run 'dexy help -on dexy'.
        """)

    if p:
        print(yaml.dump(config, default_flow_style=False))
    else:
        with open(conf, "w") as f:
            if conf.endswith(".yaml") or conf.endswith(".conf"):
                f.write(yaml_help)
                f.write(os.linesep)
                f.write(yaml.dump(config, default_flow_style=False))
            elif conf.endswith(".json"):
                json.dump(config, f, sort_keys=True, indent=4)
            else:
                msg = "Don't know how to write config file '%s'"
                raise dexy.exceptions.UserFeedback(msg % conf)

        print("Config file has been written to '%s'" % conf)
