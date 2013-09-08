from dexy.exceptions import UserFeedback
from dexy.filters.git import repo_from_path
from dexy.filters.git import repo_from_url
from dexy.filters.git import generate_commit_info
from tests.utils import assert_in_output
from tests.utils import runfilter
from tests.utils import tempdir
from nose.exc import SkipTest
import os
import json

REMOTE_REPO_HTTPS = "https://github.com/ananelson/dexy-templates"
PATH_TO_LOCAL_REPO = os.path.expanduser("~/dev/testrepo")
# TODO use subprocess to check out a repo to a temp dir, or have a repo in data
# dir, or use [gasp] submodules.

try:
    import pygit2
    import urllib

    no_local_repo = not os.path.exists(PATH_TO_LOCAL_REPO)

    try:
        urllib.urlopen("http://google.com")
        no_internet = False
    except IOError:
        no_internet = True

    if no_local_repo:
        SKIP = (True, "No local repo at %s." % PATH_TO_LOCAL_REPO)
    elif no_internet:
        SKIP = (True, "Internet not available.")
    else:
        SKIP = (False, None)

except ImportError:
    SKIP = (True, "pygit2 not installed")

def skip():
    if SKIP[0]:
        raise SkipTest(SKIP[1])

skip()

def test_run_gitrepo():
    with runfilter("repo", REMOTE_REPO_HTTPS) as doc:
        assert len(doc.wrapper.nodes) > 20

def test_generate_commit_info():
    repo, remote = repo_from_url(REMOTE_REPO_HTTPS)

    refs = repo.listall_references()
    ref = repo.lookup_reference(refs[0])
    commit = repo[ref.target]
    commit_info = generate_commit_info(commit)

    assert commit_info['author-name'] == "Ana Nelson"
    assert commit_info['author-email'] == "ana@ananelson.com"

def test_git_commit():
    with runfilter("gitcommit", REMOTE_REPO_HTTPS) as doc:
        output = doc.output_data()
        patches = json.loads(output['patches'])
        assert output['author-name'] == "Ana Nelson"
        assert output['author-email'] == "ana@ananelson.com"
        #assert output['message'] == "Add README file."
        #assert output['hex'] == "2f15837e64a70e4d34b924f6f8c371a266d16845"

def test_git_log():
    assert_in_output("gitlog", PATH_TO_LOCAL_REPO,
            "Add README file.")

def test_git_log_remote():
    assert_in_output("gitlog", REMOTE_REPO_HTTPS,
            "Rename")

def test_repo_from_url():
    repo, remote = repo_from_url(REMOTE_REPO_HTTPS)
    assert remote.name == 'origin'
    assert remote.url == REMOTE_REPO_HTTPS

def test_repo_from_path():
    repo, remote = repo_from_path(PATH_TO_LOCAL_REPO)
    assert ".git" in repo.path
    #assert isinstance(repo.head, pygit2.Object)
    # assert "README" in repo.head.message

def test_repo_from_invalid_path():
    with tempdir():
        try:
            repo, remote = repo_from_path(".")
            assert False
        except UserFeedback as e:
            assert "no git repository was found at '.'" in str(e)

def test_run_git():
    with runfilter("git", PATH_TO_LOCAL_REPO) as doc:
        doc.output_data()

def test_run_git_remote():
    with runfilter("git", REMOTE_REPO_HTTPS) as doc:
        doc.output_data()
