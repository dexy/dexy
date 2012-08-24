from dexy.exceptions import *
import logging
import StringIO
from dexy.params import RunParams

### @export "class"
class Task(object):
    ### @export "init"
    def __init__(self, key, *children, **args):
        self.args = args
        self.children = list(children)
        self.key = key

        self.state = 'new'

        self.post = args.get('post', self.post)
        self.pre = args.get('pre', self.pre)
        self.run_params = args.get('params', RunParams())

        self.setup()

    ### @export "setup"
    def setup(self):
        pass

    ### @export "pre-post"
    def pre(self, *args, **kw):
        pass

    def post(self, *args, **kw):
        pass

    ### @export "state"
    STATE_TRANSITIONS = [
            ('new', 'running'),
            ('running', 'complete')
            ]

    def transition(self, to_state):
        if (self.state, to_state) in self.STATE_TRANSITIONS:
            self.state = to_state
        else:
            raise InvalidStateTransition("%s => %s" % (self.state, to_state))

    ### @export "iter"
    def __iter__(self):
        def next_task():
            if self.state == 'new':
                self.transition('running')
                yield self.pre
                yield self
                yield self.post
                self.transition('complete')
            elif self.state == 'running':
                raise CircularDependency
            elif self.state == 'complete':
                pass
            else:
                raise UnexpectedState(self.state)

        return next_task()

    ### @export "call"
    def __call__(self, *args, **kw):
        for child in self.children:
            for task in child:
                task(*args, **kw)

        self.run(*args, **kw)

    ### @export "run"
    def run(self, *args, **kw):
        pass

    ### @export "set-log"
    def set_log(self, log_name=None):
        """
        Sets up a logger for this task which writes to a StringIO instance
        stored as a logstream attribute. Intended for testing. For actual
        logging create a file-based logger and set this as task's log attribute
        before running.
        """
        log = self.args.get('log')

        if log:
            self.log = log
        else:
            if log_name:
                self.log = logging.getLogger(log_name)
            elif hasattr(self, 'key'):
                self.log = logging.getLogger(self.key)
            else:
                self.log = logging.getLogger('log')

            self.logstream = StringIO.StringIO()
            handler = logging.StreamHandler(self.logstream)
            self.log.addHandler(handler)
            self.log.setLevel(logging.DEBUG)
