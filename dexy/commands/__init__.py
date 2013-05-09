from dexy.version import DEXY_VERSION
from modargs import args
import dexy.exceptions
import dexy.wrapper
import logging
import os
import sys
import warnings

# ensure all built-in plugins are registered
import dexy.filters
import dexy.reporters
import dexy.parsers

# import all commands
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
from dexy.commands.reporters import reporters_command
from dexy.commands.reporters import reporters_command as reports_command
from dexy.commands.serve import serve_command
from dexy.commands.templates import gen_command
from dexy.commands.templates import template_command
from dexy.commands.templates import templates_command

from dexy.commands.watch import AVAILABLE as WATCH_COMMAND_AVAILABLE
if WATCH_COMMAND_AVAILABLE:
    from dexy.commands.watch import watch_command

DEFAULT_COMMAND = 'dexy'
MOD = sys.modules[__name__]
PROG = 'dexy'
S = "   "

def resolve_argv():
    if len(sys.argv) == 1 or (sys.argv[1] in args.available_commands(MOD)) or sys.argv[1].startswith("-"):
        command_plus_args = sys.argv[1:]
        mod = MOD
        default_command = DEFAULT_COMMAND

    else:
        if ":" in sys.argv[1]:
            alias, subcommand = sys.argv[1].split(":")
        else:
            alias, subcommand = sys.argv[1], ''

        try:
            cmd = dexy.plugin.Command.create_instance(alias)
        except dexy.exceptions.NoPlugin:
            msg = "No command '%s' available. Run `dexy help` to see list of available commands.\n"
            msgargs = (alias)
            sys.stderr.write(msg % msgargs)
            sys.exit(1)

        mod_name = cmd.__module__
        mod = args.load_module(mod_name)
    
        if cmd.DEFAULT_COMMAND:
            default_command = cmd.DEFAULT_COMMAND
        else:
            default_command = cmd.NAMESPACE

        command_plus_args = [subcommand] + sys.argv[2:]

    return command_plus_args, mod, default_command

def parse_and_run_cmd(argv, module, default_command):
    try:
        args.parse_and_run_command(argv, module, default_command)
    except dexy.exceptions.UserFeedback as e:
        sys.stderr.write("Oops, there's a problem running your command. Here is the error message:" + os.linesep)
        err_msg = str(e)
        if err_msg:
            sys.stderr.write("'%s'" % str(e))
        else:
            sys.stderr.write("Sorry, can't get text of error message.")
        sys.stderr.write(os.linesep)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.stderr.write("stopping...")
        sys.exit(1)

def run():
    if hasattr(logging, 'captureWarnings'):
        logging.captureWarnings(True)
    else:
        warnings.filterwarnings("ignore",category=Warning)

    parse_and_run_cmd(*resolve_argv())

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
        args.help_command(PROG, MOD, DEFAULT_COMMAND, on)

def help_text(on=False):
    return args.help_text(PROG, MOD, DEFAULT_COMMAND, on)

def version_command():
    """Print the current version."""
    print "%s version %s" % (PROG, DEXY_VERSION)
