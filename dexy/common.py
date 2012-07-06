import os

class Common(object):
    """
    Temporary class for common artifact/opuscule methods.
    """
    def temp_filename(self, ext):
        return "%s.work%s" % (self.hashstring, ext)

    def canonical_dir(self, ignore_args = False):
        return os.path.dirname(self.name)

    def canonical_basename(self, ignore_args = False):
        return os.path.basename(self.canonical_filename(ignore_args))

    def abs_filepath(self):
        return os.path.abspath(self.filepath())

    def filename(self):
        """
        The filename where artifact content is stored, based on the hashstring.
        """
        if not hasattr(self, 'ext'):
            raise Exception("artifact %s has no ext" % self.key)
        return "%s%s" % (self.hashstring, self.ext)

    def filepath(self):
        """
        Full path (including artifacts dir location) to location where artifact content is stored.
        """
        return os.path.join(self.artifacts_dir, self.filename())

    def canonical_filename(self, ignore_args = False):
        fn = os.path.splitext(self.key.split("|")[0])[0]

        if self.args.has_key('canonical-name') and not ignore_args:
            parent_dir = os.path.dirname(fn)
            return os.path.join(parent_dir, self.args['canonical-name'])
        elif self.args.has_key('postfix') and not ignore_args:
            return "%s%s%s" % (fn, self.ext, self.args['postfix'])
        elif self.alias():
            return "%s%s%s" % (fn, self.alias(), self.ext)
        else:
            return "%s%s" % (fn, self.ext)

    def alias(self):
        """
        Whether this artifact includes an alias.
        """
        aliases = [k for k in self.key.split("|") if k.startswith("-")]
        if len(aliases) > 0:
            return aliases[0]

    def temp_dir(self):
        return os.path.join(self.artifacts_dir, self.hashstring)
