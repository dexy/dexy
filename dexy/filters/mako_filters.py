import mako.template
import dexy.filters.templating_filters

class MakoFilter(dexy.filters.templating_filters.TemplateFilter):
    ALIASES = ['mako']

    def process_text(self, input_text):
        return str(mako.template.Template(input_text).render(self.run_plugins()))
