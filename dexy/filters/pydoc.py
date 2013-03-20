from dexy.filter import DexyFilter
import inspect
import json
import pkgutil
import sys

class PythonDocumentationFilter(DexyFilter):
    """
    Returns doc info for named python modules.
    """
    aliases = ["pydoc"]
    _settings = {
            'input-extensions' : ['.txt'],
            'output-data-type' : 'keyvalue',
            'output-extensions' : ['.sqlite3', '.json']
            }

    def fetch_item_content(self, key, item):
        is_method = inspect.ismethod(item)
        is_function = inspect.isfunction(item)
        if is_method or is_function:
            # Get source code
            try:
                source = inspect.getsource(item)
            except IOError:
                source = ""

            self.add_source_for_key(key, source)

            self.output_data.append("%s:doc" % key, inspect.getdoc(item))
            self.output_data.append("%s:comments" % key, inspect.getcomments(item))

        else: # not a function or a method
            try:
                # If this can be JSON-serialized, leave it alone...
                json.dumps(item)
                self.add_source_for_key(key, item)
            except TypeError:
                # ... if it can't, convert it to a string to avoid problems.
                self.add_source_for_key(key, str(item))

    def add_source_for_key(self, key, source):
        """
        Appends source code + syntax highlighted source code to persistent store.
        """
        self.output_data.append("%s:value" % key, source)
        if not (type(source) == str or type(source) == unicode):
            source = inspect.getsource(source)
        self.output_data.append("%s:source" % key, source)

    def process_members(self, package_name, mod):
        """
        Process all members of the package or module passed.
        """
        name = mod.__name__

        for k, m in inspect.getmembers(mod):
            self.log_debug("in %s processing element %s" % (mod.__name__, k))
            if not inspect.isclass(m) and hasattr(m, '__module__') and m.__module__ and m.__module__.startswith(package_name):
                key = "%s.%s" % (m.__module__, k)
                self.fetch_item_content(key, m)

            elif inspect.isclass(m) and m.__module__.startswith(package_name):
                key = "%s.%s" % (mod.__name__, k)
                try:
                    item_content = inspect.getsource(m)
                    self.output_data.append("%s:doc" % key, inspect.getdoc(m))
                    self.output_data.append("%s:comments" % key, inspect.getcomments(m))
                    self.add_source_for_key(key, item_content)
                except IOError:
                    self.log_debug("can't get source for %s" % key)
                    self.add_source_for_key(key, "")

                try:
                    for ck, cm in inspect.getmembers(m):
                        key = "%s.%s.%s" % (name, k, ck)
                        self.fetch_item_content(key, cm)
                except AttributeError:
                    pass

            else:
                key = "%s.%s" % (name, k)
                self.fetch_item_content(key, m)

    def process_module(self, package_name, name):
        try:
            self.log_debug("Trying to import %s" % name)
            __import__(name)
            mod = sys.modules[name]
            self.log_debug("Success importing %s" % name)

            try:
                module_source = inspect.getsource(mod)
                json.dumps(module_source)
                self.add_source_for_key(name, inspect.getsource(mod))
            except (UnicodeDecodeError, IOError, TypeError):
                self.log_debug("Unable to load module source for %s" % name)

            self.process_members(package_name, mod)

        except (ImportError, TypeError) as e:
            self.log_debug(e)

    def process(self):
        """
        input_text should be a list of installed python libraries to document.
        """
        package_names = str(self.input_data).split()
        packages = [__import__(package_name) for package_name in package_names]

        for package in packages:
            self.log_debug("processing package %s" % package)
            package_name = package.__name__
            prefix = package.__name__ + "."

            self.process_members(package_name, package)

            if hasattr(package, '__path__'):
                for module_loader, name, ispkg in pkgutil.walk_packages(package.__path__, prefix=prefix):
                    self.log_debug("in package %s processing module %s" % (package_name, name))
                    if not name.endswith("__main__"):
                        self.process_module(package_name, name)
            else:
                self.process_module(package.__name__, package.__name__)

        self.output_data.save()
