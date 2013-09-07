from dexy.exceptions import InternalDexyProblem
from dexy.filter import DexyFilter
import imp
import inspect
import json
import os
import pkgutil
import sys

class PythonDocumentationFilter(DexyFilter):
    """
    Returns introspected python data in key-value storage format.

    Where input is a .txt file, this is assumed to be the name of an installed python module.

    Where input is a .py file, the file itself is loaded and parsed.
    """
    aliases = ["pydoc"]
    _settings = {
            'input-extensions' : ['.txt', '.py'],
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
            except UnicodeDecodeError:
                print "skipping", item

    def add_source_for_key(self, key, source):
        """
        Appends source code + syntax highlighted source code to persistent store.
        """
        try:
            self.output_data.append("%s:value" % key, json.dumps(source))
        except Exception as e:
            print "skipping", key, e

        if not (type(source) == str or type(source) == unicode):
            source = inspect.getsource(source)

        try:
            self.output_data.append("%s:source" % key, str(source))
        except Exception as e:
            print "skipping", key, e

    def process_members(self, package_name, mod):
        """
        Process all members of the package or module passed.
        """
        name = mod.__name__
        if name == 'dummy':
            name = None

        for k, m in inspect.getmembers(mod):
            self.log_debug("in mod '%s' processing element '%s'" % (name, k))

            is_class = inspect.isclass(m)
            has_module = hasattr(m, '__module__')
            module_exists = has_module and m.__module__
            module_matches = module_exists and m.__module__.startswith(package_name)

            if not is_class and module_matches:
                if (m.__module__ is None) or (m.__module__ == 'dummy'):
                    key = k
                else:
                    key = "%s.%s" % (m.__module__, k)

                self.fetch_item_content(key, m)

            elif is_class and module_matches:
                if name:
                    key = "%s.%s" % (name, k)
                else:
                    key = k

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
                        if name:
                            key = "%s.%s.%s" % (name, k, ck)
                        else:
                            key = "%s.%s" % (k, ck)
    
                        self.fetch_item_content(key, cm)
                except AttributeError:
                    pass

            else:
                if name:
                    key = "%s.%s" % (name, k)
                else:
                    key = k

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

    def process_python_module(self):
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

    def process_python_file(self):
        wd = self.parent_work_dir()
        ws = self.workspace()

        self.populate_workspace()
        target = os.path.join(ws, self.input_data.name)
        sys.path.append(wd)
        sys.path.append(ws)
        self.log_debug("Importing python content from %s" % target)
        try:
            mod = imp.load_source("dummy", target)
            self.process_members("", mod)
        except Exception as e:
            msg = "Could not process %s because %s"
            msgargs = (self.input_data.name, e)
            self.log_warn(msg % msgargs)

    def process(self):
        """
        input_text should be a list of installed python libraries to document.
        """
        # TODO These should not load into active workspace, should fork a new
        # python process for better isolation.
        if self.prev_ext == '.txt':
            self.process_python_module()
        elif self.prev_ext == '.py':
            self.process_python_file()
        else:
            raise InternalDexyProblem("Should not have ext %s" % self.prev_ext)

        self.output_data.save()
