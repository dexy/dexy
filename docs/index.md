# Dexy Internal Documentation

## Artifacts

An artifact represents the contents of a document at a particular stage in its filter processing. Artifacts are responsible for caching output so that a filter step does not need to be run if nothing has changed since the last time it was run. Artifacts should be able to operate as stand-alone entities for executing code or retrieving output. The artifact.py class contains common functionality, but there can be different back-end implementations of how artifacts are stored and serialized.

When an artifact is created within a normal Dexy run, a hashstring is computed based on all the inputs (i.e. document source, hashstrings of dependent documents, source code of filter class). If no inputs have changed in a subsequent run, then the same hashstring should result. If there is a cache entry corresponding to this hashstring, then we can simply obtain the results from the cache since they will not have changed.

The elements in HASH_WHITELIST should contain all the data needed to predict whether an output will be different. Currently this is:

<ul>
{% for k in d.source.artifact.HASH_WHITELIST.split(",") %}
<li>{{ k | replace("'","") | replace("[","") | replace("]","") }}</li>
{% endfor %}
</ul>

The hash_dict function returns a clean dict containing just the elements in this whitelist:
{{ d.source.artifact.hash_dict }}

And this is used to determine the hashstring:
{{ d.source.artifact.set_hashstring }}

This hashstring is used as the basis for caching and retrieving artifact information. Broadly speaking, we have three types of information to be concerned with.

Metadata - this incorporates the hash dict data and other metadata needed to help generate the artifact.

Output data - the data that results after processing the input

Input data - this is the same as the output data from the previous artifact.

### Metadata

Metadata consists of the HASH_WHITELIST attributes and some other attributes listed under META_ATTRS. The metadata, along with the input data, should be all that is required to recreate an attribute. The meta attributes should be simple attributes which are easily serializable by JSON. The metadata also includes a list of inputs, which are other artifacts which we may want to make use of.

{{ d.source.file_system_json_artifact.save_meta }}
{{ d.source.file_system_json_artifact.load_meta }}

### Output data

If output data is text-based and not binary, then it will be stored in two formats. First a 'canonical' format which contains the output in a file matching the output file extension. Secondly a JSON file format which can preserve document sections. In the case of binary data, just the canonical format exists.

### Input data

Except for the special case of an initial artifact, an artifact should not be responsible for persisting its own input data. The input data for an artifact is the same as the output data of the previous artifact.

The JSON data is loaded into memory at the beginning of processing and it accessible as the input_data_dict. Binary data is not automatically loaded into memory and it is assumed that filters will operate directly on data files or load data if they require it.

### Initializing Artifacts

Artifacts are usually created via the setup() class method which is intended to be used in the course of creating a document, so many attributes are set based on the document which is creating the artifact. However sometimes artifacts are created on their own, as when creating additional artifacts.

The 'key' argument is required to be passed when creating a new artifact.

{{ d.source.artifact['__init__'] }}

When the artifact is part of a document, the key consists of the original filename plus any filters that have been run up to this point, the final filter in the list being the filter which this artifact represents. The artifact class is responsible for generating canonical filenames based on this key:

{{ d.nose.test_artifact_filenames_file_key_with_filters }}

The long canonical form is intended to be unique, whereas the short form is more friendly and may make more intuitive sense in some cases, but may not be unique.

{{ d.source.artifact.canonical_filename }}
{{ d.source.artifact.long_canonical_filename }}

Where an Artifact is used outside of a document, the key may not have an extension:

{{ d.nose.test_artifact_filenames_simple_key }}

Where an artifact is part of a document, the extension will be determined automatically, however in the case of a standalone file, the extension will need to be specified.

The setup method associates a new artifact with its doc, and, if applicable, a previous artifact:

{{ d.source.artifact.setup }}

The setup method is called by the create initial artifact method in the Document class:

{{ d.source.document.create_initial_artifact }}

And also by the setup method in the Handler class:

{{ d.source.filter.setup }}


### Persisting and Restoring Artifacts

Artifacts are an important part of Dexy's caching system, so that documents need only be regenerated when necessary. Each artifact calculates a hashstring for itself, and later stores its data under this hashstring. If a later run of the artifact results in an identical hashstring, then it is safe to use the cached data. So the hashstring calculation should take into account all information which may have an impact on the final output.


which restricts items to the whitelist:


{{ d.nose.test_artifact_hash_dict }}

Dexy allows for different caching mechanisms. The options currently available are the default file system caching mechanism which writes data to files in the artifacts directory, and an experimental Riak (distributed key-value database) caching mechanism. Caching mechanisms are implemented by subclassing the Artifact class and implementing a save() and load() method (among others). It should be noted that, for now, an artifacts directory will still be needed even if using a caching mechanism that doesn't write data to that location, as many filters will write working files to the artifacts directory.

### FileSystemJsonArtifact save()

{{ d.source.file_system_json_artifact.save }}

