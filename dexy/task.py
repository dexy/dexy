from dexy.params import RunParams
import dexy.doc
import StringIO
import dexy.exceptions
import logging

class Task(object):
    def __init__(self, key, *children, **args):
        self.key = key
        self.children = list(children)
        self.args = args

        self.completed_children = {}

        self.state = 'new'

        self.post = args.get('post', self.post)
        self.pre = args.get('pre', self.pre)

        if args.has_key('runner') and args['runner']:
            self.runner = args['runner']
            self.setup()

    def pre(self, *args, **kw):
        pass

    def post(self, *args, **kw):
        pass

    STATE_TRANSITIONS = [
            ('new', 'setup'),
            ('setup', 'running'),
            ('running', 'complete')
            ]

    def transition(self, to_state):
        if (self.state, to_state) in self.STATE_TRANSITIONS:
            self.state = to_state
        else:
            raise dexy.exceptions.InvalidStateTransition("%s => %s" % (self.state, to_state))

    def __iter__(self):
        def next_task():
            if self.state == 'setup':
                self.transition('running')
                yield self.pre
                yield self
                yield self.post
                self.transition('complete')
            elif self.state == 'running':
                raise dexy.exceptions.CircularDependency
            elif self.state == 'complete':
                pass
            else:
                raise dexy.exceptions.UnexpectedState("%s in %s" % (self.state, self.key))

        return next_task()

    def __call__(self, *args, **kw):
        for child in self.children:
            for task in child:
                task(*args, **kw)

            self.completed_children[child.global_key()] = child
            self.completed_children.update(child.completed_children)

        self.run(*args, **kw)

    def setup(self):
        self.after_setup()

    def global_key(self):
        return "%s:%s" % (self.__class__.__name__, self.key)

    def completed_child_docs(self):
        return [c for c in self.completed_children.values() if isinstance(c, dexy.doc.Doc)]

    def after_setup(self):
        """
        Shared code that should always be run at end of setup process.
        """
        self.runner.register(self)
        self.transition('setup')

    def run(self, *args, **kw):
        pass

    def set_log(self):
        self.log = logging.getLogger(self.key)
        self.logstream = StringIO.StringIO()
        handler = logging.StreamHandler(self.logstream)
        self.log.addHandler(handler)
        self.log.setLevel(logging.DEBUG)

        try:
            self.log.addHandler(logging.getLogger('dexy').handlers[0])
        except IndexError:
            pass
