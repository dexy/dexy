from dexy.template import Template

class DefaultTemplate(Template):
    """
    A very boring default template that ships with dexy.
    """
    ALIASES = ['default']
    FILTERS_USED = ['jinja']
