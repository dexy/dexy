from dexy.artifact import FilterArtifact
from dexy.artifact import InitialArtifact
from dexy.artifact import InitialVirtualArtifact
from dexy.exceptions import *
from dexy.task import Task
import dexy.filter
import os

class Doc(Task):
    """
    A single file + 0 or more filters applied to that file.
    """
    @classmethod
    def filter_class_for_alias(klass, alias):
        if alias == '':
            raise BlankAlias
        else:
            return dexy.filter.Filter.aliases[alias]

    def output(self):
        """
        Returns a reference to the output_data Data object generated by the final filter.
        """
        return self.final_artifact.output_data

    ### @export "setup"
    def setup(self):
        ### @export "setup-parse-key"
        self.name = self.key.split("|")[0]
        self.filters = self.key.split("|")[1:]
        self.artifacts = []

        ### @export "setup-initial-artifact"
        if os.path.exists(self.name):
            initial = InitialArtifact(self.name)
        else:
            initial = InitialVirtualArtifact(self.name)

        initial.args = self.args
        initial.name = self.name
        initial.prior = None
        self.children.append(initial)
        self.artifacts.append(initial)
        self.final_artifact = initial

        ### @export "setup-filter-artifacts"
        prior = initial
        for i in range(0,len(self.filters)):
            filters = self.filters[0:i+1]
            key = "%s|%s" % (self.name, "|".join(filters))

            fragment = FilterArtifact(key)
            fragment.args = self.args
            fragment.doc = self
            fragment.filter_alias = filters[-1]
            fragment.doc_filepath = self.name
            fragment.prior = prior

            try:
                fragment.filter_class = self.filter_class_for_alias(filters[-1])
            except BlankAlias:
                raise UserFeedback("You have a trailing | or you have 2 | symbols together in your specification for %s" % self.key)

            if not fragment.filter_class.is_active():
                raise InactiveFilter

            fragment.next_filter_alias = None
            fragment.next_filter_class = None
            fragment.next_filter_name = None

            if i+1 < len(self.filters):
                next_filter_alias = self.filters[i+1]
                fragment.next_filter_alias = next_filter_alias
                fragment.next_filter_class = self.filter_class_for_alias(next_filter_alias)
                fragment.next_filter_name = fragment.next_filter_class.__name__

            self.children.append(fragment)
            self.artifacts.append(fragment)
            self.final_artifact = fragment
            self.metadata = fragment.metadata

            # update prior so this fragment will be the 'prior' in next loop
            prior = fragment

    def run(self, runner):
        self.runner = runner
        self.runner.append(self)

class WalkDoc(Task):
    """
    Parent class for docs which walk Dexy project directories.

    Shares code for skipping dexy directories.
    """
    def walk(self, start, exclude_at_root, exclude_everywhere):
        for dirpath, dirnames, filenames in os.walk(start):
            process_me = True

            if dirpath == ".":
                for x in exclude_at_root:
                    if x in dirnames:
                        dirnames.remove(x)

            for filename in filenames:
                yield(dirpath, filename)

import fnmatch
class PatternDoc(WalkDoc):
    """
    A doc which takes a file matching pattern and creates individual Doc objects for all files that match the pattern.
    """
    def setup(self):
        self.file_pattern = self.key.split("|")[0]
        self.filter_aliases = self.key.split("|")[1:]

        exclude_at_root = ['artifacts', 'logs', 'output', 'output-long']
        exclude_everywhere = ['.git']

        for dirpath, filename in self.walk(".", exclude_at_root, exclude_everywhere):
            raw_filepath = os.path.join(dirpath, filename)
            filepath = os.path.normpath(raw_filepath)
            if fnmatch.fnmatch(filepath, self.file_pattern):

                if len(self.filter_aliases) > 0:
                    doc_key = "%s|%s" % (filepath, "|".join(self.filter_aliases))
                else:
                    doc_key = filepath

                doc = Doc(doc_key)
                self.children.append(doc)

class DexyConfigDoc(Task):
    pass

class DexyJsonConfigDoc(Task):
    """
    A doc which parses old .dexy files and creates Doc objects as needed. Intended for backwards compatibility.
    """
    def setup(self):
        config = dexy.config.load_config()