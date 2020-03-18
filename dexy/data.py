from dexy.exceptions import InternalDexyProblem
import dexy.plugin
import dexy.storage
import dexy.utils
import dexy.wrapper
import inflection
import os
import posixpath
import shutil
import urllib

class Data(dexy.plugin.Plugin, metaclass=dexy.plugin.PluginMeta):
    """
    Base class for types of Data.
    """
    _settings = {
            'shortcut' : ("A shortcut to refer to a file.", None),
            'storage-type' : ("Type of storage to use.", 'generic'),
            'canonical-output' : ("Whether this data type is canonical output.", None),
            'canonical-name' : ("The default name.", None),
            'output-name' : ("A custom name which overrides default name.", None),
            'title' : ("A custom title.", None),
            }

    state_transitions = (
            (None, 'new'),
            ('new', 'ready'),
            ('ready', 'ready')
            )

    def add_to_lookup_nodes(self):
        if self.setting('canonical-output'):
            self.wrapper.add_data_to_lookup_nodes(self.key, self)
            self.wrapper.add_data_to_lookup_nodes(self.output_name(), self)
            self.wrapper.add_data_to_lookup_nodes(self.title(), self)

    def add_to_lookup_sections(self):
        if self.setting('canonical-output'):
            for section_name in self.keys():
                if not section_name == '1':
                    self.wrapper.add_data_to_lookup_sections(section_name, self)

    def __init__(self, key, ext, storage_key, settings, wrapper):
        self.key = key
        self.ext = ext
        self.storage_key = storage_key

        self.wrapper = wrapper
        self.initialize_settings(**settings)
        self.update_settings(settings)

        self._data = None
        self.state = None
        self.name = self.setting('canonical-name')
        if not self.name:
            msg = "Document must provide canonical-name setting to data."
            raise InternalDexyProblem(msg)
        elif self.name.startswith("("):
            raise Exception()

        self.transition('new')
        
    def transition(self, new_state):
        """
        Transition between states in a state machine.
        """
        dexy.utils.transition(self, new_state)

    def args_to_data_init(self):
        """
        Returns tuple of attributes to pass to create_instance.
        """
        return (self.alias, self.key, self.ext, self.storage_key, self.setting_values())

    def setup(self):
        self.setup_storage()
        self.transition('ready')

    def setup_storage(self):
        storage_type = self.storage_class_alias(self.ext)
        instanceargs = (self.storage_key, self.ext, self.wrapper,)
        self.storage = dexy.storage.Storage.create_instance(storage_type, *instanceargs)

        self.storage.assert_location_is_in_project_dir(self.name)

        if self.output_name():
            self.storage.assert_location_is_in_project_dir(self.output_name())

        self.storage.setup()

    def storage_class_alias(self, file_ext):
        return self.setting('storage-type')

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.key)

    def __lt__(self, other):
        """
        Sort data obejects by their output name.
        """
        return self.output_name() < other.output_name()

    def __getattr__(self, item):
        """
        Make setting values available as attributes.
        """
        try:
            return self._instance_settings[item]
        except KeyError:
            raise AttributeError(item)

    def data(self):
        if (not self._data) or self._data == [{}]:
            self.load_data()
        return self._data

    def load_data(self, this=None):
        try:
            self._data = self.storage.read_data()
        except IOError:
            msg = "no data in file '%s' for %s (wrapper state '%s', data state '%s')"
            msgargs = (self.storage.data_file(), self.key,
                    self.wrapper.state, self.state)
            raise dexy.exceptions.InternalDexyProblem(msg % msgargs)

    def clear_data(self):
        self._data = None

    def clear_cache(self):
        self._size = None
        try:
            os.remove(self.storage.data_file())
        except os.error as e:
            self.wrapper.log.warn(str(e))

    def copy_from_file(self, filename):
        shutil.copyfile(filename, self.storage.data_file())

    def output_to_file(self, filepath):
        """
        Write canonical output to a file. Parent directory must exist already.
        """
        if not self.storage.copy_file(filepath):
            self.storage.write_data(self.data(), filepath)

    def has_data(self):
        has_loaded_data = (self._data) and (self._data != [{}])
        return has_loaded_data or self.is_cached()

    def set_data(self, data):
        """
        Shortcut to set and save data.
        """
        self._data = data
        self.save()

    def is_cached(self, this=None):
        if this is None:
            this = (self.wrapper.state in ('walked', 'running'))
        return self.storage.data_file_exists(this)

    # Filename-related Attributes

    def parent_dir(self):
        """
        The name of the directory containing the document.
        """
        return posixpath.dirname(self.name)

    def parent_output_dir(self):
        """
        The name of the directory containing the document based on final output
        name, which may be specified in a different directory.
        """
        return posixpath.dirname(self.output_name())

    def long_name(self):
        """
        A unique, but less canonical, name for the document.
        """
        if "|" in self.key:
            return "%s%s" % (self.key.replace("|", "-"), self.ext)
        else:
            return self.setting('canonical-name')

    def rootname(self):
        """
        Returns the file name, including path, without extension.
        """
        return os.path.splitext(self.name)[0]

    def basename(self):
        """
        Returns the local file name without path.
        """
        return posixpath.basename(self.name)

    def baserootname(self):
        """
        Returns local file name without extension or path.
        """
        return posixpath.splitext(self.basename())[0]

    def web_safe_document_key(self):
        """
        Returns document key with slashes replaced by double hypheens.
        """
        return self.long_name().replace("/", "--")

    def title(self):
        """
        Canonical title of document.

        Tries to guess from document name if `title` setting not provided.
        """
        if self.setting('title'):
            return self.setting('title')

        if self.is_index_page():
            subdir = posixpath.split(posixpath.dirname(self.name))[-1]
            if subdir == "/":
                return "Home"
            elif subdir:
                return inflection.titleize(subdir)
            else:
                return inflection.titleize(self.baserootname())
        else:
            return inflection.titleize(self.baserootname())

    def relative_path_to(self, relative_to):
        """
        Returns a relative path from this document to the passed other
        document.
        """
        return posixpath.relpath(relative_to, self.output_parent_dir())

    def strip(self):
        """
        Returns contents stripped of leading and trailing whitespace.
        """
        return str(self).strip()
    
    def splitlines(self, arg=None):
        """
        Returns a list of lines split at newlines or custom split.
        """
        return str(self).splitlines(arg)

    def url_quoted_name(self):
        """
        Applies urllib's quote method to name.
        """
        return urllib.quote(self.name)

    def output_name(self):
        """
        Canonical name to output to, relative to output root. Returns None if
        artifact not in output_root.
        """
        output_root = self.wrapper.output_root

        def relativize(path):
            if output_root == ".":
                return path
            elif os.path.abspath(output_root) in os.path.abspath(path):
                return os.path.relpath(path, output_root)

        output_name = self.setting('output-name')
        if output_name:
            return relativize(output_name)
        else:
            return relativize(self.name)

    def output_parent_dir(self):
        """
        Canonical output directory, taking into account custom outputroot and document name.
        """
        return os.path.dirname(self.output_name())
        
    def filesize(self, this=None):
        """
        Returns size of file stored on disk.
        """
        if this is None:
            this = (self.wrapper.state in ('walked', 'running'))
        return self.storage.data_file_size(this)

    def is_canonical_output(self):
        """
        Used by reports to determine if document should be written to output/
        directory.
        """
        return self.setting('canonical-output')

    def is_index_page(self):
        """
        Is this a website index page, i.e. named `index.html`.
        """
        return self.output_name() and self.output_name().endswith("index.html")

    def websafe_key(self):
        """
        Returns a web-friendly version of the key.
        """
        return self.key

    # Deprecated methods

    def as_text(self):
        """
        DEPRECATED. Instead call unicode.
        """
        return str(self)

class Generic(Data):
    """
    Data type representing generic binary or text-based data in a single blob.
    """
    aliases = ['generic']

    def save(self):
        if isinstance(self._data, str):
            self.storage.write_data(self._data.encode("utf-8"))
        else:
            if self._data == None:
                msg = "No data found for '%s', did you reference a file that doesn't exist?"
                raise dexy.exceptions.UserFeedback(msg % self.key)
            self.storage.write_data(self._data)

    def __str__(self):
        if isinstance(self.data(), str):
            return self.data()
        elif not self.data():
            return str(None)
        else:
            return self.wrapper.decode_encoded(self.data())

    def iteritems(self):
        """
        Iterable list of sections in document.
        """
        yield ('1', self.data())

    def items(self):
        """
        List of sections in document.
        """
        return [('1', self.data(),)]

    def keys(self):
        """
        List of keys (section names) in document.
        """
        return ['1']

    def __getitem__(self, key):
        if key == '1':
            return self.data()
        else:
            try:
                return self.data()[key]
            except TypeError:
                if self.ext == '.json':
                    return self.from_json()[key]
                elif self.ext == '.yaml':
                    return self.from_yaml()[key]
                else:
                    raise

    def from_json(self):
        """
        Attempts to load data using a JSON parser, returning whatever objects
        are defined in the JSON.
        """
        if self._data and isinstance(self._data, str):
            return dexy.utils.parse_json(self._data)
        elif self._data and not isinstance(self._data, str):
            raise Exception(self._data.__class__.__name__)
        else:
            with open(self.storage.data_file(), "r") as f:
                return dexy.utils.parse_json_from_file(f)

    def from_yaml(self):
        """
        Attempts to load data using a YAML parser, returning whatever objects
        are defined in the YAML.
        """
        if self._data and isinstance(self._data, str):
            return dexy.utils.parse_yaml(self._data)
        elif self._data and not isinstance(self._data, str):
            raise Exception(self._data.__class__.__name__)
        else:
            with open(self.storage.data_file(), "r") as f:
                return dexy.utils.parse_yaml(f.read())

    def json_as_dict(self):
        """
        DEPRECATED. Instead call from_json
        """
        return self.from_json()

class SectionValue(object):
    def __init__(self, data, parent, parentindex):
        assert isinstance(data, dict)
        self.data = data
        self.parent = parent
        self.parentindex = parentindex

    def __str__(self):
        return self.data['contents'] or ''

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.parent.data()[self.parentindex+1][key] = value

    def splitlines(self):
        return str(self).splitlines()

class Sectioned(Data):
    """
    A document with named, ordered sections.

    Sections can also contain arbitrary metadata.
    """
    aliases = ['sectioned']

    _settings = {
            'storage-type' : 'jsonsectioned'
            }

    def setup(self):
        self.setup_storage()
        self._data = [{}]
        self.transition('ready')

    def save(self):
        try:
            self.storage.write_data(self._data)
        except Exception as e:
            print(self._data)
            msg = "Problem saving '%s': %s" % (self.key, str(e))
            raise dexy.exceptions.InternalDexyProblem(msg)

    def __str__(self):
        return "\n".join(str(v) for v in list(self.values()) if str(v))

    def __len__(self):
        """
        The number of sections.
        """
        return len(self.data())-1

    def __setitem__(self, key, value):
        keyindex = self.keyindex(key)
        if keyindex >= 0:
            # Existing section.
            assert self._data[keyindex+1]['name'] == key
            self._data[keyindex+1]['contents'] = value
        else:
            # New section.
            section_dict = {"name" : key, "contents" : value}
            self._data.append(section_dict)

    def __delitem__(self, key):
        index = self.keyindex(key)
        self.data().pop(index+1)

    def keys(self):
        return [a['name'] for a in self.data()[1:]]

    def values(self):
        return [SectionValue(a, self, i) for i, a in enumerate(self.data()[1:])]

    def output_to_file(self, filepath):
        """
        Write canonical (not structured) output to a file.
        """
        with open(filepath, "wb") as f:
            f.write(str(self).encode("utf-8"))

    def keyindex(self, key):
        if self._data == [{}]:
            return -1

        try:
            return list(self.keys()).index(key)
        except ValueError:
            return -1

    def value(self, key, throwException=True):
        index = self.keyindex(key)
        if index > -1:
            return list(self.values())[index]
        else:
            try:
                return self.data()[0][key]
            except KeyError:
                msg = "No value for %s available in sections or metadata."
                msgargs = (key)
                if throwException:
                    raise dexy.exceptions.UserFeedback(msg % msgargs)

    def __getitem__(self, key):
        try:
            return self.data()[key+1]
        except (TypeError, KeyError):
            return self.value(key)

    def items(self):
        """
        Iterable list of sections in document.
        """
        keys = self.keys()
        values = self.values()
        for i in range(len(keys)):
            yield (keys[i], values[i])

class KeyValue(Data):
    """
    Data class for key-value data.
    """
    aliases  = ['keyvalue']
    _settings = {
            'storage-type' : 'sqlite3'
            }

    def __unicode__(self):
        return repr(self)

    def data(self):
        raise Exception("No data method for KeyValue type data.")

    def storage_class_alias(self, file_ext):
        if file_ext == '.sqlite3':
            return 'sqlite3'
        elif file_ext == '.json':
            return 'json'
        else:
            return self.setting('storage-type')

    def value(self, key, throwException=True):
        try:
            return self.storage[key]
        except Exception:
            if throwException:
                raise

    def like(self, key):
        try:
            return self.storage.like(key)
        except AttributeError:
            msg = "The `like()` method is not implemented for storage type '%s'"
            msgargs = self.storage.alias
            raise dexy.exceptions.UserFeedback(msg % msgargs)

    def __getitem__(self, key):
        return self.value(key)

    def append(self, key, value):
        self.storage.append(key, value)

    def query(self, query):
        return self.storage.query(query)

    def keys(self):
        return self.storage.keys()

    def items(self):
        """
        List of available keys.
        """
        return self.storage.items()

    def save(self):
        try:
            self.storage.persist()
        except Exception as e:
            raise
            msg = "Problem saving '%s': %s" % (self.key, str(e))
            raise dexy.exceptions.InternalDexyProblem(msg)
