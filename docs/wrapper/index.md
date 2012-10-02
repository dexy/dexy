Wrapper Class and Doc Config Files

The Wrapper class provides an interface to Dexy and allows you to:
    * run dexy
    * run reports based on prior dexy runs
    * access the database of prior dexy runs

## Configuration

Dexy has several configuration options. These can be specified on the command line or in a config file, and the Wrapper class stores the selected options and makes them available to the various Dexy classes that use them.

The Wrapper class has several class constants containing default values for these options. The command line interface to Dexy, defined in `dexy.commands`, uses these class constants to specify default values for the command line options.

In the `__init__` method of the Wrapper class, instance variables are set to the default values, then updated from any config file and command line options.

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.__init__:html-source'] }}

Here is the source of `initialize_attribute_defaults`:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.initialize_attribute_defaults:html-source'] }}

Here is the source of `load_config_file`:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.load_config_file:html-source'] }}

The `update_attributes_from_config` method ensures that all keyword arguments passed correspond to known attributes, and converts some attributes from alternative names to the correct internal names. This is done to make some attribute names simpler to type on the command line, while using more expressive variable names internally.

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.update_attributes_from_config:html-source'] }}

The `RENAME_PARAMS` dict is:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.RENAME_PARAMS:html-source'] }}

This test verifies that command line options override config file options:

{{ d['modules.txt|pydoc']['dexy.tests.test_wrapper.test_kwargs_override_config_file:html-source'] }}

It is possible to generate a config file which can then be edited:

{{ d['modules.txt|pydoc']['dexy.commands.conf_command:html-source'] }}

This command calls the `default_config` class method of the Wrapper class:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.default_config:html-source'] }}

We combine directories and file names using a few methods:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.db_path:html-source'] }}

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.log_path:html-source'] }}

## Running Dexy

The wrapper class has the interface for actually running dexy. Here is how the wrapper class can be used to run dexy:

{{ d['modules.txt|pydoc']['dexy.run:html-source'] }}

 And here is the `run` method of the Wrapper class:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.run:html-source'] }}

First we call the `setup_run` method:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.setup_run:html-source'] }}

This first checks to be sure that dexy's artifacts and logs directories are present, and exits if they are not:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.check_dexy_dirs:html-source'] }}

Next we set up a logger:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.setup_log:html-source'] }}

Then we set up a database:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.setup_db:html-source'] }}

The database is used to store information about the documents we process.

After the database is set up, we assign the next sequential batch id to the wrapper so we can identify all documents created in this particular run.

Finally in our `setup_run` method we make sure that the documents we want to process are set up. Documents can be specified as positional arguments to the Wrapper constructor, and these are stored in the `args` instance attribute. Documents can also be directly assigned to the `docs_to_run` attribute. If the `docs_to_run` attribute is populated by the time `setup_run` is called, then these tasks are used with no further processing. Otherwise, the `setup_docs` method is called:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.setup_docs:html-source'] }}

This method iterates over each element in `args` and creates some type of Document based on the type of argument:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.create_doc_from_arg:html-source'] }}

When a string is passed, then this is designated to be a `Doc` unless it contains the filename wildcard character `*`, in which case it is a `PatternDoc`:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.create_doc_from_string:html-source'] }}

The difference is that Doc objects represent a single file (and this file must exist, or 'contents' must be specified for a virtual file), whereas a PatternDoc will iterate over all files matching its pattern and create Doc objects for each of these, with no error if no files are found to match the pattern.

After the appropriate doc objects are created, these are added to the `docs_to_run` attribute of the wrapper, in the same order as the args which specified them.

Here again is the source of the `run` method. Now that the setup is complete, each doc in the `docs_to_run` attribute is iterated over and called:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.run:html-source'] }}

Finally, the `save_db` method is called which persists records to the database:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.save_db:html-source'] }}

## Running and Docs

The wrapper's run method will run each task in `docs_to_run` in sequence. However, this list is just a starting point, and not a comprehensive list of all tasks which were run. As each task is set up, it is added to an OrderedDict named `tasks`.

Stuff goes into database

## Parsing Doc Config

## Query API
