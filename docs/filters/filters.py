import dexy.plugins
from dexy.filter import Filter

for k in sorted(Filter.aliases):
    print "%s %s" % (k, Filter.aliases[k].__name__)
