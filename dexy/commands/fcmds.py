import dexy.filter
import os
import inspect

def fcmds_command(alias=False):
    """
    Returns a list of available filter commands (fcmds) defined by the specified alias.

    These commands can then be run using the fcmd command.
    """

    def filter_class_commands(filter_alias):
        filter_class = dexy.filter.Filter.aliases[filter_alias]
        cmds = []
        for m in dir(filter_class):
            if m.startswith("docmd_"):
                cmds.append(m.replace("docmd_", ""))
        return sorted(cmds)

    filters_dict = dexy.filter.Filter.aliases
    if (not alias) or (not alias in filters_dict):
        print "Aliases with filter commands defined are:"
        for a in sorted(filters_dict):
            cmds = filter_class_commands(a)
            if len(cmds) > 0:
                print a
    else:
        print "Filter commands defined for %s:" % alias
        cmds = filter_class_commands(alias)
        print os.linesep.join(cmds)

def fcmd_command(
        alias=None, # The alias of the filter which defines the custom command
        cmd=None, # The name of the command to run
        help=False, # If true, just print docstring rather than running command
        **kwargs # Additional arguments to be passed to the command
        ):
    """
    Run a command defined in a dexy filter.
    """
    filter_class = dexy.filter.Filter.aliases.get(alias)

    if not filter_class:
        raise dexy.exceptions.UserFeedback("%s is not a valid alias" % alias)

    cmd_name = "docmd_%s" % cmd

    if not filter_class.__dict__.has_key(cmd_name):
        raise dexy.exceptions.UserFeedback("%s is not a valid command. There is no method %s defined in %s" % (cmd, cmd_name, filter_class.__name__))
    else:
        class_method = filter_class.__dict__[cmd_name]
        if type(class_method) == classmethod:
            if help:
                print inspect.getdoc(class_method.__func__)
            else:
                try:
                    class_method.__func__(filter_class, **kwargs)
                except TypeError as e:
                    print e.message
                    print inspect.getargspec(class_method.__func__)
                    print inspect.getdoc(class_method.__func__)
                    raise e

        else:
            raise dexy.exceptions.InternalDexyProblem("expected %s to be a classmethod of %s" % (cmd_name, filter_class.__name__))

