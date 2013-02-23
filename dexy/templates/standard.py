import dexy.template

class DefaultTemplate(dexy.template.Template):
    """
    A very boring default template that ships with dexy.
    """
    ALIASES = ['default']
    FILTERS_USED = ['jinja']
