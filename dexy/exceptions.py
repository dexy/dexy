from dexy.version import DEXY_VERSION
import platform
import dexy.utils

class UserFeedback(Exception):
    pass

class NoPlugin(UserFeedback):
    pass

class NoFilterOutput(UserFeedback):
    pass

class InactiveFilter(UserFeedback):
    def __init__(self, filter_alias):
        self.message = dexy.utils.s("""
        You are trying to use a filter '%s' which isn't active.
        Some additional software may need to be installed first.
        """ % filter_alias)

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
