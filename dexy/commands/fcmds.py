import dexy.filter
import os
import inspect

def fcmds_command(
        alias=False # alias of filter to list commands for, otherwise all commands are printed
        ):
    """
    Returns a list of available filter commands (fcmds) defined by the specified alias.

    These commands can then be run using the fcmd command.
    """
    def filter_commands(filter_instance):
        cmds = []
        for m in dir(filter_instance):
            if m.startswith("docmd_"):
                cmds.append(m.replace("docmd_", ""))
        return sorted(cmds)

    if alias:
        filter_instances = [dexy.filter.Filter.create_instance(alias)]
    else:
        filter_instances = dexy.filter.Filter

    for filter_instance in filter_instances:
        cmds = filter_commands(filter_instance)
        if cmds:
            print filter_instance.alias
            for cmd in cmds:
                print "  %s" % cmd

def fcmd_command(
        alias=None, # The alias of the filter which defines the custom command
        cmd=None, # The name of the command to run
        help=False, # If true, just print docstring rather than running command
        **kwargs # Additional arguments to be passed to the command
        ):
    """
    Run a command defined in a dexy filter.
    """
    filter_instance = dexy.filter.Filter.create_instance(alias)

    cmd_name = "docmd_%s" % cmd

    if not cmd_name in dir(filter_instance):
        msg = "%s is not a valid command. There is no method %s defined in %s"
        msgargs = (cmd, cmd_name, filter_instance.__class__.__name__)
        raise dexy.exceptions.UserFeedback(msg % msgargs)
    else:
        instance_method = getattr(filter_instance, cmd_name)
        if inspect.ismethod(instance_method):
            if help:
                print inspect.getdoc(instance_method.__func__)
            else:
                try:
                    instance_method.__func__(filter_instance, **kwargs)
                except TypeError as e:
                    print e.message
                    print inspect.getargspec(instance_method.__func__)
                    print inspect.getdoc(instance_method.__func__)
                    raise e

        else:
            msg = "expected %s to be an instance method of %s"
            msgargs = (cmd_name, filter_instance.__class__.__name__)
            raise dexy.exceptions.InternalDexyProblem(msg % msgargs)
