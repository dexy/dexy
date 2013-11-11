from dexy.filter import Filter
from dexy.doc import Doc
from dexy.wrapper import Wrapper
import logging

def dummy_wrapper():
    wrapper = Wrapper()
    wrapper.log = logging.getLogger('dexy')
    wrapper.log.addHandler(logging.NullHandler)
    return wrapper

def env_command():
    """
    Prints list of template plugins.
    """
    f = Filter.create_instance("template")
    f.doc = Doc('dummy', dummy_wrapper())
    env = f.run_plugins()

    for k in sorted(env):
        try:
            helpstring, value = env[k]
        except Exception:
            print k
            raise

        print "%s: %s" % (k, helpstring,)
