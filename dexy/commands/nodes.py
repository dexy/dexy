from dexy.node import Node
from dexy.commands.utils import dummy_wrapper
import inspect

def nodes_command(
        alias = False # Print docs for a particular node type.
        ):
    """
    Prints available node types and their settings.
    """

    if not alias:
        # list all plugins
        for alias in sorted(Node.plugins):
            print(alias)

        print("For info on a particular node type run `dexy nodes -alias doc`")
    else:
        print_node_info(alias)


def print_node_info(alias):
    print(alias)

    _, settings = Node.plugins[alias]

    instance = Node.create_instance(alias, "dummy", dummy_wrapper())
    instance.update_settings(settings)

    print('')
    print(instance.setting('help'))
    print('')

    if len(instance._instance_settings) > 2:
        print('Settings:')

    for k in sorted(instance._instance_settings):
        if k in ('aliases', 'help',):
            continue

        tup = instance._instance_settings[k]
        print("    %s" % k)

        for line in inspect.cleandoc(tup[0]).splitlines():
            print("        %s" % line)

        print("        default value: %s" % tup[1])
        print('')
