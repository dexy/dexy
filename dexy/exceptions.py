import platform

class NonzeroExit(Exception):
    pass

class InactiveFilter(Exception):
    pass

class InvalidStateTransition(Exception):
    pass

class UnexpectedState(Exception):
    pass

class CircularDependency(Exception):
    pass

class InternalDexyProblem(Exception):
    def __init__(self, message):
        self.message = """\nOops! You may have found a bug in Dexy.
        The developer would really appreciate if you copy and paste this entire message
        and the Traceback above it into a bug report at http://dexy.tenderapp.com.
        Your version of Dexy is %s
        Your platform is %s\n""" % ("0.0.0", platform.system())
        self.message += message

    def __str__(self):
        return self.message

class UserFeedback(Exception):
    pass

class BlankAlias(Exception):
    pass
