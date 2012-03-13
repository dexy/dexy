from dexy.dexy_filter import DexyFilter
import dexy.introspect
import json
import os

class ApiFilter(DexyFilter):
    """
    Base class for filters which post content to a remote API, such as a blog, CMS
    or helpdesk app. Provides standard formats and locations for storing
    configuration and authentication information.

    Need to read config for the API in general, such as the base URL and an API
    key for authentication.

    Also need to read config for the particular task/document being uploaded.
    This could be stored in the .dexy config entry, but this has two drawbacks.
    First, it makes it difficult to bulk define documents according to a
    pattern. Secondly, it makes it very difficult for dexy to modify this
    configuration to add additional information, such as the returned id for a
    newly created document.

    So, it is preferable to define a local file (defined by a relative path to
    the document in question) which can be overridden per-document in which we
    just store the API-related config and which can be modified by dexy without
    concern about identifying the entry in a .dexy file or accidentally
    overwriting some unrelated information.
    """
    ALIASES = ['apis']
    MASTER_API_KEY_FILE = "~/.dexyapis"
    PROJECT_API_KEY_FILE = ".dexyapis"
    PAGE_CONTENT_EXTENSIONS = ['.md', '.txt', '.html']
    API_KEY_NAME = None
    API_KEY_KEYS = ['username', 'password', 'url']

    DOCUMENT_API_CONFIG_FILE = None
    DOCUMENT_API_CONFIG_FILE_KEY = "api-config-file"

    # Put API key locations in this array, later entries will override earlier
    # entries if found, so you can set a user-wide default but override per-project.
    API_KEY_LOCATIONS = [MASTER_API_KEY_FILE, PROJECT_API_KEY_FILE]

    @classmethod
    def docmd_create_keyfile(klass):
        """
        Creates a key file in location specified by MASTER_API_KEY_FILE.
        """
        key_filename = os.path.expanduser(klass.MASTER_API_KEY_FILE)
        if os.path.exists(key_filename):
            raise Exception("File %s already exists!" % key_filename)

        keyfile_content = {}
        filter_list = dexy.introspect.filters()
        for filter_class in filter_list.values():
            if issubclass(filter_class, klass) and not filter_class == klass:
                print filter_class.__name__
                if not filter_class.API_KEY_NAME:
                    raise Exception("filter class %s should set API_KEY_NAME" % filter_class.__name__)
                keyfile_content[filter_class.API_KEY_NAME] = dict((k, "TODO") for k in filter_class.API_KEY_KEYS)

        with open(key_filename, "wb") as f:
            json.dump(keyfile_content, f, sort_keys = True, indent=4)

    def document_api_config_file(self):
        if self.artifact.args.has_key(self.DOCUMENT_API_CONFIG_FILE_KEY):
            return self.artifact.args[self.DOCUMENT_API_CONFIG_FILE_KEY]
        else:
            return self.DOCUMENT_API_CONFIG_FILE

    def document_config_file(self):
        document_dir = os.path.dirname(self.artifact.name)
        return os.path.join(document_dir, self.document_api_config_file())

    def read_document_config(self):
        document_config = self.document_config_file()
        if os.path.exists(document_config):
            with open(document_config, "r") as f:
                return json.load(f)
        else:
            raise Exception("no file %s found" % document_config)

    def save_document_config(self, config):
        document_config = self.document_config_file()
        with open(document_config, "w") as f:
            json.dump(config, f, sort_keys=True, indent=4)

    @classmethod
    def read_param_class(klass, param_name):
        param_value = None
        if not param_name in klass.API_KEY_KEYS:
            raise Exception("Param %s not specified in API_KEY_KEYS for %s" % (param_name, klass.__name__))

        for filename in klass.API_KEY_LOCATIONS:
            if "~" in filename:
                filename = os.path.expanduser(filename)

            if os.path.exists(filename):
                with open(filename, "r") as f:
                    params = json.load(f)
                    if params.has_key(klass.API_KEY_NAME):
                        param_value = params[klass.API_KEY_NAME][param_name]

        if param_value and param_value.startswith("$"):
            # need to get value of bash variable
            param_value_from_env = os.getenv(param_value.lstrip("$"))
            if not param_value_from_env:
                raise Exception("Bash variable %s not defined in this environment!" % param_value)
            param_value = param_value_from_env

        if param_value:
            return param_value
        else:
            msg = "Could not find %s for %s in: %s" % (param_name, klass.API_KEY_NAME, ", ".join(klass.API_KEY_LOCATIONS))
            raise Exception(msg)

    def read_param(self, param_name):
        param_value = self.arg_value(param_name)
        if not param_value:
            param_value = self.__class__.read_param_class(param_name)

        return param_value
