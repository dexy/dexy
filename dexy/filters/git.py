from dexy.exceptions import UserFeedback, InternalDexyProblem
from dexy.filter import DexyFilter
import os
import tempfile
import json

try:
    import pygit2
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

def repo_from_path(path):
    """
    Initializes a pygit Repository instance from a local repo at 'path'
    """
    repo = pygit2.init_repository(path, False)
    if repo.is_empty:
        raise UserFeedback("no git repository was found at '%s'" % path)
    return repo, None

def repo_from_url(url, remote_name="origin"):
    """
    Initializes a pygit Repository instance from a remote repo at 'url'
    """
    tempdir = tempfile.mkdtemp() # TODO move to .dexy/persistent/tempdir
    repo = pygit2.init_repository(tempdir, False)
    remote = repo.create_remote(remote_name, url)
    remote.fetch()
    return repo, remote

def generate_commit_info(commit):
    # Currently this is diffing with nothing, so the 'diff' is a full printout
    # of the current contents of the repo.
    diff = commit.tree.diff_to_tree()

    patches = []
    for i, patch in enumerate(diff):
        patches.append({
            'old-file-path' : patch.old_file_path,
            'new-file-path' : patch.new_file_path,
            'hunks' : [ { 
                'old-start' : hunk.old_start,
                'old-lines' : hunk.old_lines,
                'new-start' : hunk.new_start,
                'new-lines' : hunk.new_lines,
                'lines' : hunk.lines
                } for hunk in patch.hunks]
            })

    commit_info = {
            'author-name' : commit.author.name,
            'author-email' : commit.author.email,
            'message' : commit.message.strip(),
            'hex' : commit.hex,
            'patch' : diff.patch.encode('ascii', 'ignore'),
            'patches' : json.dumps(patches).encode('ascii', 'ignore')
            }

    return commit_info

class GitBase(DexyFilter):
    """
    Base class for various git-related filters.
    """
    aliases = []
    _settings = {
            'reference' : ("The reference to use.", None),
            'revision' : ("The revision to use, see 'man gitrevisions'.", None),
            'url-prefixes' : ("""Tuple of strings which mean the specified repo
                should be treated as a URL.""", ("http", "git"))
            }

    def is_active(self):
        return AVAILABLE

    def is_url(self, input_text):
        """
        Should the input text be treated as the URL of a remote git repo?
        """
        return input_text.startswith(self.setting('url-prefixes'))

    def reference(self, repo):
        if self.setting('reference'):
            return repo.lookup_reference(self.setting('reference'))
        else:
            refs = repo.listall_references()
            return repo.lookup_reference(refs[0])

    def revision(self, repo):
        if self.setting('revision'):
            return repo.revparse_single(self.setting('revision'))

    def work(self, repo, remote, ref):
        return "do stuff here in subclass"

    def process_text(self, input_text):
        if self.is_url(input_text):
            repo, remote = repo_from_url(input_text)
        else:
            repo, remote = repo_from_path(input_text)

        ref = self.reference(repo)

        # TODO capture GitError class
        return self.work(repo, remote, ref)

class GitBaseKeyValue(GitBase):
    """
    A filter using key-value storage to manage content from a git repo.
    """
    _settings = {
            'data-type' : 'keyvalue',
            'output-extensions' : ['.sqlite3', '.json']
            }

    def process(self):
        input_text = str(self.input_data)
        if self.is_url(input_text):
            repo, remote = repo_from_url(input_text)
        else:
            repo, remote = repo_from_path(input_text)

        ref = self.reference(repo)

        # TODO capture GitError class
        self.work(repo, remote, ref)

        self.output_data.save()

class Git(GitBase):
    """
    What should be default?
    """
    aliases = ['git']

    def work(self, repo, remote, ref):
        return "done"

class GitRepo(GitBase):
    """
    Adds all files in a repo to the project tree as additional documents.

    Files can be filtered to limit which ones are added.
    """
    aliases = ['repo']

    def work(self, repo, remote, ref):
        parent_dir = self.output_data.parent_dir()

        print(dir(ref))
        commit = repo[ref.target]
        tree = commit.tree

        def process_tree(tree, add_to_dir):
            for entry in tree:
                obj = repo[entry.oid]
                if obj.__class__.__name__ == 'Blob':
                    doc_key = os.path.join(add_to_dir, entry.name)
                    self.add_doc(doc_key, obj.data)
                elif obj.__class__.__name__ == 'Tree':
                    process_tree(obj, os.path.join(parent_dir, entry.name))
                else:
                    raise InternalDexyProblem(obj.__class__.__name__)

        process_tree(tree, parent_dir)
        # TODO return something more meaningful like a list of the files added.
        # doesn't matter that much since this repo is used for its side effects
        return "done"

class GitCommit(GitBaseKeyValue):
    """
    Returns key-value store information for the most recent commit, or the
    specified revision.
    """
    aliases = ['gitcommit']

    def work(self, repo, remote, ref):
        commit = repo[ref.target]
        commit_info = generate_commit_info(commit)

        for k, v in commit_info.items():
            self.output_data.append(k, v)

class GitLog(GitBase):
    """
    Returns a simple commit log for the specified repository.
    """
    aliases = ['gitlog']
    _settings = {
            'output-extensions' : ['.txt']
            }

    def work(self, repo, remote, ref):
        log = ""
        for commit in repo.walk(ref.target, pygit2.GIT_SORT_TIME):
            log += "%s: %s\n" % (commit.hex, commit.message.strip())
        return log
