from dexy.exceptions import UserFeedback
from dexy.filters.api import ApiFilter

import urllib
import re


class WebSequenceDiagrams(ApiFilter):
    """
    Dexy filter to use WebSequenceDiagrams.com
    """
    aliases = ["wsd"]
    _settings = {
        "version": ("Version of the WebSequenceDiagrams API to address", "1"),
        "style": ("Style to use, e.g. 'patent' or 'napkin'", "default"),
        "key": ("Your WebSequenceDiagrams API Key if you have one", None),
        "api-url": "http://www.websequencediagrams.com/",
        "output-extensions": ['.png', '.svg', '.img', '.pdf'],
        "input-extensions": ['.wsd'],
        "output": True,
        'api-key-name': "wsd",
        "added-in-version": "1.0.13",

    }
    _unset = ['api-username', 'api-password']

    def process(self):
        request = {}
        settings = self.setting_values()
        request["message"] = self.input_data
        request["style"] = settings["style"]
        request["apiVersion"] = settings["version"]
        key = None
        try:
            key = settings["key"] or self.read_param("key")
        except KeyError:
            pass
        if key:
            request["apikey"] = key
            self.log_debug("Using key to access WebSequenceDiagrams")
        else:
            self.log_debug("Accessing WebSequenceDiagrams without API key")

        resource = urllib.parse.urlencode(request)
        self.log_debug("Fetching from WebSequenceDiagrams")
        response = urllib.urlopen(settings["api-url"]+"index.php", resource)
        line = response.readline()
        response.close()

        expr = re.compile("(\?(img|pdf|png|svg)=[a-zA-Z0-9]+)")
        match = expr.search(line)

        if match is None:
            self.log_error("Problem fetching from WebSequenceDiagrams")
            raise UserFeedback("Invalid response from server.")

        self.log_debug("Writing WebSequenceDiagrams result to {0}".format(
            self.output_filepath()))

        response = urllib.urlopen(settings["api-url"] + match.group(0))
        self.output_data.set_data(response.read())
        self.output_data.save()
        response.close()
