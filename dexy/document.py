from dexy.artifact import Artifact
from dexy.logger import log
import os

### @export "init"
class Document(object):
    def __init__(self, name_or_key, filters = []):
        self.name = name_or_key.split("|")[0]
        self.filters = name_or_key.split("|")[1:]
        self.filters += filters
        self.inputs = []
        self.artifacts = []
        self.use_all_inputs = False

### @export "key"
    def key(self):
        return "%s|%s" % (self.name, "|".join(self.filters))

### @export "inputs"
    def add_input(self, input_doc):
        if not input_doc in self.inputs:
            self.inputs.append(input_doc)

    def finalize_inputs(self, members_dict):
        if self.use_all_inputs:
            for doc in members_dict.values():
                if not doc.use_all_inputs: # this would create mutual dependency
                    self.add_input(doc)

### @export "steps"
    def next_handler_name(self):
        if self.at_last_step():
            return 'None'
        else:
            return self.filters[self.step]
    
    def next_handler_class(self):
        if not self.at_last_step():
            return self.controller.handlers[self.next_handler_name()]

    def at_last_step(self):
        return (len(self.filters) == self.step)

### @export "input-artifacts"
    def input_artifacts(self):
        input_artifacts = {}
        for input_doc in self.inputs:
            artifact = input_doc.artifacts[-1]
            input_artifacts[input_doc.key()] = artifact.dj_filename()
        return input_artifacts

### @export "create-initial-artifact"
    def create_initial_artifact(self):
        artifact_key = self.name
        artifact = Artifact.setup(self, artifact_key, None)
        artifact.ext = os.path.splitext(self.name)[1]
        artifact.data = open(self.name, "r").read()
        artifact.data_dict['1'] = artifact.data
        artifact.input_artifacts = self.input_artifacts()
        artifact.set_hashstring()
        artifact.generate()
        self.artifacts.append(artifact)
        return (artifact, artifact_key)

### @export "run"
    def run(self, controller):
        self.controller = controller
        self.step = 0
        
        artifact, artifact_key = self.create_initial_artifact()
        log.info("(step %s) %s -> %s" % (self.step, artifact_key, artifact.filename()))

        for f in self.filters:
            artifact_key += "|%s" % f
            self.step += 1
    
            HandlerClass = self.controller.handlers[f]
            h = HandlerClass.setup(
                self, 
                artifact_key,
                artifact, 
                self.next_handler_class()
            )
            
            artifact = h.generate_artifact()
            if not artifact:
                raise Exception("no artifact created!")
            self.artifacts.append(artifact)
            
            log.info("(step %s) %s -> %s" % (self.step, artifact_key, artifact.filename()))

        return self
