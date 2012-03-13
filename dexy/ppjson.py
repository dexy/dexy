import json
import sys

def run():
    if len(sys.argv) == 2:
        filename = sys.argv[1]

        with open(filename, "r") as f:
            try:
                contents = json.load(f)
            except ValueError as e:
                print "error parsing JSON in %s" % filename
                raise e
    else:
        filename = None
        contents = json.loads(sys.stdin.read())

    pretty = []

    for line in json.dumps(contents, sort_keys=True, indent=4).splitlines():
        pretty.append(line.rstrip())

    if filename:
        with open(filename, "w") as f:
            f.write("\n".join(pretty))
    else:
        print "\n".join(pretty)
