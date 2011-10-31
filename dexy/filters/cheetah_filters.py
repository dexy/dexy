import Cheetah.Template
import dexy.filters.templating_filters

class CheetahFilter(dexy.filters.templating_filters.TemplateFilter):
    ALIASES = ['cheetah']

    def process_text(self, input_text):
        return str(Cheetah.Template.Template(input_text, searchList = self.run_plugins()))
