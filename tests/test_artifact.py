from dexy.artifact import Artifact

def test_artifact_filenames_simple_key():
    artifact = Artifact('abc')
    artifact.ext = '.out'
    assert artifact.canonical_filename() == 'abc.out'
    assert artifact.long_canonical_filename() == 'abc.out'

def test_artifact_filenames_file_key():
    artifact = Artifact('abc.txt')
    artifact.ext = '.out'
    assert artifact.canonical_filename() == 'abc.out'
    assert artifact.long_canonical_filename() == 'abc.txt.out'

def test_artifact_filenames_file_key_with_filters():
    artifact = Artifact('abc.txt|def|ghi')
    artifact.ext = '.out'
    assert artifact.canonical_filename() == 'abc.out'
    assert artifact.long_canonical_filename() == 'abc.txt-def-ghi.out'
