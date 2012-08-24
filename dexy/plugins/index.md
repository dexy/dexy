Plugins allow you to extend Dexy's capabilities by creating custom filters or by changing the way some of Dexy's internals work.

[TOC]

## 'Hello, World' Custom Filter

Filters are the most common thing you want to customize. Here is a 5 minute guide to writing a custom Dexy filter.

## Writing and Installing Plugins

Many plugins are included within the Dexy distribution itself and these plugins are automatically available in your projects.

Custom plugins can be written as standard Python packages and you can install these packages in the usual way (i.e. using pip or setuptools). This also means you can specify other packages as dependencies and they will be installed via pip.

In order to implement a new feature, you subclass the Dexy class corresponding to the type of feature you want to implement. You can implement multiple features within a single plugin by making several subclasses, even of different types.

Your module should load without generating any ImportError exceptions regardless of whether dependencies are present, and you can indicate a problem with depenencies by returning False for the `is_active()` method.

### Filters

To write a custom filter, you subclass the `Filter` class in the `dexy.filter` module.

### Reporters

To write a custom reporter, you subclass the `Reporter` class in the `dexy.reporter` module.

### Commands

To create a custom dexy command, you subclass the 'Command' class in the dexy.plugin` module. Then in the same module as you do this subclassing, you also define a command. namespacing.

## Dexy Viewer Plugin Example

The Dexy Viewer is a plugin which allows you to run a local web server which helps you preview what your Dexy snippets look like and to copy and paste tags into your document. In this section we see how this feature is implemented.
