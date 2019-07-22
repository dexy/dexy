import dexy.filter
import inspect

def fcmds_command(
        alias=False # Only print commands defined by this alias.
        ):
    """
    Prints a list of available filter commands.
    """
    if alias:
        filter_instances = [dexy.filter.Filter.create_instance(alias)]
    else:
        filter_instances = dexy.filter.Filter

    for filter_instance in filter_instances:
        cmds = filter_instance.filter_commands()
        if cmds:
            print("filter alias:", filter_instance.alias)
            for command_name in sorted(cmds):
                docs = inspect.getdoc(cmds[command_name])
                if docs:
                    doc = docs.splitlines()[0]
                    print("    %s   # %s" % (command_name, doc))
                else:
                    print("    %s" % command_name)
            print('')

def fcmd_command(
        alias=None, # The alias of the filter which defines the custom command
        cmd=None, # The name of the command to run
        **kwargs # Additional arguments to be passed to the command
        ):
    """
    Run a filter command.
    """
    filter_instance = dexy.filter.Filter.create_instance(alias)
    cmd_name = "docmd_%s" % cmd

    if not cmd_name in dir(filter_instance):
        msg = "%s is not a valid command. There is no method %s defined in %s"
        msgargs = (cmd, cmd_name, filter_instance.__class__.__name__)
        raise dexy.exceptions.UserFeedback(msg % msgargs)

    else:
        instance_method = getattr(filter_instance, cmd_name)
        # TODO use try/catch instead of inspect.ismethod
        if inspect.ismethod(instance_method):
            try:
                instance_method.__func__(filter_instance, **kwargs)
            except TypeError as e:
                print(e.message)
                print(inspect.getargspec(instance_method.__func__))
                print(inspect.getdoc(instance_method.__func__))
                raise

        else:
            msg = "expected %s to be an instance method of %s"
            msgargs = (cmd_name, filter_instance.__class__.__name__)
            raise dexy.exceptions.InternalDexyProblem(msg % msgargs)
