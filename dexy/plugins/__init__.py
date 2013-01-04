import dexy.plugins.api_filters
import dexy.plugins.archive_filters
import dexy.plugins.boto_filters
import dexy.plugins.clang_filters
import dexy.plugins.deprecated_filters
import dexy.plugins.example_filters
import dexy.plugins.file_extension_filters
import dexy.plugins.idio_filters
import dexy.plugins.java_filters
import dexy.plugins.latex_filters
import dexy.plugins.markdown_filters
import dexy.plugins.nltk_filter
import dexy.plugins.output_reporters
import dexy.plugins.parsers
import dexy.plugins.pexpect_filters
import dexy.plugins.phantomjs_filters
import dexy.plugins.pydoc_filters
import dexy.plugins.pygments_filters
import dexy.plugins.pygments_plugins
import dexy.plugins.restructured_text_filters
import dexy.plugins.run_reporter
import dexy.plugins.split_filters
import dexy.plugins.standard_filters
import dexy.plugins.stationery
import dexy.plugins.stdout_filters
import dexy.plugins.stdout_input_filters
import dexy.plugins.subprocess_filters
import dexy.plugins.templates
import dexy.plugins.templating_filters
import dexy.plugins.website_reporters
import dexy.plugins.wordpress_filters
import dexy.plugins.yamlargs_filters

import pkg_resources
# Automatically register plugins in any python package named like dexy_*
for dist in pkg_resources.working_set:
    if dist.key.startswith("dexy-"):
        import_pkg = dist.egg_name().split("-")[0]
        __import__(import_pkg)
