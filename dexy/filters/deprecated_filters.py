from dexy.dexy_filter import DexyFilter
import shutil

class DeprecatedCopyFilter(DexyFilter):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['cp']
    BINARY = True
    FINAL = True

    def process(self):
        print self.artifact.key, "- The 'cp' filter is deprecated. This filter is no longer necessary, you can remove '|cp' from your specification and the file will still be copied."
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())
