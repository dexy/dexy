from dexy.exceptions import UserFeedback, InternalDexyProblem
from dexy.filters.api import ApiFilter

import urllib
import re


class WebSequenceDiagrams(ApiFilter):
    """
    Dexy filter to use WebSequenceDiagrams.com
    """
    aliases = ["wsd"]
    NODOC = True
    _settings = {
        "version" : "1",
        "style" : "default",
        "key" : None,
        "endpoint" : "http://www.websequencediagrams.com/",
        "output-extensions" : ['.png','.svg','.img','.pdf'],
        "input-extensions" : ['.wsd'],
        "output" : True,
        'api-key-name' : "wsd",
        "added-in-version" : "1.0.13"
    }

    def process(self):
        request = {}
        settings=self.setting_values()
        request["message"] = self.input_data
        request["style"] = settings["style"]
        request["apiVersion"] = settings["version"]
        key= settings["key"] or self.read_param("key")
        if key:
            request["apikey"] = key
            self.log_debug("Using key {key}".format(key=key))

        resource = urllib.urlencode(request)
        self.log_debug("Fetching from WebSequenceDiagrams")
        f = urllib.urlopen(settings["endpoint"]+"index.php", resource)
        line = f.readline()
        f.close()

        expr = re.compile("(\?(img|pdf|png|svg)=[a-zA-Z0-9]+)")
        match = expr.search(line)

        if match is None:
            self.log_error("Problem fetching from WebSequenceDiagrams")
            raise UserFeedback("Invalid response from server.")
            return

        self.log_debug("Writing WebSequenceDiagrams result to {0}".format(self.output_filepath()))
        urllib.urlretrieve(settings["endpoint"] + match.group(0),
                           self.output_filepath())
