from dexy.artifact import Artifact
from dexy.artifacts.file_system_json_artifact import FileSystemJsonArtifact

def test_artifact_filenames_simple_key():
    artifact = Artifact()
    artifact.key = 'abc'
    artifact.ext = '.out'
    assert artifact.canonical_filename() == 'abc.out'
    assert artifact.long_canonical_filename() == 'abc.out'

def test_artifact_filenames_file_key():
    artifact = Artifact()
    artifact.key = 'abc.txt'
    artifact.ext = '.out'
    assert artifact.canonical_filename() == 'abc.out'
    assert artifact.long_canonical_filename() == 'abc.txt.out'

def test_artifact_filenames_file_key_with_filters():
    artifact = Artifact()
    artifact.key = 'abc.txt|def|ghi'
    artifact.ext = '.out'
    assert artifact.canonical_filename() == 'abc.out'
    assert artifact.long_canonical_filename() == 'abc.txt-def-ghi.out'

def test_add_additional_artifact():
    artifact = Artifact()
    artifact.key = 'abc.txt'
    artifact.artifacts_dir = 'artifacts'
    new_artifact = artifact.add_additional_artifact('def.txt', '.txt')
    assert new_artifact.final
    assert new_artifact.additional
    assert new_artifact.key in artifact.inputs()

def test_simple_metadata():
    HASHSTRING = 'abc123'
    a1 = FileSystemJsonArtifact()
    a1.hashstring = HASHSTRING
    a1.key = 'xyz'
    a1.save_meta()

    a2 = FileSystemJsonArtifact()
    a2.hashstring = HASHSTRING
    assert not a2.key
    a2.load_meta()
    assert a2.key == 'xyz'
