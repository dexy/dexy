from dexy.filters.pydoc import PythonIntrospection
import io
import dexy.exceptions
import inspect
import os

try:
    import nose
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class PythonTest(PythonIntrospection):
    """
    Runs the tests in the specified Python modules.

    Python modules must be installed on the system. Returns a key-value store
    with test results and source code.
    
    Many packages are installed without tests, so this won't work.
    """
    aliases = ['pytest']
    _settings = {
            'run-tests' : (
                "Whether to run tests or just return test source code.",
                True
                ),
            'test-passed-when-not-run' : (
                "Value which should be used for test_passed when tests are not run.",
                True
                ),
            'load-tests-mode' : (
                "'dir' to find tests by location relative to package dir, 'name' if tests are in their own module.",
                'dir'),
            'path-to-tests-dir' : (
                "Path from package dir to tests dir.",
                "../tests"),
            'chdir' : (
                "Path from package dir to chdir to.",
                None),
            'nose-argv' : (
                "Need to fake out argv since sys.argv will be args for dexy, not nose.",
                ['nosetests', '--stop', '--verbose'])
            }

    def is_active(self):
        return AVAILABLE

    def load_tests_from_dir(self, module_name):
        self.log_debug("Loading module '%s' to find its tests." % module_name)
        mod = self.load_module(module_name)

        self.mod_file_dir = os.path.dirname(mod.__file__)
        relpath = self.setting('path-to-tests-dir')
        tests_dir = os.path.normpath(os.path.join(self.mod_file_dir, relpath))
        self.log_debug("Attempting to load tests from dir '%s'" % tests_dir)

        loader = nose.loader.TestLoader()
        return loader.loadTestsFromDir(tests_dir)

    def load_tests_from_name(self, module_name):
        loader = nose.loader.TestLoader()
        return loader.loadTestsFromName(module_name)

    def load_tests(self, module_name):
        mode = self.setting('load-tests-mode')
        if mode == 'dir':
            return self.load_tests_from_dir(module_name)
        elif mode == 'name':
            return self.load_tests_from_name(module_name)
        else:
            msg = "Invalid load-tests-mode setting '%s'" % mode
            raise dexy.exceptions.UserFeedback(msg)

    def append_source(self, test, test_passed):
        for key, member in test.context.__dict__.items():
            if inspect.ismethod(member) or inspect.isfunction(member):
                qualified_test_name = "%s.%s" % (test.context.__name__, member.__name__)
                source = inspect.getsource(member.__code__)

                doc = inspect.getdoc(member)
                if doc:
                    doc = inspect.cleandoc(doc)
                    self.output_data.append("%s:doc" % qualified_test_name, doc)

                comments = inspect.getcomments(member.__code__)

                self.output_data.append("%s:source" % qualified_test_name, source)
                self.output_data.append("%s:name" % qualified_test_name, member.__name__)
                self.output_data.append("%s:comments" % qualified_test_name, comments)
                self.output_data.append("%s:passed" % qualified_test_name, str(test_passed))

    def run_test(self, test):
        # TODO This isn't working... maybe because we're running this in a test
        noselogs = io.StringIO()
        config = nose.config.Config(
                logStream = noselogs
                )

        if self.setting('run-tests'):
            self.log_debug("Running test suite %s" % test)
            test_passed = nose.core.run(
                    suite=test,
                    config=config,
                    argv=self.setting('nose-argv')
                    )
            self.log_debug("Passed: %s" % test_passed)
        else:
            test_passed = self.setting('test-passed-when-not-run')

        return test_passed

    def process(self):
        module_names = str(self.input_data).split()
        self.mod_file_dir = None
        orig_wd = os.path.abspath(".")
        chdir = self.setting('chdir')

        for module_name in module_names:
            tests = self.load_tests(module_name)

            if chdir:
                chdir = os.path.abspath(os.path.join(self.mod_file_dir, chdir))
                self.log_warn("Changing dir to %s for tests" % chdir)
                os.chdir(chdir)

            for test in tests:
                test_passed = self.run_test(test)
                self.append_source(test, test_passed)

            if chdir:
                self.log_warn("Changing dir back to %s" % orig_wd)
                os.chdir(orig_wd)

        self.output_data.save()
