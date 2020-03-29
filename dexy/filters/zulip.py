from dexy.filters.api import ApiFilter
import json

try:
    import zulip
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class ZulipFilter(ApiFilter):
    """

    Create a .zuliprc file
    per https://zulipchat.com/api/configuring-python-bindings

    Hint: When you go to get your API key it will automatically download a
    .zuliprc file for you
    """
    aliases = ['zulip']

    _settings = {
            'config-file' : '~/.zuliprc',
            'input-extensions' : ['.*'],
            'output-extensions' :  ['.json']
            }

    def is_active(self):
        return AVAILABLE

    def process(self):
        client = zulip.Client(config_file=self.setting('config-file'))

        if self.input_data.ext in ('.txt', '.md'):
            content = str(self.input_data)
            request = {
                 "type": "stream",
                 "to": self.setting('stream'),
                 "topic": self.setting('topic'),
                 "content": content
                 }
            response = client.send_message(request)

        else:
            pass

        self.output_data.set_data(json.dumps(response))
