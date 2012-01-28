from dexy.artifacts.file_system_pickle_artifact import FileSystemPickleArtifact
import cPickle

class FileSystemcPickleArtifact(FileSystemPickleArtifact):
    """Artifact which persists data by writing to the file system and using
    cjson for serializing metadata"""
    def write_dict_to_file(self, data_dict, filepath):
        with open(filepath, "wb") as f:
            cPickle.dump(data_dict, f)

    def read_dict_from_file(self, filepath):
        with open(filepath, "rb") as f:
            return cPickle.load(f)
