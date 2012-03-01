import json
import sys

def run():
    filename = sys.argv[1]
    pretty = []

    with open(filename, "r") as f:
        try:
            contents = json.load(f)
        except ValueError as e:
            print "error parsing JSON in %s" % filename
            raise e

    for line in json.dumps(contents, sort_keys=True, indent=4).splitlines():
        pretty.append(line.rstrip())

    with open(filename, "w") as f:
        f.write("\n".join(pretty))
