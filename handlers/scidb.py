try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from dexy.handler import DexyHandler
import pexpect

class ScidbHandler(DexyHandler):
    INPUT_EXTENSIONS = [".scidb", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['scidb']

    def process_dict(self, input_dict):
        output_dict = OrderedDict()
        for k, v in input_dict.items():
            output = ""
            for line in v.rstrip().split("\n"):
                output += "> %s\n" % line

                if len(line) == 0 or line.startswith('#'):
                    continue
                command = "/home/ana/b_0_5_release/bin/iquery -q \"%s\"" % line
                self.log.debug(command)
                output += pexpect.run(command)
            output_dict[k] = output
        return output_dict

