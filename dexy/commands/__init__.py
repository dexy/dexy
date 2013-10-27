### "imports"
from dexy.version import DEXY_VERSION
from modargs import args
import cashew.exceptions
import dexy.exceptions
import dexy.wrapper
import logging
import os
import sys
import warnings
import inspect

### "load-plugins"
import dexy.load_plugins

### "import-all-commands"
from dexy.commands.cite import cite_command
from dexy.commands.conf import conf_command
from dexy.commands.dirs import cleanup_command
from dexy.commands.dirs import reset_command
from dexy.commands.dirs import setup_command
from dexy.commands.fcmds import fcmd_command
from dexy.commands.fcmds import fcmds_command
from dexy.commands.filters import filter_command
from dexy.commands.filters import filters_command
from dexy.commands.grep import grep_command
from dexy.commands.info import info_command
from dexy.commands.it import dexy_command
from dexy.commands.it import it_command
from dexy.commands.it import targets_command
from dexy.commands.reporters import reporters_command
from dexy.commands.reporters import reporters_command as reports_command
from dexy.commands.serve import serve_command
from dexy.commands.templates import gen_command
from dexy.commands.templates import template_command
from dexy.commands.templates import templates_command

### "modargs-settings"
dexy_default_cmd = 'dexy'
dexy_cmd_mod = sys.modules[__name__]
prog = 'dexy'
### @end

def run():
    capture_warnings()
    parse_and_run_cmd(*resolve_argv())

def capture_warnings():
    """
    Capture deprecation messages and other irrelevant warnings in whatever way
    is appropriate to the dexy version.
    """
    if hasattr(logging, 'captureWarnings'):
        logging.captureWarnings(True)
    else:
        warnings.filterwarnings("ignore",category=Warning)

def resolve_argv():
    """
    Do some processing of the user-provided arguments in argv before they go to
    modargs so we can support commands defined in plugins.
    """
    only_one_arg = (len(sys.argv) == 1)
    second_arg_is_known_cmd = not only_one_arg and \
        sys.argv[1] in args.available_commands(dexy_cmd_mod)
    second_arg_is_option = not only_one_arg and \
        sys.argv[1].startswith("-")

    if only_one_arg or second_arg_is_known_cmd or second_arg_is_option:
        return sys.argv[1:], dexy_cmd_mod, dexy_default_cmd

    else:
        cmd, subcmd, cmd_mod = resolve_plugin_command(sys.argv[1])
        default_cmd = cmd.default_cmd or cmd.namespace
        return [subcmd] + sys.argv[2:], cmd_mod, default_cmd

def resolve_plugin_command(raw_command_name):
    """
    Take a command name like viewer:run and return the command method and
    module object.
    """
    if ":" in raw_command_name:
        alias, subcommand = raw_command_name.split(":")
    else:
        alias, subcommand = raw_command_name, ''

    try:
        cmd = dexy.plugin.Command.create_instance(alias)
    except cashew.exceptions.NoPlugin:
        msg = """No command '%s' available.
        Run `dexy help` to see list of available commands."""
        msgargs = (alias)
        sys.stderr.write(inspect.cleandoc(msg) % msgargs)
        sys.stderr.write(os.linesep)
        sys.exit(1)

    mod_name = cmd.__module__
    cmd_mod = args.load_module(mod_name)

    return cmd, subcommand, cmd_mod

def parse_and_run_cmd(argv, module, default_command):
    try:
        args.parse_and_run_command(argv, module, default_command)
    except (dexy.exceptions.UserFeedback, cashew.exceptions.UserFeedback) as e:
        msg = """Oops, there's a problem running your command.
        Here is some more information:"""
        sys.stderr.write(inspect.cleandoc(msg))
        sys.stderr.write(os.linesep)

        err_msg = str(e)
        if err_msg:
            sys.stderr.write("'%s'" % str(e))
        else:
            sys.stderr.write("Sorry, can't get text of error message.")

        sys.stderr.write(os.linesep)
        sys.exit(1)

    except KeyboardInterrupt:
        sys.stderr.write("stopping...")
        sys.stderr.write(os.linesep)
        sys.exit(1)

def help_command(
        example=False, # Whether to run any live examples, if available.
        filters=False, # Whether to print the list of available dexy filters.
        reports=False, # Whether to print the list of available dexy reports.
        f=False, # If a filter alias is specified, help for that filter is printed.
        on=False # The dexy command to get help on.
    ):
    # TODO list plugin commands too when -on not specified
    if f:
        filter_command(f, example)
    elif filters:
        filters_command()
    elif reports:
        reports_command()
    else:
        args.help_command(prog, dexy_cmd_mod, dexy_default_cmd, on)

def help_text(on=False):
    return args.help_text(prog, dexy_cmd_mod, dexy_default_cmd, on)

def version_command():
    """
    Print the version number of dexy.
    """
    print "%s version %s" % (prog, DEXY_VERSION)
