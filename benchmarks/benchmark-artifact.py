from dexy.artifact import Artifact
from dexy.artifacts.file_system_json_artifact import FileSystemJsonArtifact
from dexy.artifacts.file_system_pickle_artifact import FileSystemPickleArtifact

def call_benchmark_artifact(artifact_class, n = 100):
    for i in xrange(n):
        print "running test", i
        benchmark_artifact(artifact_class)

def benchmark_artifact(artifact_class):
    a1 = artifact_class()
    a1.key = 'xyz'
    a1.set_data("abc")
    a1.set_hashstring()

    a2 = artifact_class()
    a2.hashstring = a1.hashstring
    assert not a2.key
    a2.load_meta()
    assert a2.key == 'xyz'

call_benchmark_artifact(FileSystemJsonArtifact, 10)
call_benchmark_artifact(FileSystemPickleArtifact, 10)

