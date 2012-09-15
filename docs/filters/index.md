# Guide to Dexy Filters

[TOC]

## Introductory Example

Filters are run by artifact objects, when necessary, as follows:

{{ d['modules.txt|pydoc']['dexy.artifact.FilterArtifact.generate:html-source'] }}

So an instance of the relevant filter class is initialized, its generating artifact is assigned as an attribute, it gets a copy of the artifact's log, and then its `process()` method is called.

The `process()` method is where the filter does whatever transformation is desired on the input it is give. The filter class has several methods to make it easy to work with the input from the previous artifact, and to store the generated output. In some cases, processing is done within Dexy's thread by python code operating directly in the `process()` method, in other cases the `process()` method will shell out to a command line tool and will work either on files in the file system or by communicating with external processes using pipes. As a result, Dexy provides options for reading and storing data within Python, and also provides ways of creating working files containing input data, and retrieving processed content from the file system.

Here is a simple example of what can go in a filter's `process()` method:

{{ d['modules.txt|pydoc']['dexy.plugins.example_filters.ExampleProcessMethod.process:html-source'] }}

First this method calls the `input_data()` instance method:

{{ d['modules.txt|pydoc']['dexy.filter.Filter.input_data:html-source'] }}

This method calles the `data()` method on the result of `input()`, where `input()` returns the `input_data` instance of the filter's artifact:

{{ d['modules.txt|pydoc']['dexy.filter.Filter.input:html-source'] }}

The `data()` method returns the raw data, either from memory if it's already loaded, or read from the cached source file:

{{ d['modules.txt|pydoc']['dexy.data.GenericData.data:html-source'] }}

So `input_data()` in our filter's `process()` method returns the raw data being input to this filter, and some extra text is added so we know the filter has run:

{{ d['modules.txt|pydoc']['dexy.plugins.example_filters.ExampleProcessMethod.process:html-source'] }}

In the second line, we call the `result()` method, which returns the `output_data` instance of the filter's artifact, which represents the entity we will use to store the results of our processing:

{{ d['modules.txt|pydoc']['dexy.filter.Filter.result:html-source'] }}

We call the `set_data()` method of this GenericData object, passing our `output` string as the argument:

{{ d['modules.txt|pydoc']['dexy.data.GenericData.set_data:html-source'] }}

So, this covers the basic actions we need to take in a filter's process method. We need to get the input data in some format, do some transformation on it, then save this as output data.

## Common Utilities

### User-Specified Arguments

Users can specify various parameters when they create documents, in this example the parameter `foo` is set to the value `bar`:

{{ d['modules.txt|pydoc']['dexy.tests.test_doc.test_pattern_doc_args:html-source'] }}

That parameter is defined at the document level, sometimes we want to designate arguments that are intended for a particular filter. To do that, we can pass a keyword argument where the key is the alias of the filter we want to target, and the value is a dict of the arguments we want the filter to have.

Here is an example filter whose output is a list of the filter arguments it received:

{{ d['modules.txt|pydoc']['dexy.plugins.example_filters.ExampleFilterArgs.process_text:html-source'] }}

And here is a test showing how filter args can be specified:

{{ d['modules.txt|pydoc']['dexy.tests.test_filter.test_filter_args:html-source'] }}

Within a filter, we can access the arguments intended for that filter by simply calling `args()`:

{{ d['modules.txt|pydoc']['dexy.filter.Filter.args:html-source'] }}

This in turn calls the `filter_args()` method of the artifact instance:

{{ d['modules.txt|pydoc']['dexy.artifact.FilterArtifact.filter_args:html-source'] }}

### File Extensions

Filter args can also be used to specify a file extension for a filter. For example, pygments can output many formats but defaults to html. Here we specify latex instead:

{{ d['modules.txt|pydoc']['dexy.tests.test_artifact.test_custom_file_extension:html-source'] }}

If not specified, Dexy automatically tries to find a file extension that will work with the next filter in line. Here we use a filter that only accepts `.tex` extension in order to force pygments to output latex:

{{ d['modules.txt|pydoc']['dexy.tests.test_artifact.test_choose_extension_from_overlap:html-source'] }}

And if there is no overlap between a file's extension and what the next filter can take, Dexy raises a UserFeedback exception:

{{ d['modules.txt|pydoc']['dexy.tests.test_artifact.test_bad_file_extension_exception:html-source'] }}

Similarly if one filter can't output anything the next filter in line can accept:

{{ d['modules.txt|pydoc']['dexy.tests.test_artifact.test_no_file_extension_overlap:html-source'] }}

### Data Classes

Filters need to choose a type of data storage appropriate for the data they will generate. Usually this means specifying the `OUTPUT_DATA_TYPE` class constant:

{{ d['modules.txt|pydoc']['dexy.filter.Filter.data_class_alias:html-source'] }}

This defaults to `{{ d['modules.txt|pydoc']['dexy.filter.Filter.OUTPUT_DATA_TYPE:value'] }}`. This type corresponds to the alias of the subclass of Data you want to use, in this case the `GenericData` class (aliases: {{ d['modules.txt|pydoc']['dexy.data.GenericData.ALIASES:value'] }}).

Another option is `sectioned`, and this is automatically chosen when filters implement a method that means a dict is the result:

{{ d['modules.txt|pydoc']['dexy.filter.DexyFilter.data_class_alias:html-source'] }}

A third option is `keyvalue`, and this is used, for example, by the `pydoc` filter.

Data types can be defined using Dexy's plugin system. Different data types may expose different API methods, for example key value storage provides an `append` method to add new key-value items, here is an example of this in use:

{{ d['modules.txt|pydoc']['dexy.plugins.example_filters.KeyValueExample.process:html-source'] }}

### Additional Documents

Another common feature is being able to add another document on-the-fly.

{{ d['modules.txt|pydoc']['dexy.filter.Filter.add_doc:html-source'] }}

## Python-Based Filters

In this section we review the classes that implement filters within Python by subclassing the `process()` method of one of its helpers.

The `DexyFilter` class is a subclass of `Filter` which provides some extra methods designed for filters that work within Python, i.e. that don't generate content by shelling out to another process. The `process()` method in DexyFilter looks for one of three helper methods defined on the class, and if it finds any of them, it does the right thing with the content returned by those methods:

{{ d['modules.txt|pydoc']['dexy.filter.DexyFilter.process:html-source'] }}

If it doesn't find one of them, then it just copies its input unchanged.

So, to implement a Python-based filter, you can either implement one of these helper methods, or you can override the whole `process()` method. If you do this then you need to ensure that results are saved in the cache, either by calling the `set_data()` method, or by saving output directly to the `data_file()` location.

Here is an example of a filter with a `process_text` method:

{{ d['modules.txt|pydoc']['dexy.plugins.example_filters.ExampleProcessTextMethod:html-source'] }}

Test:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_example_filters.test_process_text_filter:html-source'] }}

Here is one with a `process_dict` method:

{{ d['modules.txt|pydoc']['dexy.plugins.example_filters.ExampleProcessDictMethod:html-source'] }}

Test:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_example_filters.test_process_dict_filter:html-source'] }}

And here is one with a `process_text_do_dict` method:

{{ d['modules.txt|pydoc']['dexy.plugins.example_filters.ExampleProcessTextToDictMethod:html-source'] }}

Test:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_example_filters.test_process_text_to_dict_filter:html-source'] }}

Here is an example of a custom `process()` method that calls `set_data()`:

{{ d['modules.txt|pydoc']['dexy.plugins.example_filters.ExampleProcessMethod:html-source'] }}

Test:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_example_filters.test_process_method:html-source'] }}

And here is one where data is written directly to the cache file:

{{ d['modules.txt|pydoc']['dexy.plugins.example_filters.ExampleProcessMethodManualWrite:html-source'] }}

Test:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_example_filters.test_process_method_manual_write:html-source'] }}

## External Process Filters

In this section we review the classes that implement subprocess or pexpect based filters. The SubprocessFilter class contains basic methods for working with external processes.

The `executables()` method allows us to specify different executables depending on the platform by setting class constants, and also to specify multiple options to allow for variations in how the same program may be called.

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.executables:html-source'] }}

The `executable()` method returns the first of the methods in `executables()` which is found on the system:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.executable:html-source'] }}

So if we make a class with a fake executable:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_process_filters.NotPresentExecutable:html-source'] }}

Then the item shows up in the list of executables, but not as the result of `executable()`:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_process_filters.test_not_present_executable:html-source'] }}

We can use this to determine whether the filter is active:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.is_active:html-source'] }}

The code used to determine whether the executable is present does so by searching paths on the file system using Python:

{{ d['modules.txt|pydoc']['dexy.utils.command_exists:html-source'] }}

We also define a method to determine the version of external software we are using:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.version:html-source'] }}

This calls the `version_command()` method which determines the appropriate command to call:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.version_command:html-source'] }}

The `version()` method returns None if no version command exists. If a command exists but an error occurs while running it, it returns False. If all goes well it returns the first line of the version information returned. The version string is used as part of the hashstring, so that updated external software will cause a filter to be re-run. It is also sometimes displayed as part of the `dexy filters` command.

Here is the `process()` method:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.process:html-source'] }}

It first calls `command_string()` which composes the command we want to run:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.command_string:html-source'] }}

The first element of the command string is the executable, and then we have arguments to the executable, the name of the script to run, arguments for the script, and finally the output file where output should be written. The command string is composed with the most typical order in which these appear, for some filters we need to override this where an executable has a different syntax or we want to customize the string in some way. Arguments are not always present, we just accommodate them if so.

Command line args come from passing an `args` parameter to the filter arguments:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.command_line_args:html-source'] }}

Here is an example of passing a parameter to the python interpreter:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_process_filters.test_command_line_args:html-source'] }}

Script args appear in a different location, and are for passing arguments to the script being run, rather than the interpreter:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_process_filters.test_scriptargs:html-source'] }}

Of course, all this assumes that the executable in question expects things in this sequence. If not, the `command_string()` method needs to be customized.

Once we have a command string, we pass it to the method which will actually execute the command, along with the results of `setup_env()`:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.setup_env:html-source'] }}

The environment can be augmented by specifying a dict of env values in the filter class's ENV variable, and also by passing an 'env' argument to the filter:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_process_filters.test_custom_env_in_args:html-source'] }}

Here is the `run_command()` method:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.run_command:html-source'] }}

It starts by calling the `setup_wd()` method which creates a working directory using the artifact's hashstring to keep it separate from other working directories.

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.setup_wd:html-source'] }}

The `setup_wd()` is a shortcut which call the artifact's `create_working_dir()` method:

{{ d['modules.txt|pydoc']['dexy.artifact.FilterArtifact.create_working_dir:html-source'] }}

This creates a working directory, and also populates it with all the files that the artifact depends on, and with a file containing the previous step in the filter process. This means that, within this working directory, files can be referenced by the same relative pathnames as if they were being used outside of dexy, but with whatever changes dexy has made in the mean time. Here is an example showing how files are arranged and may be accessed:

{{ d['modules.txt|pydoc']['dexy.tests.test_artifact.test_create_working_dir:html-source'] }}

Returning to the `run_command()` method, we save the location of the working directory we just created by calling `setup_wd()`. Next we set up pipes for stdin, stdout, stderr as needed, optionally writing stdout and stderr to the same pipe. Then after noting in the log the command we will run and the location in which we will run it, we use the [`subprocess` library](http://docs.python.org/library/subprocess.html) to actually run the command. Here is the code again:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.run_command:html-source'] }}

The working directory, pipes for communicating with the process, and our customized environment are passed as arguments to Popen. We call the [`communicate`](http://docs.python.org/library/subprocess.html#subprocess.Popen.communicate) method to write any input needed to stdin, and to read any data from stdout. The contents of stdout and stderr are written to the log for help troubleshooting.

Then the `walk_working_directory()` method is called:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.walk_working_directory:html-source'] }}

This method generates a new document which contains all of the files found in the working directory, and their contents. This allows for detecting and documenting secondarily generated by the script that has been run.

Finally, the proc method and the contents of stdout are returned.

Here is the `process()` method we started with:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.process:html-source'] }}

We check the exit code of the process, and raise an exception if it is nonzero, unless we are choosing to ignore nonzero exit codes:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.handle_subprocess_proc_return:html-source'] }}

Here is a test showing a nonzero exit causing an exception:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_process_filters.test_nonzero_exit:html-source'] }}

And here is another test showing no exception since ignore_nonzero_exit is set to True:

{{ d['modules.txt|pydoc']['dexy.tests.plugins.test_process_filters.test_ignore_nonzero_exit:html-source'] }}

The final line of our `process()` method calls `copy_canonical_file()`:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessFilter.copy_canonical_file:html-source'] }}

Back when we specified our command string, we had output be written to a canonical filename, now we must copy that file to its final location to serve as our cache of the results of this filter.

### Subprocess Stdout Filter

The previous filter assumes that our executable will write its output to a file. Now instead we want to capture what gets written to stdout. We modify the `process()` method as follows:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessStdoutFilter.process:html-source'] }}

Here is the code that generates our command text:

{{ d['modules.txt|pydoc']['dexy.plugins.process_filters.SubprocessStdoutFilter.command_string_stdout:html-source'] }}

And after the process has run, instead of copying the canonical file to the cache, we use the `set_data()` method and pass the stdout from the proc, which we received via the pipe.


## Individual Filter Reference

Here we talk about all the filters that are available, their features and their implementation.
