from dexy.artifacts.file_system_json_artifact import FileSystemJsonArtifact
import pickle

class FileSystemPickleArtifact(FileSystemJsonArtifact):
    def meta_filename(self):
        return "%s-meta.pickle" % (self.hashstring)

    def cached_output_filename(self):
        return "%s-output.pickle" % (self.hashstring)

    def write_dict_to_file(self, data_dict, filepath):
        with open(filepath, "wb") as f:
            pickle.dump(data_dict, f)

    def read_dict_from_file(self, filepath):
        with open(filepath, "rb") as f:
            return pickle.load(f)

