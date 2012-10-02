[TOC]

# Tour of Dexy

Let's start by looking at the Dexy config file for this document and seeing how this gets processed by Dexy to generate a run. Here is the whole Python config file:

{{ d['config.py|idio'] }}

When this config file is run, Dexy will compile all the specified documents and output the finished products. Some of these documents are specified as strings, others are lists containing a string plus a dict of arguments.

Here is the source of `run`:

{{ d['modules.txt|pydoc']['dexy.run:html-source'] }}

The Wrapper object contains various parameter values and the keyword arguments are passed to this to override default settings if desired.

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.__init__:html-source'] }}

Next the runner instance's `run` method is called:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.run:html-source'] }}

The various `setup` methods do Dexy-related setup.

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.setup_dexy_dirs:html-source'] }}

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.setup_log:html-source'] }}

We need a connection to the sqlite db which will store run information:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.setup_db:html-source'] }}

The `setup_docs` method processes the arguments passed to `run` and creates Doc objects for any file name or pattern strings. Each doc object's `setup` method is called so the docs are ready to be run:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.setup_docs:html-source'] }}

All the created docs are then stored in the instance in an array called `docs`. The `run` instance method then iterates over all these docs, and for each doc triggers the doc's iterator which, in turn, calls all its child attributes. Thus all documents are processed in order. Here, again, is the source of the `Runner.run` method:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.run:html-source'] }}

Finally the `save_db` method commits all database transactions:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.save_db:html-source'] }}

Here, again, is the source of the `run` method in the dexy module:

{{ d['modules.txt|pydoc']['dexy.run:html-source'] }}

Finally, the `report` instance method is called, which runs all reports defined in plugins:

{{ d['modules.txt|pydoc']['dexy.wrapper.Wrapper.report:html-source'] }}

Now we can look at more detail into how these various elements work together.

[TOC]

## Tasks in a Tree

The basic Task class handles tree operations.

When this class is initialized, it is passed a key, a tuple of child tasks, and additional keyword arguments. These arguments are saved in instance variables for later use. We will use a state machine later to detect circular dependencies or other problems with running the tree, for now we initialize the task's state as `new`. If there are keyword arguments named 'post' or 'pre' these are assumed to define custom pre and post functions. We automatically run the `setup` method if the prerequisite `runner` object is include in the keyword args:

{{ d['modules.txt|pydoc']['dexy.task.Task.__init__:html-source'] }}

The `setup()` method will be used more extensively in subclasses of `Task`, for now it just calls `after_setup` which appends this task to a list of tasks in the runner and changes the state to be `setup`:

{{ d['modules.txt|pydoc']['dexy.task.Task.setup:html-source'] }}

{{ d['modules.txt|pydoc']['dexy.task.Task.after_setup:html-source'] }}

The `__iter__()` method defines and calls a `next_task()` function which does different things depending on the task's state. If the state is already `running` and we attempt to iterate again, this indicates a circular dependency was specified and an exception is raised. If the task is already complete, then we don't need to take any further action. If the state is `setup` then we will run the task by yielding the pre method first, then calling the object itself, and then calling the post method.

{{ d['modules.txt|pydoc']['dexy.task.Task.__iter__:html-source'] }}

The `__call__` method runs the task:

{{ d['modules.txt|pydoc']['dexy.task.Task.__call__:html-source'] }}

First this method iterates over children and then over tasks within each child, triggering their call methods. Then children which have been completed are added to a dict which each task instance has for accessing later. Then the `run` method is called, which can be overridden in subclasses to do whatever the desired `work` of the task is.

{{ d['modules.txt|pydoc']['dexy.task.Task.run:html-source'] }}

### Task Subclass Example

This Task class is intended to be subclassed with custom `run()` methods and perhaps custom `pre()` and `post()` methods. Various different subclasses can be mixed together.

Here is an example of a subclass of Task defining a `pre()`, `run()`, and `post()` method:

{{ d['modules.txt|pydoc']['dexy.tests.test_task.SubclassTask:html-source'] }}

We can call this like so:

{{ d['modules.txt|pydoc']['dexy.tests.test_task.test_run_demo_single:html-source'] }}

But take care not to call it without iterating to the sufficient level, or else the `pre` and `post` methods won't be run, nor other important setup code:

{{ d['modules.txt|pydoc']['dexy.tests.test_task.test_run_incorrectly:html-source'] }}

When we nest a child inside of a parent, it looks like this:

{{ d['modules.txt|pydoc']['dexy.tests.test_task.test_run_demo_parent_child:html-source'] }}

A CircularDependency exception is raised if we try to have 2 tasks be each other's children:

{{ d['modules.txt|pydoc']['dexy.tests.test_task.test_circular:html-source'] }}

### Docs

The Doc class is a subclass of Task which represents Dexy documents.

When docs are created, dependencies are nested in the parent Doc class and, because Doc is a subclass of Task, we can run all docs in the correct order. The Doc class also generates child tasks to run each step in the filter process.

The `setup` method creates child tasks for each step in the filter process. It also makes sure that any child Doc instances have their setup methods run:

{{ d['modules.txt|pydoc']['dexy.doc.Doc.setup:html-source'] }}

An initial artifact is created which holds the original input content:

{{ d['modules.txt|pydoc']['dexy.doc.Doc.setup_initial_artifact:html-source'] }}

Then for each filter to be run (if any), a filter artifact is created which takes the previous artifact's output as its input:

{{ d['modules.txt|pydoc']['dexy.doc.Doc.setup_filter_artifact:html-source'] }}

Note that the `children` attribute is used by the Task class and may include dependent documents as well as artifacts. We also add artifacts (but not the chlid docs) to a local `artifacts` array attribute so these can be accessed in a known order.

### Artifacts

The Artifact class is used to handle a step in processing. The first step in processing is different from subsequent steps since in this first step we are reading a source file which will be processed by later steps.

#### Initial Artifacts

The InitialArtifact class is a subclass of the Artifact class and this is used to handle the first step in processing.

{{ d['modules.txt|pydoc']['dexy.artifact.Artifact.setup:html-source'] }}

Initial artifacts may take input from a file or they may be virtual artifacts where their input is specified in code.

{{ d['modules.txt|pydoc']['dexy.artifact.InitialArtifact.run:html-source'] }}

Metadata attributes look like this for a file-based initial artifact:

{{ d['modules.txt|pydoc']['dexy.artifact.InitialArtifact.set_metadata_attrs:html-source'] }}

And like this for a virtual initial artifact:

{{ d['modules.txt|pydoc']['dexy.artifact.InitialVirtualArtifact.set_metadata_attrs:html-source'] }}

A file-based artifact always uses the `generic` data type:

{{ d['modules.txt|pydoc']['dexy.artifact.InitialArtifact.data_class_alias:html-source'] }}

For a virtual artifact, the data type is determined from the format of the contents, or by a user-specified option if supplied:

{{ d['modules.txt|pydoc']['dexy.artifact.InitialVirtualArtifact.data_class_alias:html-source'] }}

An `output_data` object is set up and then, if the hashcode determines that the object is not present in the cache, data is copied to the cache as appropriate:

{{ d['modules.txt|pydoc']['dexy.artifact.InitialArtifact.set_output_data:html-source'] }}

{{ d['modules.txt|pydoc']['dexy.artifact.InitialVirtualArtifact.set_output_data:html-source'] }}

### Filter Artifacts

The FilterArtifact class runs a single filter which runs on the output of the previous step, which may be the Initial Artifact or a prior filter artifact.

{{ d['modules.txt|pydoc']['dexy.artifact.FilterArtifact.run:html-source'] }}

We first determine the file extension to be output by this artifact:

{{ d['modules.txt|pydoc']['dexy.artifact.FilterArtifact.set_extension:html-source'] }}


Now we calculate the hashstring which is our tool for smart caching:

{{ d['modules.txt|pydoc']['dexy.artifact.FilterArtifact.set_metadata_hash:html-source'] }}

Finally the `setup_output_data` method creates an instance of the `Data` subclass desired.

{{ d['modules.txt|pydoc']['dexy.artifact.FilterArtifact.setup_output_data:html-source'] }}

Now that we have an output data type and a hashstring, we can check the cache and either proceecd using cached output, or run the filter by calling `generate`:

{{ d['modules.txt|pydoc']['dexy.artifact.FilterArtifact.generate:html-source'] }}

If we use the cached version, we need to check the database to see if any docs were created as side effects of running this previously, and create new doc objects for them so their results can be read from the cache.

{{ d['modules.txt|pydoc']['dexy.artifact.FilterArtifact.reconstitute_cached_children:html-source'] }}

## Data Objects

The Data class and its subclasses are responsible for storing the output that Dexy generates and letting it be accessed by other filters and by reports.

{{ d['modules.txt|pydoc']['dexy.data.Data.__init__:html-source'] }}

Data objects are initialized with a key, file extension and hashstring. A wrapper instance contains the usual information about where the cache is stored. A storage type is the final piece needed to identify and make use of the cached data (or to store data in the cache).

The key, extension, hashstring and storage type are stored in the database and can be retrieved based on a document key and the most recent batch id. So, from a document key, a data object can be correctly specified and retrieved from the cache.

Data objects are how other filters access information from an input, and also how reporters and other post-processors make use of finished output.



## Writing Filters

The `Filter` class defines a `process()` method which defines some convenience methods that can be implemented in other filters. Or, filters can override the `process()` method.

The `process()` method of the filter is responsible for ensuring that data is written to disk. Data may be left in memory by the filter, but this data may be cleared out at any time.

The convenience methods take care of persisting the data and they also save data in memory. All that is necessary is to return processed data in the appropriate format.


## Config Formats

There are several different config formats now available...

## Command Line Interface

# Docs and Tests

# Plugins
