from dexy.common import OrderedDict
import dexy.plugin
import chardet
import dexy.storage
import dexy.utils
import dexy.wrapper
import os
import posixpath
import shutil
import inflection

class Data(dexy.plugin.Plugin):
    """
    Base class for types of Data.
    """
    __metaclass__ = dexy.plugin.PluginMeta
    _settings = {
            'default-storage-type' : ("Type of storage to use if not specified", 'generic'),
            }

    state_transitions = (
            (None, 'new'),
            ('new', 'ready')
            )

    def __init__(self, key, ext, canonical_name, storage_key,
            args, storage_type, canonical_output, wrapper):
        self.key = key
        self.ext = ext
        self.name = canonical_name
        self.storage_key = storage_key
        self.args = args
        self.storage_type = storage_type
        self.wrapper = wrapper
        self.canonical_output = canonical_output

        self.initialize_settings()

        self._data = None
        self.state = None

        self.transition('new')

    def output_name(self):
        """
        Canonical name to output to, relative to output root. Returns 'none' if
        artifact not in output_root.
        """
        if self.wrapper.output_root in self.name:
            return os.path.relpath(self.name, self.wrapper.output_root)

    def transition(self, new_state):
        dexy.utils.transition(self, new_state)

    def setup(self):
        self.setup_storage()
        self.transition('ready')

    def __repr__(self):
        return "Data('%s')" % (self.key)

    def storage_class_alias(self, file_ext):
        return self.setting('default-storage-type')

    def __unicode__(self):
        if isinstance(self.data(), unicode):
            return self.data()
        elif not self.data():
            return unicode(None)
        else:
            if self.wrapper.encoding == 'chardet':
                encoding = chardet.detect(self.data())['encoding']
                if not encoding:
                    return self.data().decode("utf-8")
                else:
                    return self.data().decode(encoding)
            else:
                return self.data().decode(self.wrapper.encoding)

    def __str__(self):
        return str(unicode(self))

    def args_to_data_init(self):
        """
        Returns a tuple of attributes in the correct order to pass to create_instance
        """
        return (self.alias, self.key, self.ext, self.name,
                self.storage_key, self.args, self.storage_type,
                self.canonical_output,)
    
    def keys(self):
        return []

    def setup_storage(self):
        self.storage_type = self.storage_type or self.storage_class_alias(self.ext)
        instanceargs = (self.storage_key, self.ext, self.wrapper,)
        self.storage = dexy.storage.Storage.create_instance(self.storage_type, *instanceargs)
        self.storage.assert_location_is_in_project_dir(self.name)
        self.storage.setup()

    def parent_dir(self):
        return posixpath.dirname(self.name)

    def long_name(self):
        if "|" in self.key:
            return "%s%s" % (self.key.replace("|", "-"), self.ext)
        else:
            return self.name

    def basename(self):
        return posixpath.basename(self.name)

    def baserootname(self):
        """
        Returns basename stripped of file extension.
        """
        return posixpath.splitext(self.basename())[0]

    def web_safe_document_key(self):
        return self.long_name().replace("/", "--")

    def title(self):
        if self.is_index_page():
            subdir = posixpath.split(posixpath.dirname(self.name))[-1]
            if subdir == "/":
                title_from_name = "Home"
            else:
                title_from_name = inflection.titleize(subdir)
        else:
            title_from_name = inflection.titleize(self.baserootname())

        return self.args.get('title') or title_from_name

    def relative_path_to(self, relative_to):
        return posixpath.relpath(relative_to, self.parent_dir())

    def relative_refs(self, relative_to_file):
        doc_dir = posixpath.dirname(relative_to_file)
        refs = [
                posixpath.relpath(self.key, doc_dir),
                posixpath.relpath(self.long_name(), doc_dir),
                "/%s" % self.key,
                "/%s" % self.long_name(),
                "title:%s" % self.title()
        ]
        if self.args.get('shortcut'):
            refs.append(self.args.get('shortcut'))
        return refs

    # Define functions that might get called on expectation of a string...

    def strip(self):
        return unicode(self).strip()
    
    def splitlines(self, arg=None):
        return unicode(self).splitlines(arg)

class Generic(Data):
    """
    Data type representing generic binary or text-based data.
    """
    aliases = ['generic']

    def save(self):
        if isinstance(self._data, unicode):
            self.storage.write_data(self._data.encode("utf-8"))
        else:
            if self._data == None:
                raise dexy.exceptions.InternalDexyProblem("no data for %s" % self.key)
            self.storage.write_data(self._data)

    def set_data(self, data):
        """
        Set data to the passed argument and persist data to disk.
        """
        self._data = data
        self.save()

    def load_data(self, this=None):
        try:
            self._data = self.storage.read_data()
        except IOError:
            msg = "no data in file '%s' for %s (wrapper state '%s')"
            msgargs = (self.storage.data_file(), self.key, self.wrapper.state)
            raise dexy.exceptions.InternalDexyProblem(msg % msgargs)

    def has_data(self):
        return self._data or self.is_cached()

    def is_cached(self, this=None):
        if this is None:
            this = (self.wrapper.state in ('walked', 'running'))
        return self.storage.data_file_exists(this)

    def filesize(self, this=None):
        if this is None:
            this = (self.wrapper.state in ('walked', 'running'))
        return self.storage.data_file_size(this)

    def data(self):
        if not self._data:
            self.load_data()
        return self._data

    def as_text(self):
        return unicode(self)

    def as_sectioned(self):
        return {'1' : self.data()}

    def json_as_dict(self):
        return self.from_json()

    def from_json(self):
        """
        Attempts to load data using a JSON parser, returning whatever objects are defined in the JSON.
        """
        if self._data and isinstance(self._data, basestring):
            return dexy.utils.parse_json(self._data)
        elif self._data and not isinstance(self._data, basestring):
            raise Exception(self._data.__class__.__name__)
        else:
            with open(self.storage.data_file(), "r") as f:
                return dexy.utils.parse_json_from_file(f)

    def is_canonical_output(self):
        return self.canonical_output

    def is_index_page(self):
        return self.name.endswith("index.html")

    def websafe_key(self):
        return self.key

    def copy_from_file(self, filename):
        shutil.copyfile(filename, self.storage.data_file())

    def clear_data(self):
        self._data = None

    def clear_cache(self):
        self._size = None
        try:
            os.remove(self.storage.data_file())
        except os.error as e:
            self.wrapper.log.warn(str(e))

    def output_to_file(self, filepath):
        """
        Write canonical output to a file. Parent directory must exist already.
        """
        if not self.storage.copy_file(filepath):
            self.storage.write_data(self.data(), filepath)

class Sectioned(Generic):
    """
    Data in sections which must be kept in order.
    """
    aliases = ['sectioned']

    _settings = {
            'default-storage-type' : 'jsonordered'
            }

    def __unicode__(self):
        return u"\n".join(unicode(v) for v in self.data().values())

    def __str__(self):
        return "\n".join(str(v) for v in self.data().values())

    def as_sectioned(self):
        return self.data()

    def keys(self):
        return self.data().keys()

    def output_to_file(self, filepath):
        """
        Write canonical output to a file.
        """
        with open(filepath, "wb") as f:
            f.write(unicode(self).encode("utf-8"))

    def value(self, key):
        return self.data()[key]

    def __getitem__(self, key):
        return self.value(key)

class KeyValue(Generic):
    """
    Data class for key-value data.
    """
    aliases  = ['keyvalue']
    _settings = {
            'default-storage-type' : 'sqlite3'
            }

    def storage_class_alias(self, file_ext):
        if file_ext == '.sqlite3':
            return 'sqlite3'
        elif file_ext == '.json':
            return 'json'
        else:
            return self.setting('default-storage-type')

    def __unicode__(self):
        return self.as_text()

    def as_text(self):
        text = []
        for k, v in self.storage:
            text.append(u"%s: %s" % (k, v))
        return u"\n".join(text)

    def as_sectioned(self):
        od = OrderedDict()
        for k, v in self.storage:
            od[k] = v
        return od

    def data(self):
        return self.as_sectioned()

    def value(self, key):
        return self.storage[key]

    def like(self, key):
        return self.storage.like(key)

    def __getitem__(self, key):
        return self.value(key)

    def append(self, key, value):
        self.storage.append(key, value)

    def query(self, query):
        return self.storage.query(query)

    def keys(self):
        return self.storage.keys()

    def save(self):
        try:
            self.storage.save()
        except Exception as e:
            print e
            raise dexy.exceptions.InternalDexyProblem("problem saving %s" % self.key)
