import dexy.filters
import dexy.reporters
import dexy.parsers
import dexy.datas

# Automatically register plugins in any python package named like dexy_*
import pkg_resources
for dist in pkg_resources.working_set:
    if dist.key.startswith("dexy-"):
        import_pkg = dist.egg_name().split("-")[0]
        try:
            __import__(import_pkg)
        except ImportError as e:
            print(("plugin", import_pkg, "not registered because", e))
