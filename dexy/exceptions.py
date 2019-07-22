from cashew.exceptions import InactivePlugin
from cashew.exceptions import UserFeedback
from dexy.version import DEXY_VERSION
import dexy.utils
import platform

class NoFilterOutput(UserFeedback):
    pass

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
