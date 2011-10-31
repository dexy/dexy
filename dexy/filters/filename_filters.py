from dexy.dexy_filter import DexyFilter
import os
import re

class FilenameFilter(DexyFilter):
    """Generate random filenames to track provenance of data."""
    ALIASES = ['fn']

    def process_text(self, input_text):
        # TODO this should not match more than two dashes
        for m in re.finditer("dexy--(\S+)\.([a-z]+)", input_text):
            local_key = m.groups()[0]
            ext = m.groups()[1]

            parent_dir = os.path.dirname(self.artifact.name)
            key = os.path.join(parent_dir, local_key)

            key_with_ext = "%s.%s" % (key, ext)
            key_with_ext_with_dexy = "%s|dexy" % key_with_ext

            if key_with_ext in self.artifact.inputs().keys():
                artifact = self.artifact.inputs()[key_with_ext]
                self.log.debug("[fn] existing key %s in artifact %s links to file %s" %
                          (key_with_ext, self.artifact.key, artifact.filename()))
            elif key_with_ext_with_dexy in self.artifact.inputs().keys():
                artifact = self.artifact.inputs()[key_with_ext_with_dexy]
                self.log.debug("[fn] existing key %s in artifact %s links to existing file %s" %
                          (key_with_ext, self.artifact.key, artifact.filename()))
            else:
                self.log.debug("[fn] could not find match for %s" % (key_with_ext))
                artifact = self.artifact.add_additional_artifact(key_with_ext, ext)
                self.log.debug("[fn] created new artifact %s ; links to new file %s" %
                          (key_with_ext, artifact.filename()))

            input_text = input_text.replace(m.group(), artifact.filename())

        # Hack to replace __ with -- in case we want to document how to use this
        # filter, we can't use -- because this will be acted upon.
        for m in re.finditer("dexy__(.+)\.([a-z]+)", input_text):
            key = m.groups()[0]
            ext = m.groups()[1]
            replacement_key = "dexy--%s.%s" % (key, ext)
            input_text = input_text.replace(m.group(), replacement_key)

        return input_text
