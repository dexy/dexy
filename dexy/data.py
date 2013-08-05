from dexy.exceptions import InternalDexyProblem
import chardet
import dexy.plugin
import dexy.storage
import dexy.utils
import dexy.wrapper
import inflection
import os
import posixpath
import shutil

class Data(dexy.plugin.Plugin):
    """
    Base class for types of Data.
    """
    __metaclass__ = dexy.plugin.PluginMeta
    _settings = {
            'shortcut' : ("A shortcut to refer to a file.", None),
            'ws-template' : ("custom website template to apply.", None),
            'storage-type' : ("Type of storage to use.", 'generic'),
            'canonical-output' : ("Whether this data type is canonical output.", None),
            'canonical-name' : ("The default name.", None),
            'output-name' : ("A custom name which overrides default name.", None),
            'title' : ("A custom title.", None),
            }

    state_transitions = (
            (None, 'new'),
            ('new', 'ready')
            )

    def __init__(self, key, ext, storage_key, settings, wrapper):
        self.key = key
        self.ext = ext
        self.storage_key = storage_key

        self.wrapper = wrapper
        self.initialize_settings(**settings)

        self._data = None
        self.state = None
        self.name = self.setting('canonical-name')
        if not self.name:
            msg = "Document must provide canonical-name setting to data."
            raise InternalDexyProblem(msg)
        elif self.name.startswith("("):
            raise Exception()

        self.transition('new')

    def output_name(self):
        """
        Canonical name to output to, relative to output root. Returns 'none' if
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
            if "/" in output_name:
                if output_root in output_name:
                    return relativize(output_name)
                else:
                    self.storage.assert_location_is_in_project_dir(output_name)
                    return output_name
            else:
                output_dir = os.path.dirname(relativize(self.name))
                return os.path.join(output_dir, output_name)
        else:
            return relativize(self.name)
        
    def transition(self, new_state):
        dexy.utils.transition(self, new_state)

    def setup(self):
        self.setup_storage()
        self.transition('ready')

    def __repr__(self):
        return "Data('%s')" % (self.key)

    def storage_class_alias(self, file_ext):
        return self.setting('storage-type')

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
        return (self.alias, self.key, self.ext, self.storage_key, self.setting_values())
    
    def keys(self):
        return []

    def setup_storage(self):
        storage_type = self.storage_class_alias(self.ext)
        instanceargs = (self.storage_key, self.ext, self.wrapper,)
        self.storage = dexy.storage.Storage.create_instance(storage_type, *instanceargs)

        self.storage.assert_location_is_in_project_dir(self.name)

        if self.output_name():
            self.storage.assert_location_is_in_project_dir(self.output_name())

        self.storage.setup()

    def parent_dir(self):
        return posixpath.dirname(self.name)

    def parent_output_dir(self):
        return posixpath.dirname(self.output_name())

    def long_name(self):
        if "|" in self.key:
            return "%s%s" % (self.key.replace("|", "-"), self.ext)
        else:
            return self.setting('canonical-name')

    def rootname(self):
        return os.path.splitext(self.name)[0]

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

        return self.setting('title') or title_from_name

    def relative_path_to(self, relative_to):
        return posixpath.relpath(relative_to, self.parent_dir())

    # Define functions that might get called on expectation of a string...

    def strip(self):
        return unicode(self).strip()
    
    def splitlines(self, arg=None):
        return unicode(self).splitlines(arg)

    def save(self):
        try:
            self.storage.save()
        except Exception as e:
            print e
            raise dexy.exceptions.InternalDexyProblem("problem saving %s" % self.key)

class Generic(Data):
    """
    Data type representing generic binary or text-based data in a single blob.
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
        has_loaded_data = (self._data) and (self._data != [{}])
        return has_loaded_data or self.is_cached()

    def is_cached(self, this=None):
        if this is None:
            this = (self.wrapper.state in ('walked', 'running'))
        return self.storage.data_file_exists(this)

    def filesize(self, this=None):
        if this is None:
            this = (self.wrapper.state in ('walked', 'running'))
        return self.storage.data_file_size(this)

    def data(self):
        if (not self._data) or self._data == [{}]:
            self.load_data()
        return self._data

    def as_text(self):
        return unicode(self)

    def keys(self):
        return ['1']

    def __getitem__(self, key):
        if key == '1':
            return self.data()
        else:
            return self.data()[key]

    def iteritems(self):
        yield ('1', self.data())

    def items(self):
        return [('1', self.data(),)]

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
        return self.setting('canonical-output')

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

class SectionValue(object):
    def __init__(self, data, parent, parentindex):
        assert isinstance(data, dict)
        self.data = data
        self.parent = parent
        self.parentindex = parentindex

    def __unicode__(self):
        return unicode(self.data['contents'])

    def __str__(self):
        return str(self.data['contents'])

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.parent.data()[self.parentindex+1][key] = value

    def splitlines(self):
        return unicode(self).splitlines()

class Sectioned(Generic):
    """
    Data in sections which must be kept in order.
    """
    aliases = ['sectioned']

    _settings = {
            'storage-type' : 'jsonsectioned'
            }

    def __unicode__(self):
        return u"\n".join(unicode(v) for v in self.values())

    def __str__(self):
        return "\n".join(str(v) for v in self.values())

    def __len__(self):
        return len(self.data())-1

    def setup(self):
        self.setup_storage()
        self._data = [{}]
        self.transition('ready')

    def __setitem__(self, key, value):
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
            f.write(unicode(self).encode("utf-8"))

    def keyindex(self, key):
        try:
            return self.keys().index(key)
        except ValueError:
            return -1

    def value(self, key):
        index = self.keyindex(key)
        if index > -1:
            return self.values()[index]
        else:
            try:
                return self.data()[0][key]
            except KeyError:
                msg = "No value for %s available in sections or metadata."
                msgargs = (key)
                raise dexy.exceptions.UserFeedback(msg % msgargs)

    def __getitem__(self, key):
        try:
            return self.data()[key+1]
        except TypeError:
            return self.value(key)

    def iteritems(self):
        keys = self.keys()
        values = self.values()
        for i in range(len(self)):
            yield (keys[i], values[i])

    def items(self):
        return [(key, value) for (key, value) in self.iteritems()]

class KeyValue(Generic):
    """
    Data class for key-value data.
    """
    aliases  = ['keyvalue']
    _settings = {
            'storage-type' : 'sqlite3'
            }

    def storage_class_alias(self, file_ext):
        if file_ext == '.sqlite3':
            return 'sqlite3'
        elif file_ext == '.json':
            return 'json'
        else:
            return self.setting('storage-type')

    def __unicode__(self):
        return self.as_text()

    def as_text(self):
        text = []
        for k, v in self.storage:
            text.append(u"%s: %s" % (k, v))
        return u"\n".join(text)

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
