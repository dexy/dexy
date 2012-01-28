from dexy.artifacts.file_system_json_artifact import FileSystemJsonArtifact
import cjson

class FileSystemCjsonArtifact(FileSystemJsonArtifact):
    """Artifact which persists data by writing to the file system and using
    cjson for serializing metadata"""

    def write_dict_to_file(self, data_dict, filepath):
        with open(filepath, "wb") as f:
            f.write(cjson.encode(data_dict))

    def read_dict_from_file(self, filepath):
        with open(filepath, "rb") as f:
            return cjson.decode(f.read())
