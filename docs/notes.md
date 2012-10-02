

Dexy creates documents from source files by running the contents through filters. Filters can do anything to transform the text or binary content of the source file.

Sometimes filters need to access other documents in addition to the source file. For example a markdown file containing a tutorial might need to access scripts which show the code that should be written for the tutorial. Because the scripts need to be processed prior to the template file being compiled, Dexy needs to have a means of specifying dependencies.

We create a tree of documents which incorporate the dependencies we need. This allows us to specify the documents to be run and the order in which they should be run. We will build the classes up from a base Task class which handles the tree operations, then we will create subclasses of Task which wrap the functionality we need to define documents, and to break the document up into the separate steps of obtaining the original source input, and then running this input throug the various filters.











{{ d['dexy/artifact.py|idio']['filter-artifact-run'] }}

We first need to calculate the hashstring. Now we use different criteria than for an initial artifact. Artifacts always have a prior artifact, which may be the initial artifact, and we store that prior artifact's hashstring as the `prior_hash` attribute, because obviously if the input has changed, we will need to run our artifact again. We also use attributes like the document key and file extension, the next filter (which may have an impact due to the selection of file extension), any arguments passed to this filter, and also the hashstrings of all tasks in this tree that have already been completed, since their output may be used in this filter's processing:

{{ d['dexy/artifact.py|idio']['set-metadata-hash'] }}

Once we have determined the hash, we can set up the output data object and then determine whether we need to run the filter or if the element is already present in the cache:

{{ d['dexy/artifact.py|idio']['artifact-output-data'] }}

## Data Class

The Data class wraps methods which access data that may be cached or in memory. Each Artifact has references to two data objects, one representing the input data and another representing the output data. The output data from one artifact becomes the input data to the next element in the filter chain.

{{ d['dexy/data.py|idio']['json-data-class'] }}

The `_data` and `_ordered_dict` attributes represent data when it is stored in memory, in two possible formats. `_data` is for raw data, which can be text-based or binary. The `_ordered_dict` attribute represents textual data which is structured in ordered sections with names.

We define query methods to tell us if data is present, either in memory or in the designated data file on disk:

{{ d['dexy/data.py|idio']['has-data'] }}

We can fetch data by calling the `data()` method which will load from a data file if necessary:

{{ d['dexy/data.py|idio']['return-data'] }}

Many filters work with data in data files, so it may not be necessary to have files loaded into memory at all.

## Writing Filters


Whil many filters will not need to worry about anything other than implementing one of the `process_` convenience methods which provide access to the input data and handle persisting output data, some filters will need to access more information.

### Accessing Other Docs

Filters have access to the list of all processed Doc objects, and via these Doc objects they can access intermediate artifacts if desired. The `processed()` method returns an iterator over previously processed docs:

{{ d['dexy/dexy_filter.py|idio']['processed'] }}

Here is an example of using this within a filter:

{{ d['dexy/filters/example_filters.py|idio']['access-other-documents'] }}

We begin by creating an array to hold the strings we will return:

{{ d['dexy/filters/example_filters.py|idio']['access-other-docs-process-text'] }}

We iterate over the docs using the `processed()` method, and we assert that the returned elements are in fact members of Doc class:

{{ d['dexy/filters/example_filters.py|idio']['access-other-docs-iterate'] }}

We calculate the lengths of the children and artifacts arrays of the returned docs:

{{ d['dexy/filters/example_filters.py|idio']['access-other-docs-lens'] }}

We calculate the length of the generated output of the doc, using the string length if the doc has a single data element, and the ordered dict length if the doc returns sectioned data:

{{ d['dexy/filters/example_filters.py|idio']['access-other-docs-output-length'] }}

Finally we finish the doc loop by appending a string with this information to our `info` array and then we return all the lines of generated text to complete our filter processing:

{{ d['dexy/filters/example_filters.py|idio']['access-other-docs-finish'] }}

Here is a test of this filter showing some example outout:

{{ d['dexy/tests/filters/test_example_filters.py|idio']['test-access-other-documents'] }}

{% if False -%}

## Writing Custom Pre and Post Functions

compare writing custom pre/post functions with passing them as args.

+ adding additional children within a filter (archive filters, filename filter)
+ option to return _data or _ordered_dict?

{% endif -%}
