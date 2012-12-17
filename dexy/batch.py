from dexy.notify import Notify
import time

class Batch(object):
    def __init__(self, wrapper, batch_id=None):
        self.wrapper = wrapper

        if batch_id:
            self.load(batch_id)
        else:
            self.new()

    def filters_used(self):
        filters = set()
        for doc in self.docs():
            filters = filters.union([f for f in doc.filters if not f.startswith("-")])
        return filters

    def load(self, batch_id):
        """
        Loads a previously run batch into memory.
        """
        self.batch_id = batch_id

    def save(self):
        """
        Persist a batch's info to disk (for later retrieval by load).
        """
        pass

    def add_doc(self, new_doc):
        self.lookup_table[new_doc.key_with_class()] = new_doc
        self.notifier.subscribe("newchild", new_doc.handle_newchild)

    def new(self):
        """
        Sets up defaults for a new batch.
        """
        self.state = 'new'
        self.notifier = Notify(self)
        self.batch_id = self.wrapper.db.next_batch_id()
        self.previous_batch_id = self.wrapper.db.calculate_previous_batch_id(self.batch_id)

    def create_lookup_table(self):
        """
        Creates a lookup table assuming the tree has already been populated.
        """
        self.lookup_table = dict((t.key_with_class(), t) for t in self.tree)

    def load_ast(self, ast):
        self.ast = ast
        self.tree, created_tasks = self.ast.walk()

        self.lookup_table = {}
        for task in created_tasks.values():
            self.lookup_table[task.key_with_class()] = task
            self.notifier.subscribe("newchild", task.handle_newchild)

    def run(self, target=None):
        self.start_time = time.time()

        if target:
            # Look for identical target in root-level nodes
            nodes = [n for n in self.tree if n.key == target]
            
            if not nodes:
                # Look for similar target in root-level nodes
                nodes = [n for n in self.tree if n.key.startswith(target)]

            if not nodes:
                # Look for identical target anywhere in tree
                nodes = [n for n in self.lookup_table.values() if n.key == target]
                # TODO sort nodes..

            if not nodes:
                # Look for similar target anywhere in tree
                nodes = [n for n in self.lookup_table.values() if n.key.startswith(target)]
                # TODO sort nodes..

        else:
            nodes = self.tree

        self.state = 'populating'

        for node in nodes:
            for task in node:
                task()

        self.state = 'settingup'

        for node in nodes:
            for task in node:
                task()

        self.state = 'running'

        for node in nodes:
            for task in node:
                task()

        self.state = 'complete'

        self.end_time = time.time()

    def elapsed(self):
        return self.end_time - self.start_time

    # Methods for accessing lists of tasks
    def task(self, task_key):
        if not ":" in task_key:
            task_key = "Doc:%s" % task_key
        return self.lookup_table[task_key]

    def tasks(self):
        return self.lookup_table.values()

    def docs(self):
        return [v for k, v in self.lookup_table.iteritems() if k.startswith("Doc:")]

    def doc_names(self):
        return [doc.name for doc in self.docs()]

    def tasks_by_elapsed(self, n=10):
        return sorted(self.lookup_table.values(), key=lambda task: hasattr(task, 'doc') and task.elapsed or None, reverse=True)[0:n]
