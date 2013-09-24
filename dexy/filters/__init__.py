import dexy.filters.ansi
import dexy.filters.api
import dexy.filters.archive
import dexy.filters.asciidoctor
import dexy.filters.aws
import dexy.filters.deprecated
import dexy.filters.easy
import dexy.filters.example
import dexy.filters.fluid_html
import dexy.filters.git
import dexy.filters.id
import dexy.filters.ipynb
import dexy.filters.ipynbcasper
import dexy.filters.java
import dexy.filters.latex
import dexy.filters.lyx
import dexy.filters.md
import dexy.filters.org
import dexy.filters.pexp
import dexy.filters.phantomjs
import dexy.filters.pydoc
import dexy.filters.pytest
import dexy.filters.pyg
import dexy.filters.pyn
import dexy.filters.rst
import dexy.filters.sanitize
import dexy.filters.soup
import dexy.filters.split
import dexy.filters.standard
import dexy.filters.sub
import dexy.filters.templating
import dexy.filters.wordpress
import dexy.filters.yamlargs
import dexy.filters.xxml

import dexy.filter
import os

yaml_file = os.path.join(os.path.dirname(__file__), 'filters.yaml')
dexy.filter.Filter.register_plugins_from_yaml_file(yaml_file)

# Automatically register plugins in any python package named like dexy_*
import pkg_resources
for dist in pkg_resources.working_set:
    if dist.key.startswith("dexy-"):
        import_pkg = dist.egg_name().split("-")[0]
        try:
            __import__(import_pkg)
        except ImportError as e:
            print "plugin", import_pkg, "not registered because", e
