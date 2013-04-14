from dexy.version import DEXY_VERSION
import dexy.utils
import platform

class UserFeedback(Exception):
    pass

class NoPlugin(UserFeedback):
    pass

class NoFilterOutput(UserFeedback):
    pass

class InactiveFilter(UserFeedback):
    def __init__(self, filter_alias_or_instance):
        from dexy.utils import s
        if isinstance(filter_alias_or_instance, basestring):
            msg = """You are trying to use a filter '%s' which isn't active.
            Some additional software may need to be installed first."""
            self.message = s(msg % filter_alias_or_instance)
        else:
            self.message = "You are trying to use a filter '%s' which isn't active." % filter_alias_or_instance.alias
            executable = filter_alias_or_instance.setting('executable')
            if executable:
                self.message += " The software '%s' is required." % executable
            else:
                self.message += " Some additional software may need to be installed first."

class CircularDependency(UserFeedback):
    pass

class BlankAlias(UserFeedback):
    pass

class InvalidStateTransition(Exception):
    pass

class UnexpectedState(Exception):
    pass

class InternalDexyProblem(Exception):
    def __init__(self, message):
        self.message = dexy.utils.s("""
        Oops! You may have found a bug in Dexy.
        The developer would really appreciate if you copy and paste this entire message
        and the Traceback above it into an email and send to info@dexy.it
        Your version of Dexy is %s
        Your platform is %s""" % (DEXY_VERSION, platform.system()))
        self.message += "\n"
        self.message += message

    def __str__(self):
        return self.message

class DeprecatedException(InternalDexyProblem):
    pass

class TemplateException(InternalDexyProblem):
    pass
